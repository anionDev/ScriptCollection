import os
import subprocess
import hashlib
import time
import datetime
import codecs
import sys
import xml.dom.minidom

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

def file_is_empty(file:str):
    return os.stat(file).st_size == 0

def execute(program:str, arguments:str, workingdirectory:str="",timeout=120):
    if not os.path.isabs(workingdirectory):
        workingdirectory=os.path.abspath(workingdirectory)
    exit_code = subprocess.call(program + " " + arguments, cwd=workingdirectory, timeout=timeout)
    return exit_code

def ensure_directory_exists(path:str):
    if(not os.path.isdir(path)):
        os.makedirs(path)

def ensure_file_exists(path:str):
    if(not os.path.isfile(path)):
        with open(path,"a+") as f:
            pass

def ensure_file_does_not_exist(path:str):
    if(os.path.isfile(path)):
        os.remove(path)

def get_time_from_internet():
    import ntplib
    response = ntplib.NTPClient().request('pool.ntp.org')
    return datetime.datetime.fromtimestamp(response.tx_time)

def format_xml_file(file:str, encoding:str):
    with codecs.open(file, 'r', encoding=encoding) as f:
        text = f.read()
    text=xml.dom.minidom.parseString(text).toprettyxml()
    with codecs.open(file, 'w', encoding=encoding) as f:
        f.write(text)
