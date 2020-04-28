import os
import sys
from os.path import abspath
import traceback
import argparse
error_occurred=False
original_directory=os.getcwd()
current_directory = os.path.dirname(os.path.abspath(__file__))
os.chdir(current_directory)

try:

    sys.path.append(abspath(os.path.join(current_directory,f"..{os.path.sep}..{os.path.sep}..{os.path.sep}Miscellaneous")))
    from Utilities import *
    sys.path.append(abspath(os.path.join(current_directory,f"..{os.path.sep}..{os.path.sep}..{os.path.sep}Git")))
    from CommonGitFunctions import *
    from configparser import ConfigParser
    import time
    
    parser=argparse.ArgumentParser()
    parser.add_argument("configurationfile")
    args=parser.parse_args()
    configurationfile=args.configurationfile
    write_message_to_stdout(f"Run generic releasescript-part '{os.path.basename(__file__)}' with configurationfile '{configurationfile}'")    
    configparser=ConfigParser()
    configparser.read_file(open(configurationfile, mode="r", encoding="utf-8"))

    commit_id=merge(configparser.get('general','repository'), configparser.get('prepare','developmentbranchname'), configparser.get('prepare','masterbranchname'))
    version=get_semver_version_from_gitversion(configparser.get('general','repository'))
    create_tag(configparser.get('general','repository'), commit_id, configparser.get('prepare','gittagprefix')+ version)

except Exception as exception:
    write_exception_to_stderr_with_traceback(exception, traceback)
    error_occurred=True

finally:
    os.chdir(original_directory)

if(error_occurred):
    sys.exit(1)
else:
    sys.exit(0)
