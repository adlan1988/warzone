#!/usr/bin/env python

import argparse, cmd, getpass
import api, warmerise
from pprint import pprint

try:
	import readline
except ImportError:
	pass

class WarzoneCmd(cmd.Cmd):
	""" An interactive prompt for interacting with Warmerise's
	API, following the model set by PlayN's interpreter """
	
	def __init__(self):
		cmd.Cmd.__init__(self)
		self.api = api.WarmeriseAPI()
		
		self.session = None
		self.sessions = {}
		
		self.update_prompt()
	
	def start(self):
		# For now, just cmdloop wrapper.
		# Will make this more sophisticated for exception handling later
		self.cmdloop()
	
	def update_prompt(self):
		""" Update the prompt using selected session """
		sesname = ""
		if self.session is not None:
			sesname = "/%s" % self.session.username
		self.prompt = "(Warzone%s) " % sesname
	
	def prompt_login(self, email=None, password=None, phpsessid=None):
		
		session = None
		
		try:
			if phpsessid is not None: # PHPSESSID login
				raise NotImplementedError
			else:  # E-mail / password login
				noecho = "(Password will not echo)" if (password is None) else ""
				print("Prompting for auth info: %s" % noecho)
				
				if email is None:
					email = raw_input("E-mail: ")
				
				if password is None:
					password = getpass.getpass("Password: ")
				
				session = warmerise.login(email, password)
		except err.NPlayAuthError as e:
			print("Login failed") # Use logging later
			return
		
		if session is None: return
		
		self.sessions[session.username.lower()] = session
		self.session = session
		
		self.update_prompt()
	
	#
	# Command: `exit`
	#
	
	def help_exit(self):
		print("Exit the interpreter")
	
	def do_exit(self, str):
		return True
	
	# 
	# Command: `login`
	#
	
	def help_login(self):
		self.create_parser_login().print_help()
	
	def do_login(self, str):
		""" Login to a Warmerise account and store the session data """
		parser = self.create_parser_login()
		
		try: args = parser.parse_args(str.split())
		except: return
		
		args.phpsessid = None
		if args.phpsessid: self.prompt_login(phpsessid=args.phpsessid)
		else: self.prompt_login(email=args.email, password=args.password)
	
	#
	# Command: `session`
	#
	
	def help_session(self):
		self.create_parser_session().print_help()
	
	def do_session(self, str):
		""" """
		parser = self.create_parser_session()
		
		try: args = parser.parse_args(str.split())
		except: return
		
		if args.all:
			for (username, session) in self.sessions.items():
				self.print_session(session)
		elif args.session is None and self.session:
			self.print_session(self.session)
		
		if args.session: # Switch to session
			selected = None
			search = args.session.lower()
			
			if "@" in search:
				for (username, session) in self.sessions.items():
					if search == session.email.lower():
						selected = session
						break
			else:
				try: selected = self.sessions[search]
				except KeyError: pass
			
			if selected: self.session = selected
			else: print("Specified username/e-mail address not found in active sessions")
			
			self.update_prompt()
	
	def create_parser_login(self):
		parser = argparse.ArgumentParser(prog="login", add_help=False,
			description="login to Warmerise and store the session for later use")
		parser.add_argument("email", metavar="EMAIL", nargs="?", default=None, help="e-mail address to login with")
		parser.add_argument("password", metavar="PASS", nargs="?", default=None, help="password to login with")
		#parser.add_argument("-P", "--phpsessid", metavar="SESSION", help="PHPSESSID to login with")
		return parser
	
	def create_parser_session(self):
		parser = argparse.ArgumentParser(prog="session", add_help=False,
			description="switch to a different session or print information about sessions")
		parser.add_argument("-a", "--all", action="store_true", help="print information about all sessions")
		parser.add_argument("session", metavar="SESSION", nargs="?", default=None, help="username/email of session to switch to")
		return parser
	
	def print_session(self, session=None):
		""" Print information about a session """
		if not session and self.session: session = self.session
		elif not session: return
		pprint(vars(session))