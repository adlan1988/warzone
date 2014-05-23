#!/usr/bin/env python

import argparse, cmd, getpass
import api, warmerise, xp
from pprint import pprint

import errors as err

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
		
		self.keyinter = False
		
		self.update_prompt()
	
	def start(self):
		""" Start the interpreter """
		while True:
			try:
				self.cmdloop()
				self.postloop()
				break
			except KeyboardInterrupt:
				print
				if not self.keyinter:
					self.keyinter = True
				else:
					exit(0)
			except err.WarmeriseWebError as e:
				print(str(e))
	
	def emptyline(self):
		pass
	
	def precmd(self, line=None):
		""" We have a command, clear key interrupt """
		self.keyinter = False
		return line
	
	def update_prompt(self):
		""" Update the prompt using selected session """
		sesname = ""
		if self.session is not None:
			sesname = "/%s" % self.session.username
		self.prompt = "(Warzone%s) " % sesname
	
	def prompt_login(self, email=None, password=None, phpsessid=None):
		""" Prompt the user to login to an account """
		session = None
		
		try:
			if phpsessid is not None: # PHPSESSID login
				raise NotImplementedError
			else:  # E-mail / password login
				noecho = "(Password will not echo)" if (password is None) else ""
				
				if email is None or password is None:
					print("Prompting for auth info: %s" % noecho)
				
				if email is None:
					email = raw_input("E-mail: ")
				
				if password is None:
					password = getpass.getpass("Password: ")
				
				session = warmerise.login(email, password)
		except err.WarmeriseAuthError as e:
			print("Login failed") # Use logging later
			return
		except err.WarmeriseStatusCodeError as e:
			print("Login failed (site may just be down)")
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
		""" Select a session or print information about them """
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
	
	def help_stats(self):
		self.create_parser_stats().print_help()
	
	def do_stats(self, str):
		""" Modify the stats of the account of the current session """
		parser = self.create_parser_stats()
		
		try: args = parser.parse_args(str.split())
		except: return
		
		# Make sure we're in a session
		if self.session is None:
			print("No login session to set stats for")
			return
		
		# Nothing to do
		if args.kills is None and args.deaths is None and args.killstreak is None:
			return
		
		# Refresh
		self.session.set_game_login()
		
		# If desired killstreak is less than or equal to current,
		# no point in sending
		if args.killstreak <= self.session.highest_killstreak:
			args.killstreak = None
		
		kills = deaths = killstreak = 0
		
		if args.kills is not None:
			kills = args.kills - self.session.kills
		if args.deaths is not None:
			deaths = args.deaths - self.session.deaths
		if args.killstreak is not None:
			killstreak = args.killstreak
		
		print("Sending stats...")
		self.api.save_score(session=self.session,
			kills=kills, deaths=deaths, killstreak=killstreak)
		
		print("Confirming change...")
		self.session.set_game_login()
		
		success = True
		
		if args.kills is not None and args.kills != self.session.kills:
			print("Kills count was not changed successfully")
			success = False
		if args.deaths is not None and args.deaths != self.session.deaths:
			print("Deaths count was not changed successfully")
			success = False
		if args.killstreak is not None and args.killstreak != self.session.highest_killstreak:
			print("Killstreak count was not changed successfully")
			success = False
		
		if success:
			print("All changes successful!")
	
	def help_xp(self):
		self.create_parser_xp().print_help()
	
	def do_xp(self, str):
		""" Set the XP for an account. Reserved for its own command as setting
		the XP to a greater value may require request spamming. """
		parser = self.create_parser_xp()
		
		try: args = parser.parse_args(str.split())
		except: return
		
		if args.method is None: args.method = "sync" # Default method
		
		if self.session is None:
			print("No login session to set xp for")
			return
		
		# Refresh
		self.session.set_game_login()
		
		# Nothing to do
		if args.xp == self.session.xp:
			return
		
		# No limit for subtracting
		if args.xp < self.session.xp:
			response = self.api.save_score(session=self.session, xp=(args.xp - self.session.xp))
		else:
			# Need to send a bunch of responses...
			incr = args.increment
			
			if incr > 49 and not args.ignore_roof:
				print("Lowering increment value to 49, anything greater is ignored by the API...")
				incr = 49
			
			diff = args.xp - self.session.xp
			
			grinder = xp.XPGrinder(session=self.session, diff=diff, increment=incr)
			
			if args.method == "sync": grinder.grind_sync()
			elif args.method == "async":
				try: grinder.grind_async()
				except ImportError:
					print("Async method not available, grequests not found")
					return
		
		self.session.set_game_login()
		
		if self.session.xp != args.xp:
			print("XP was not changed successfully")
	
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
	
	def create_parser_stats(self):
		parser = argparse.ArgumentParser(prog="stats", add_help=False,
			description="set kills, deaths, and highest killstreak for an account")
		parser.add_argument("-k", "--kills", type=int, default=None, help="set kills for an account")
		parser.add_argument("-d", "--deaths", type=int, default=None, help="set deaths for an account")
		parser.add_argument("-K", "--killstreak", type=int, default=None,
			help="set the highest killstreak for an account (warning: killstreak count cannot be decreased)")
		return parser
	
	def create_parser_xp(self):
		parser = argparse.ArgumentParser(prog="xp", add_help=False,
			description="set xp for an account")
		parser.add_argument("-a", "--method-async", dest="method", action="store_const", const="async",
			help="use asynchronous method to spam requests")
		parser.add_argument("-i", "--increment", type=int, default=49, help="amount to increment by (max: 49)")
		parser.add_argument("-R", "--ignore-roof", action="store_true", help="don't force the increment roof")
		parser.add_argument("xp", metavar="XP", type=int, help="desired amount of XP")
		return parser
	
	def print_session(self, session=None):
		""" Print information about a session """
		if not session and self.session: session = self.session
		elif not session: return
		pprint(vars(session))