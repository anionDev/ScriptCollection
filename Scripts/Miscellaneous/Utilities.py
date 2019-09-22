import os
from subprocess import Popen, PIPE
import hashlib
import time
import datetime
import codecs
import sys
import xml.dom.minidom
import datetime

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

def remove_duplicates(sequence):
    seen = set()
    seen_add = seen.add
    return [x for x in sequence if not (x in seen or seen_add(x))]

def string_to_boolean(v):
    if isinstance(v, bool):
       return v
    if v.lower() in ('yes', 'true', 't', 'y', '1'):
        return True
    elif v.lower() in ('no', 'false', 'f', 'n', '0'):
        return False
    else:
        raise argparse.ArgumentTypeError('Boolean value expected.')

def file_is_empty(file:str):
    return os.stat(file).st_size == 0

def execute(program:str, arguments, workingdirectory:str="",timeout=120, shell=False):
    return execute_get_output(program, arguments, workingdirectory, timeout, shell)[0]

def execute_get_output(program:str, arguments:str, workingdirectory:str="",timeout=120, shell=False):
    program_and_arguments=arguments.split()
    program_and_arguments=[program]
    program_and_arguments.extend(arguments.split())
    return execute_raw(program_and_arguments,workingdirectory,timeout,shell)

def execute_get_output_by_argument_array(program:str, arguments, workingdirectory:str="",timeout=120, shell=False):
    program_and_arguments=[program]
    program_and_arguments.extend(arguments)
    return execute_raw(program_and_arguments,workingdirectory,timeout,shell)

def execute_raw(program_and_arguments, workingdirectory:str="",timeout=120, shell=False):
    if not os.path.isabs(workingdirectory):
        workingdirectory=os.path.abspath(workingdirectory)
    process = Popen(program_and_arguments, stdout=PIPE, stderr=PIPE, cwd=workingdirectory,shell=shell)
    stdout, stderr = process.communicate()
    exit_code = process.wait()
    return (exit_code, stdout.decode("utf-8"), stderr.decode("utf-8"))

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

def format_xml_file(file:str, encoding:str):
    with codecs.open(file, 'r', encoding=encoding) as f:
        text = f.read()
    text=xml.dom.minidom.parseString(text).toprettyxml()
    with codecs.open(file, 'w', encoding=encoding) as f:
        f.write(text)

def extract_winrar_archive(file:str, password:str):
    password_set=password is None
    argument="x "+"\""+file+"\""
    if password_set:
        argument=argument+" -p"+password
    return execute("winrar",argument,os.getcwd(),sys.maxsize)

def get_internet_time():
    return datetime.datetime.now()#TODO

def system_time_equals_internet_time(maximal_tolerance_difference: datetime.timedelta):
    return abs(get_internet_time()-datetime.datetime)<maximal_tolerance_difference

def system_time_equals_internet_time_with_default_tolerance():
    return system_time_equals_internet_time(get_default_tolerance_for_system_time_equals_internet_time())

def check_system_time(maximal_tolerance_difference: datetime.timedelta):
    if not system_time_equals_internet_time(maximal_tolerance_difference):
        raise ValueError("System time may be wrong")

def check_system_time_with_default_tolerance():
    return check_system_time(get_default_tolerance_for_system_time_equals_internet_time())

def get_default_tolerance_for_system_time_equals_internet_time():
    return datetime.timedelta(hours=0, minutes=0, seconds=3)
