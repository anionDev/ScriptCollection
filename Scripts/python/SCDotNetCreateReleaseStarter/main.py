import os
import sys
from os.path import abspath
import traceback
import argparse

def SCdotnetCreateReleaseStarter_cli():

	sys.path.append(abspath(os.path.join(current_directory,f"..{os.path.sep}..{os.path.sep}Miscellaneous")))
	from datetime import datetime
	from configparser import ConfigParser

	parser=argparse.ArgumentParser()
	parser.add_argument("configurationfile")
	args=parser.parse_args()
	configurationfile=args.configurationfile
	write_message_to_stdout(f"Run generic releasescript with configurationfile '{configurationfile}'")

	configparser=ConfigParser()
	configparser.read_file(open(configurationfile, mode="r", encoding="utf-8"))

	logfile=configparser.get('general','logfilefolder')+os.path.sep+configparser.get('general','productname')+"_BuildAndPublish_"+str(datetime.today().strftime('%Y-%m-%d-%H-%M-%S'))+".log"
	execute_and_raise_exception_if_exit_code_is_not_zero("python", f"SCdotnetCreateRelease.py {configurationfile}", current_directory,3600,2,True,"Create"+configparser.get('general','productname')+"Release" ,False,logfile)


if __name__ == '__main__':
    SCdotnetCreateReleaseStarter_cli()
