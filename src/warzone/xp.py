#!/usr/bin/env python

import api, time

try: import grequests
except: grequests = None

class XPGrinder:
	def __init__(self, session, diff, increment=49, scount=4):
		self.session = session
		self.diff = diff
		self.increment = increment
		self.scount = scount # Number of async/threaded operations allowed simultaneously
		self.api = api.WarmeriseAPI()
		
		self.reqnum = self.diff / self.increment
		self.leftovers = self.diff % self.increment
		
	def grind_sync(self):
		""" Spam XP requests synchronously using rquests """
		# Send N requests with full increment
		for i in range(0, self.reqnum):
			print("Sending XP=%i as request (%i / %i)" % (self.increment, i, self.reqnum))
			response = self.api.save_score(session=self.session, xp=self.increment)
		
		# Send leftovers
		if self.leftovers > 0:
			print("Sending leftover XP=%i" % self.leftovers)
			response = self.api.save_score(session=self.session, xp=self.leftovers)
	
	def grind_async(self):
		""" Spam XP requests asynchronously using grequests, if available """
		if grequests is None: raise ImportError
		
		# May be async issues regarding waiting..
		waiting = completed = 0
		
		def on_response(response=None, details=None):
			completed += 1
			waiting -= 1
			print("Async XP response completed!")
		
		while completed < self.reqnum:
			
			while waiting < self.scount:
				self.api.save_score(session=self.session,
					xp=self.increment, async=True, callback=on_response)
				waiting += 1
			
			time.sleep(0.01) # 1 centisecond
		
		# Do leftovers sync
		if self.leftovers > 0:
			self.api.save_score(session=self.session, xp=self.leftovers)
	
	def grind_threaded(self):
		pass
		