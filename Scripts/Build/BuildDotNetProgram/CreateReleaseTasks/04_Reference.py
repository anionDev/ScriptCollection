import os
import argparse
import sys
from os.path import abspath
import traceback
error_occurred=False
original_directory=os.getcwd()
current_directory = os.path.dirname(os.path.abspath(__file__))
os.chdir(current_directory)

def get_publishdirectory(configparser, version:str):
    result=configparser.get('build','publishdirectory')
    result=result.replace("__version__",version)
    ensure_directory_exists(result)
    return result

try:

    sys.path.append(abspath(os.path.join(current_directory,f"..{os.path.sep}..{os.path.sep}..{os.path.sep}Miscellaneous")))
    from Utilities import *
    sys.path.append(abspath(os.path.join(current_directory,f"..{os.path.sep}..{os.path.sep}..{os.path.sep}Git")))
    from CommonGitFunctions import *
    import datetime
    from configparser import ConfigParser
    
    parser=argparse.ArgumentParser()
    parser.add_argument("configurationfile")
    args=parser.parse_args()
    configurationfile=args.configurationfile
    write_message_to_stdout(f"Run generic releasescript-part '{os.path.basename(__file__)}' with configurationfile '{configurationfile}'")

    configparser=ConfigParser()
    configparser.read_file(open(configurationfile, mode="r", encoding="utf-8"))
    
    repository_folder=configparser.get('general','repository')
    version='0.6.7'#get_semver_version_from_gitversion(repository_folder)
    
    publishdirectory=get_publishdirectory(configparser,version)
    opencoverreportfile=publishdirectory+os.path.sep+configparser.get('general','productname')+".TestCoverage.opencover.xml"
    
    #execute_and_raise_exception_if_exit_code_is_not_zero("reportgenerator", '-reports:"'+opencoverreportfile+'" -targetdir:"'+configparser.get('reference','coveragereportfolder')+'"')
    
    docfx_file_with_path=configparser.get('reference','docfxfile')
    docfxfolder=os.path.dirname(docfx_file_with_path)
    docfxfile=os.path.basename(docfx_file_with_path)
    execute_and_raise_exception_if_exit_code_is_not_zero("docfx", docfxfile, docfxfolder)
    
    commitmessage="Updated reference"
    #commit(configparser.get('reference','referencerepository'), commitmessage)
    #commit(configparser.get('release','releaserepository'), commitmessage)
     
except Exception as exception:
    write_exception_to_stderr_with_traceback(exception, traceback)
    error_occurred=True

finally:
    os.chdir(original_directory)

if(error_occurred):
    sys.exit(1)
else:
    sys.exit(0)
