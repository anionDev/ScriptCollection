import os
import subprocess
import hashlib

def absolute_file_paths(directory:str):
   for dirpath,_,filenames in os.walk(directory):
       for f in filenames:
           yield os.path.abspath(os.path.join(dirpath, f))

def get_sha256_of_file(file:str):
    sha256 = hashlib.sha256()
    with open(file, "rb") as fileObject:
        for chunk in iter(lambda: fileObject.read(4096), b""):
            sha256.update(chunk)
    return sha256.hexdigest()

def execute(program:str, arguments:str, workingdirectory:str="",timeout=120):
    if not os.path.isabs(workingdirectory):
        workingdirectory=os.path.abspath(workingdirectory)
    exit_code = subprocess.call(program + " " + arguments, cwd=workingdirectory, timeout=timeout)
    return exit_code

def ensure_directory_exists(path:str):
    if(not os.path.isdir(path)):
        os.makedirs(path)
def ensure_file_does_not_exist(path:str):
    if(os.path.isfile(path)):
        os.remove(path)

def commit(directory:str, message:str):
    execute("git","add -A",directory,3600)
    execute("git","commit -m \""+message+"\"",directory)
