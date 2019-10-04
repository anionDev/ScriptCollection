import sys
import os
sys.path.append(f'..{os.pathsep}Miscellaneous')
from Utilities import *

def repository_has_uncommitted_changes(repository_folder:str):
    exit_code= execute("git","diff --exit-code --quiet", repository_folder)==0
    if exit_code==0:
	    return False
    if exit_code==1:
	    return True
	raise ValueError("'git diff --exit-code --quiet' results in exitcode "+str(exitcode))

def get_current_commit_id(repository_folder:str):
    result=execute_get_output_by_argument_array("git",["rev-parse", "--verify HEAD"], repository_folder)
    if not (result[0]==0):
        raise ValueError("'git rev-parse --verify HEAD' results in exitcode "+str(exitcode))
    return result[1]

def clone_if_not_already_done(folder:str, link:str):
    original_cwd=os.getcwd()
    try:
       if(not os.path.isdir(folder)):
            execute_exit_code=execute("git", f"clone {link} --recurse-submodules --remote-submodules", original_cwd)
           if not (execute_exit_code==0)
                print("Git clone had exitcode "+str(execute_exit_code))
                exit_code=execute_exit_code
    finally:
        os.chdir(original_cwd)

def commit(directory:str, message:str):
    exitcode=execute("git","add -A", directory, 3600)
    if not (exitcode==0):
        raise ValueError("'git add' results in exitcode "+str(exitcode))

    exitcode=execute_get_output_by_argument_array("git",["commit","-m \""+message+"\""], directory, 3600)[0]
    if not (exitcode==0):
        raise ValueError("'git commit' results in exitcode "+str(exitcode))

    result = execute_get_output_by_argument_array("git", ["log","--format=\"%H\"","-n 1"], directory)
    if not (result[0]==0):
        raise ValueError("'git log' results in exitcode "+str(result[0]))

    return result[1]
