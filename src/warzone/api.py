#!/usr/bin/env python

import requests

try: import grequests
except: grequests = None

class WarmeriseAPI:
	
	api_path = "http://warmerise.com/Warmerise/PHP/Public"
	
	def post(self, path, data=None, async=False, callback=None):
		
		if not data: data = {}
		url = "%s/%s" % (self.api_path, path)
		
		# Sync
		if not async:
			response = requests.post(url, data=data)
			
			if response.status_code != 200:
				raise err.WarmeriseStatusCodeError(response)
			
			return response
		# Async
		else:
			if not grequests: raise ImportError
			
			wrapper = WarmeriseAPICallbackWrapper(callback)
			req = grequests.get(path, hooks={ "response": wrapper.fire })
			
			return grequests.map([req])
	
	def game_login(self, w1337, async=False, callback=None):
		""" Send a POST to GameLogin.php to get info about an account """
		return self.post("GameLogin.php", data={ "hash": w1337 },
			async=async, callback=callback)
	
	def save_score(self, session=None, username=None, key=None,
		xp=0, kills=0, deaths=0, killstreak=0, async=False, callback=None):
		""" Send a POST to SaveScore.php to modify xp, kills, deaths, and
		highest killstreak for an account """
		
		if session is None and (username is None or key is None):
			return
		
		if session:
			username = session.username
			key = session.key
		
		data_str = "%s,%s,%i,%i,%i,%i" % (
			session.username, session.key,
			xp, kills, deaths, killstreak
		)
		
		return self.post("SaveScore.php", data={ "data": data_str },
			async=async, callback=callback)

class WarmeriseAPICallbackWrapper:
	def __init__(self, callback=None):
		self.callback = callback
	
	def fire(self, response, verify=None, cert=None,
		proxies=None, timeout=0, stream=None):
		""" Fire the callback """
		
		# gevent/grequests details
		details = {
			"verify": verify,
			"cert": cert,
			"proxies": proxies,
			"timeout": timeout,
			"stream": stream,
		}
		
		if self.callback:
			self.callback(response=response, details=details)