import os
from shutil import copyfile
import argparse
import sys
from os.path import abspath
import traceback
error_occurred=False
original_directory=os.getcwd()
current_directory = os.path.dirname(os.path.abspath(__file__))
os.chdir(current_directory)

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
    configparser.read(configurationfile)

    #build nupkg
    repository_folder=configparser.get('general','repository')
    version=get_semver_version_from_gitversion(repository_folder)
    commit_id = strip_new_lines_at_begin_and_end(execute_and_raise_exception_if_exit_code_is_not_zero("git", "rev-parse HEAD",repository_folder)[1])
    year = str(datetime.datetime.now().year)
    nuspecfilename=configparser.get('general','productname')+".nuspec"
    copyfile(configparser.get('release','nuspectemplatefile'), os.path.join(configparser.get('build','publishdirectory'),version,nuspecfilename))
    os.chdir(os.path.join(configparser.get('build','publishdirectory'),version))
    with open(nuspecfilename, encoding="utf-8", mode="r") as f:
      nuspec_content=f.read().replace('__version__', version).replace('__commitid__', commit_id).replace('__year__', year)
    with open(nuspecfilename, encoding="utf-8", mode="w") as f:
      f.write(nuspec_content)
    execute_and_raise_exception_if_exit_code_is_not_zero("nuget", f"pack {nuspecfilename}",os.path.join(configparser.get('build','publishdirectory'),version))

except Exception as exception:
    write_exception_to_stderr_with_traceback(exception, traceback)
    error_occurred=True

finally:
    os.chdir(original_directory)

if(error_occurred):
    sys.exit(1)
else:
    sys.exit(0)
