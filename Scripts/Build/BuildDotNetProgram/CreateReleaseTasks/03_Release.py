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
    import tempfile
    import uuid
    
    parser=argparse.ArgumentParser()
    parser.add_argument("configurationfile")
    args=parser.parse_args()
    configurationfile=args.configurationfile
    write_message_to_stdout(f"Run generic releasescript-part '{os.path.basename(__file__)}' with configurationfile '{configurationfile}'")

    configparser=ConfigParser()
    configparser.read_file(open(configurationfile, mode="r", encoding="utf-8"))
    repository_folder=configparser.get('general','repository')
    version=get_semver_version_from_gitversion(repository_folder)
    commitmessage=f"Added {configparser.get('general','productname')} {configparser.get('prepare','gittagprefix')}{version}"

    #build nugetpackage
    if configparser.getboolean('release','createnugetpackage'): 
        commit_id = strip_new_lines_at_begin_and_end(execute_and_raise_exception_if_exit_code_is_not_zero("git", "rev-parse HEAD",repository_folder,30,0)[1])
        year = str(datetime.datetime.now().year)
        
        #todo move to new folder and then to versionbinarysubfolder
        tempdir=tempfile.gettempdir() + os.path.sep+str(uuid.uuid4())
        ensure_directory_exists(tempdir)
        move_content_of_folder(get_publishdirectory(configparser,version),tempdir)
        nuspecfilename=configparser.get('general','productname')+".nuspec"
        nuspecfolder=os.path.join(get_publishdirectory(configparser,version))
        ensure_directory_exists(nuspecfolder)
        nuspecfile=os.path.join(nuspecfolder,nuspecfilename)
        copyfile(configparser.get('release','nuspectemplatefile'),nuspecfile)
        newtarget=os.path.join(get_publishdirectory(configparser,version),"Binary")
        ensure_directory_exists(newtarget)
        move_content_of_folder(tempdir,newtarget)
        os.chdir(get_publishdirectory(configparser,version))
        with open(nuspecfilename, encoding="utf-8", mode="r") as f:
          nuspec_content=f.read()
          nuspec_content=nuspec_content.replace('__version__', version)
          nuspec_content=nuspec_content.replace('__commitid__', commit_id)
          nuspec_content=nuspec_content.replace('__year__', year)
          nuspec_content=nuspec_content.replace('__productname__', configparser.get('general','productname'))
          nuspec_content=nuspec_content.replace('__author__', configparser.get('general','author'))
          nuspec_content=nuspec_content.replace('__description__', configparser.get('general','description'))
        with open(nuspecfilename, encoding="utf-8", mode="w") as f:
          f.write(nuspec_content)
        execute_and_raise_exception_if_exit_code_is_not_zero("nuget", f"pack {nuspecfilename}",get_publishdirectory(configparser,version))
        
        latest_nupkg_file=configparser.get('general','productname')+"."+version+".nupkg"
        ensure_directory_does_not_exist(tempdir)
        
        #publish to local nuget-feed
        localnugettarget=configparser.get('release','localnugettarget')
        execute_and_raise_exception_if_exit_code_is_not_zero("dotnet",f"nuget push {latest_nupkg_file} --force-english-output --source {localnugettarget}",get_publishdirectory(configparser,version))
        commit(configparser.get('release','localnugettargetrepository'), commitmessage)
    
    commit(configparser.get('release','releaserepository'), commitmessage)
    
except Exception as exception:
    write_exception_to_stderr_with_traceback(exception, traceback)
    error_occurred=True

finally:
    os.chdir(original_directory)

if(error_occurred):
    sys.exit(1)
else:
    sys.exit(0)
