#!/usr/bin/env python

import argparse
import warmerise
import interpreter as warzonecmd

def main():
	parser = create_parser()
	args = parser.parse_args()
	
	#if args.email and args.password:
	#	session = warmerise.login(email=args.email, password=args.password)
	#	pprint(vars(session))
	
	interpreter = warzonecmd.WarzoneCmd()
	
	if args.email or args.password:
		interpreter.prompt_login(email=args.email, password=args.password)
	
	interpreter.start()
	
def create_parser():
	parser = argparse.ArgumentParser(add_help=True,
		description="tool to mess with Warmerise")
	parser.add_argument("-l", "--email", metavar="EMAIL", help="e-mail address to login with")
	parser.add_argument("-p", "--password", metavar="PASSWORD", help="password to login with")
	return parser

if __name__ == "__main__":
	main()