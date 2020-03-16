import os
import sys
from os.path import abspath
import traceback
import argparse
error_occurred=False
original_directory=os.getcwd()
current_directory = os.path.dirname(os.path.abspath(__file__))

try:
    sys.path.append(abspath(os.path.join(current_directory,f"..{os.path.sep}..{os.path.sep}Miscellaneous")))
    from Utilities import *
    from datetime import datetime
    from configparser import ConfigParser

    parser=argparse.ArgumentParser()
    parser.add_argument("configurationfile")
    args=parser.parse_args()
    configurationfile=args.configurationfile
    write_message_to_stdout(f"Run generic releasescript with configurationfile '{configurationfile}'")

    configparser=ConfigParser()
    configparser.read(configurationfile)

    logfile=configparser.get('general','logfilefolder')+os.path.sep+"Release_"+str(datetime.today().strftime('%Y-%m-%d-%H-%M-%S'))+".log"
    execute_and_raise_exception_if_exit_code_is_not_zero("python", f"CreateRelease.py {configurationfile}", current_directory,3600,True,True,"Create"+configparser.get('general','productname')+"Release" ,False,logfile)

except Exception as exception:
    write_exception_to_stderr_with_traceback(exception, traceback)
    error_occurred=True

finally:
    os.chdir(original_directory)

if(error_occurred):
    sys.exit(1)
else:
    sys.exit(0)
