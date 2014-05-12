#!/usr/bin/env python

class WarmeriseWebError(Exception):
	def __init__(self, msg=None, response=None):
		self.msg = msg
		self.response = response
	
	def __str__(self):
		return self.msg or ""

class WarmeriseStatusCodeError(WarmeriseWebError):
	def __init__(self, response):
		WarmeriseWebError.__init__(
			self,
			msg="Unexpected status code: %i" % response.status_code,
			response=response
		)

class WarmeriseAuthError(WarmeriseWebError):
	def __init__(self, msg=None, response=None):
		WarmeriseWebError.__init__(
			self,
			msg=msg,
			response=response
		)