import os
import sys
from os.path import abspath
import traceback
original_directory=os.getcwd()
current_directory = os.path.dirname(os.path.abspath(__file__))
os.chdir(current_directory)
error_occurred=False

try:

    script_folder=abspath(os.path.join(current_directory,f".."))
    sys.path.append(f"{script_folder}{os.path.sep}Miscellaneous")
    from Utilities import *
    sys.path.append(f"{script_folder}{os.path.sep}Git")
    from CommonGitFunctions import *
    from configparser import ConfigParser
    configuration_file=sys.argv[1]

    #create release
    generic_createreleasescript_script=abspath(f"{script_folder}{os.path.sep}Build{os.path.sep}BuildDotNetProgram{os.path.sep}CreateReleaseStarter.py")
    execute_and_raise_exception_if_exit_code_is_not_zero("python",f"{generic_createreleasescript_script} {configuration_file}")
    
    #overhead
    configparser=ConfigParser()
    configparser.read(configuration_file)
    version=get_semver_version_from_gitversion(configparser.get('general','repository'))
    latest_nupkg_folder=configparser.get('build','publishdirectory')+os.path.sep+version
    latest_nupkg_file=configparser.get('general','productname')+"."+version+".nupkg"
    commitmessage=f"Added {configparser.get('general','productname')} {configparser.get('prepare','gittagprefix')}{version}"
    commit(configparser.get('release','releaserepository'), commitmessage)
    
    #publish to local nuget-feed
    localnugettarget=configparser.get('release','localnugettarget')
    execute_and_raise_exception_if_exit_code_is_not_zero("dotnet",f"nuget push {latest_nupkg_file} --force-english-output --source {localnugettarget}",latest_nupkg_folder)
    commit(configparser.get('release','localnugettargetrepository'), commitmessage)
    
except Exception as exception:
    write_exception_to_stderr_with_traceback(exception, traceback)
    error_occurred=True

finally:
    os.chdir(original_directory)

if(error_occurred):
    sys.exit(1)
else:
    sys.exit(0)
