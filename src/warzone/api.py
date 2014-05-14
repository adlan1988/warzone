#!/usr/bin/env python

import requests

class WarmeriseAPI:
	
	api_path = "http://warmerise.com/Warmerise/PHP/Public/"
	
	def post(self, path, data=None):
		if not data: data = {}
		
		url = "%s/%s" % (self.api_path, path)
		response = requests.post(url, data=data)
		
		if response.status_code != 200:
			raise err.WarmeriseStatusCodeError(response)
		
		return response
	
	def game_login(self, w1337):
		return self.post("GameLogin.php", data={ "hash": w1337 })
	
	def save_score(self, session, stats):
		
		if session is None or stats is None: return
		
		for key in ("xp", "kills", "deaths", "highest_killstreak"):
			if key not in stats:
				stats[key] = 0
		
		data_str = "%s,%s,%i,%i,%i,%i" % (
			session.username, session.key,
			stats["xp"], stats["kills"], stats["deaths"], stats["highest_killstreak"]
		)
		
		response = self.post("SaveScore.php", data={ "data": data_str })