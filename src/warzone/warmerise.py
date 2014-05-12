#!/usr/bin/env python

"""
This file is going to look very similar to nplay.py from
the PlayN project, as both NPlay and Warmerise use SocialEngine.
There are a few differences between them though, as Warmerise
sets a special cookie on login.
"""

import re, requests

# Path to directory with Warmerise's custom PHP scripts
NSDG_PHP_PATH = "http://warmerise.com/Warmerise/PHP/Public/"
LOGIN_PATH = "http://warmerise.com/login"

def login(email, password):
	url = LOGIN_PATH
	sid = get_phpsessid()
	session = Session(email=email, phpsessid=sid)
	
	# Get headers to use
	headers = get_headers()
	headers["Referer"] = "%s/return_url/64-Lw==" % LOGIN_PATH
	
	# POST data
	data = {
		"email": email,
		"password": password,
		"remember": "",
		"return_url": "64-Lw==",
		"submit": "" }
	
	response = requests.post(url, data=data,
		cookies=session.get_cookies(), headers=headers,
		allow_redirects=False) 
		
	# We don't want to follow the 302->200 redirect so we can
	# grab the w1337 cookie
	if response.status_code != 302:
		raise StandardError("Unexpected status code on login: %i" % response.status_code)
	
	if "w1337" not in response.cookies:
		raise StandardError("w1337 cookie not found after login")
	
	session.w1337 = response.cookies["w1337"]
	
	complete_session_info(session)
	
	return session

def complete_session_info(session):
	""" Complete the session info, currently only makes
	a call to GameLogin.php """
	
	data = {
		"hash": session.w1337,
	}
	
	response = requests.post("%s/GameLogin.php" % NSDG_PHP_PATH, data=data,
		cookies=session.get_cookies(), headers=get_headers())
	
	if response.status_code != 200:
		raise StandardError("Unexpected status code on GameLogin.php: %i" % response.status_code)
	
	session.set_gamelogin(response.text)
	
def get_headers():
	return {
		"Host": "www.warmerise.com",
		"User-Agent": "Mozilla/5.0 (Windows NT 5.1; rv:27.0) Gecko/20100101 Firefox/27.0"
	}

def get_phpsessid():
	""" Pay a visit to the login page to get a usable PHPSESSID """
	url = "http://www.warmerise.com/login"
	headers = get_headers()
	response = requests.get(url, headers=headers)
	sid = response.cookies["PHPSESSID"]
	
	if sid is None:
		raise StandardError("Could not retrieve a PHPSESSID")
	
	return sid

class Session:
	def __init__(self, email=None, phpsessid=None):
		self.email = email
		self.phpsessid = phpsessid
		self.w1337 = None # Cookie set on login, used for game-related PHP scripts
		
		# Data retrieved from GameLogin.php
		self.username = None
		self.key = None
		self.xp = 0
		self.kills = 0
		self.deaths = 0
		self.highest_killstreak = 0
		self.rank = 0
		self.unknown = 4 # ?
		self.cash = 0
		
		self.gamelogin_set = False
	
	def get_cookies(self):
		""" Get a dictionary that can be passed to requests for cookie data """
		cookies = { "PHPSESSID": self.phpsessid, "cookie_test": "1", }
		if self.w1337: cookies["w1337"] = self.w1337
		return cookies
	
	def set_gamelogin(self, text):
		""" Set fields from the response given by GameLogin.php """
		# Replace weird stuff with colon
		text = re.sub(r'[^\x00-\x7F]+',':', text).encode("ascii")
		#separator = "\xA7"
		
		lines = text.splitlines()
		
		if len(lines) <= 0: return
		
		fields = lines[0].split(":") # lines[0].split(separator)
		if(len(fields) == 9):
			self.username = fields[0]
			self.key = fields[1]
			self.xp = int(fields[2])
			self.kills = int(fields[3])
			self.deaths = int(fields[4])
			self.highest_killstreak = int(fields[5])
			self.rank = int(fields[6])
			self.unknown = int(fields[7])
			self.cash = int(fields[8])
			
			self.gamelogin_set = True
		
		if len(lines) == 1: return
		
		self.clan_names = lines[1].split(":") # lines[1].split(separator)
		self.clan_names.pop(-1)