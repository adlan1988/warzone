#!/usr/bin/env python

import requests

class WarmeriseAPI:
	
	api_path = "http://warmerise.com/Warmerise/PHP/Public"
	
	def post(self, path, data=None):
		if not data: data = {}
		
		url = "%s/%s" % (self.api_path, path)
		response = requests.post(url, data=data)
		
		if response.status_code != 200:
			raise err.WarmeriseStatusCodeError(response)
		
		return response
	
	def game_login(self, w1337):
		""" Send a POST to GameLogin.php to get info about an account """
		return self.post("GameLogin.php", data={ "hash": w1337 })
	
	def save_score(self, session=None, username=None, key=None,
		xp=0, kills=0, deaths=0, killstreak=0):
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
		
		return self.post("SaveScore.php", data={ "data": data_str })