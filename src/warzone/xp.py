#!/usr/bin/env python

import api, sys, time, threading

try: import grequests
except: grequests = None

class XPGrinder:
	def __init__(self, session, diff, increment=49, scount=16):
		self.session = session
		self.diff = diff
		self.increment = increment
		self.scount = scount # Number of async/threaded operations allowed simultaneously
		self.api = api.WarmeriseAPI()
		
		self.lock = threading.Lock()
		
		self.reset()
	
	def reset(self):
		""" Reset certain counters for re-use of the grinder """
		self.reqnum = self.diff / self.increment
		self.leftovers = self.diff % self.increment
		
		self.completed = 0
		self.sent = 0
		self.waiting = 0
		self.failed = 0
		
		return self
		
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
		#waiting = completed = 0
		#
		#def on_response(response=None, details=None):
		#	completed += 1
		#	waiting -= 1
		#	print("Async XP response completed!")
		
		print("Required number of full requests: %i" % self.reqnum)
		
		sleeptime = 0.01 # 1 centisecond
		
		# When spamming requests really quickly, Warmerise's PHP backend seems to
		# "ignore" some of the requests..
		while self.sent < self.reqnum:
			
			while self.waiting < self.scount and self.sent < self.reqnum:
				self.api.save_score(session=self.session,
					xp=self.increment, async=True, callback=self.on_async_response)
				self.waiting += 1
				self.sent += 1
				
				#print("Waiting for another request, waiting = %i" % self.waiting)
			
			time.sleep(sleeptime) # 1 centisecond
		
		while self.completed < self.reqnum: time.sleep(sleeptime)
		
		print
		
		#print("Failed requests: %i" % self.failed)
		
		# Do leftovers sync
		if self.leftovers > 0:
			self.api.save_score(session=self.session, xp=self.leftovers)
	
	def on_async_response(self, response=None, details=None):
		
		self.completed += 1
		self.waiting -= 1
		
		if response.status_code != 200:
			self.failed += 1
		
		sys.stdout.write("Async XP response completed! (%i/%i)\r"
			% (self.completed, self.reqnum))
	
	def grind_threaded(self):
		pass
		