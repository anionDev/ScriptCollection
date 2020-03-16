import sys
import os
import pathlib
sys.path.append(str(pathlib.Path(str(pathlib.Path(__file__).parent.absolute())+os.path.sep+".."+os.path.sep+"Miscellaneous").resolve()))
from Utilities import *

def repository_has_uncommitted_changes(repository_folder:str):
    argument="diff --exit-code --quiet"
    exit_code = execute_and_raise_exception_if_exit_code_is_not_zero("git",argument, repository_folder)[0]
    if exit_code==0:
        return False
    if exit_code==1:
        return True
    raise ValueError(f"'git {argument}' results in exitcode "+str(exitcode))

def get_current_commit_id(repository_folder:str):
    argument="rev-parse --verify HEAD"
    result=execute_and_raise_exception_if_exit_code_is_not_zero("git","rev-parse --verify HEAD", repository_folder)
    return result[1].replace('\r','').replace('\n','')

def push(folder:str, remotename:str, localbranchname:str, remotebranchname:str):
    argument=f"push {remotename} {localbranchname}:{remotebranchname}"
    result=execute_and_raise_exception_if_exit_code_is_not_zero("git",argument, repository_folder)
    if not (result[0]==0):
        raise ValueError(f"'git {argument}' results in exitcode "+str(exitcode))
    return result[1].replace('\r','').replace('\n','')

def clone_if_not_already_done(folder:str, link:str):
    exit_code=-1
    original_cwd=os.getcwd()
    try:
       if(not os.path.isdir(folder)):
           argument=f"clone {link} --recurse-submodules --remote-submodules"
           execute_exit_code=execute_and_raise_exception_if_exit_code_is_not_zero(f"git {argument}", argument, original_cwd)[0]
           if execute_exit_code!=0:
               print(f"'git {argument}' had exitcode "+str(execute_exit_code))
               exit_code=execute_exit_code
    finally:
        os.chdir(original_cwd)
    return exit_code

def commit(directory:str, message:str):
    
    execute_and_raise_exception_if_exit_code_is_not_zero("git","add -A", directory, 3600)[0]

    argument=f'commit -m "{message}"'
    exitcode=execute_full("git",argument, directory, 600)[0]
    if not (exitcode==0):
        print(f"Warning: 'git {argument}' results in exitcode "+str(exitcode)+". This means that probably either there were no changes to commit or an error occurred while commiting")

    return get_current_commit_id(directory)

def create_tag(directory:str, target_for_tag:str, tag:str):
    execute_and_raise_exception_if_exit_code_is_not_zero("git",f"tag {tag} {target_for_tag}", directory, 3600)

def checkout(directory:str, branch:str):
    execute_and_raise_exception_if_exit_code_is_not_zero("git","checkout "+branch, directory, 3600)

def merge(directory:str, sourcebranch:str, targetbranch:str):
    checkout(directory, targetbranch)
    execute_and_raise_exception_if_exit_code_is_not_zero("git","merge --no-commit --no-ff "+sourcebranch, directory, 3600)
    commit_id = commit(directory,f"Merge branch '{sourcebranch}' into '{targetbranch}'")
    return commit_id
