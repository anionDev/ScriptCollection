import os
from subprocess import Popen, PIPE
import hashlib
import time
import shutil
import uuid
from pathlib import Path
import codecs
import sys
import xml.dom.minidom
import datetime
from os import listdir
from os.path import isfile, join, isdir

def rename_names_of_all_files_and_folders(folder:str, replace_from:str, replace_to:str):
    for file in get_direct_files_of_folder(folder):
        replace_in_filename(file, replace_from, replace_to)
    for sub_folder in get_direct_folders_of_folder(folder):
        rename_names_of_all_files_and_folders(sub_folder, replace_from, replace_to)
    replace_in_foldername(folder, replace_from, replace_to)

def get_direct_files_of_folder(folder:str):
    result = [os.path.join(folder,f) for f in listdir(folder) if isfile(join(folder, f))]
    return result

def get_direct_folders_of_folder(folder:str):
    result = [os.path.join(folder,f) for f in listdir(folder) if isdir(join(folder, f))]
    return result

def replace_in_filename(file:str, replace_from:str, replace_to:str):
    filename=Path(file).name
    if(replace_from in filename):
        folder_of_file=os.path.dirname(file)
        os.rename(file,os.path.join(folder_of_file, filename.replace(replace_from, replace_to)))

def replace_in_foldername(folder:str, replace_from:str, replace_to:str):
    foldername=Path(folder).name
    if(replace_from in foldername):
        folder_of_folder=os.path.dirname(folder)
        os.rename(folder,os.path.join(folder_of_folder, foldername.replace(replace_from, replace_to)))

def absolute_file_paths(directory:str):
   for dirpath,_,filenames in os.walk(directory):
       for f in filenames:
           yield os.path.abspath(os.path.join(dirpath, f))

def str_none_safe(variable):
    if variable is None:
        return ''
    else:
        return str(variable)

def get_sha256_of_file(file:str):
    sha256 = hashlib.sha256()
    with open(file, "rb") as fileObject:
        for chunk in iter(lambda: fileObject.read(4096), b""):
            sha256.update(chunk)
    return sha256.hexdigest()

def remove_duplicates(input):
    result=[]
    for item in input:
        if not item in result:
            result.append(item)
    return result

def string_to_boolean(value):
    if isinstance(value, bool):
       return value
    if value.lower() in ('yes', 'true', 't', 'y', '1'):
        return True
    elif value.lower() in ('no', 'false', 'f', 'n', '0'):
        return False
    else:
        raise argparse.ArgumentTypeError('Boolean value expected.')

def file_is_empty(file:str):
    return os.stat(file).st_size == 0

def execute(program:str, arguments, workingdirectory:str="",timeout=120, shell=False, write_output_to_console=True):
    result = execute_get_output(program, arguments, workingdirectory, timeout, shell)
    if write_output_to_console:
        sys.stdout.write(result[1]+'\n')
        sys.stderr.write(result[2]+'\n')
    return result[0]

def execute_and_raise_exception_if_exit_code_is_not_zero(program:str, arguments, workingdirectory:str="",timeout=120, shell=False):
    exit_code=execute(program, arguments, workingdirectory, timeout, shell)
    if exit_code!=0:
        raise Exception(f"'{workingdirectory}>{program} {arguments}' had exitcode {exit_code}")

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
    if workingdirectory=="":
        workingdirectory=os.getcwd()
    else:
        if not os.path.isabs(workingdirectory):
            workingdirectory=os.path.abspath(workingdirectory)
    program_and_argument_as_string=" ".join(program_and_arguments)
    write_message_to_stdout(f"{workingdirectory}>{program_and_argument_as_string}")
    process = Popen(program_and_argument_as_string, stdout=PIPE, stderr=PIPE, cwd=workingdirectory,shell=shell)
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

def format_xml_file(file:str, encoding:str):
    with codecs.open(file, 'r', encoding=encoding) as f:
        text = f.read()
    text=xml.dom.minidom.parseString(text).toprettyxml()
    with codecs.open(file, 'w', encoding=encoding) as f:
        f.write(text)

def get_clusters_and_sectors(dispath:str):
    import ctypes
    sectorsPerCluster = ctypes.c_ulonglong(0)
    bytesPerSector = ctypes.c_ulonglong(0)
    rootPathName = ctypes.c_wchar_p(dispath)
    ctypes.windll.kernel32.GetDiskFreeSpaceW(rootPathName, ctypes.pointer(sectorsPerCluster), ctypes.pointer(bytesPerSector), None, None)
    return (sectorsPerCluster.value, bytesPerSector.value)

def write_content_to_random_file(content:str):
    temp_file=str(uuid.uuid4())
    written_files.append(temp_file)
    with open(temp_file, 'w+') as f:
        f.write(file_content)
    return temp_file

def wipe_disk(diskpath:str, iterations=1):
    total, used, free = shutil.disk_usage(diskpath)
    id = str(uuid.uuid4())
    temp_folder=diskpath+os.linesep+id
    ensure_directory_exists(temp_folder)
    original_working_directory=os.getcwd()
    content_char="x"
    try:
        for iteration_number in list(range(iterations)):
            print("Start iteration "+str(iteration_number+1)+"...")
            os.chdir(temp_folder)
            total, used, free = shutil.disk_usage(diskpath)
            clusters_and_sectors=get_clusters_and_sectors(diskpath)
            written_files=[]
            file_size=clusters_and_sectors[0]*clusters_and_sectors[1]
            file_content=content_char * file_size
            while file_size < free:
                written_files.append(create_file(file_content))
                total, used, free = shutil.disk_usage(diskpath)
            if 0 < free:
                written_files.append(create_file(free))
            for file in written_files:
                os.remove(file)
    finally:
        os.chdir(original_working_directory)

def extract_archive_with_7z(unzip_file:str, file:str, password:str, output_directory:str):
    password_set=not password is None
    file_name=Path(file).name
    file_folder=os.path.dirname(file)
    argument="x"
    if password_set:
        argument=argument+" -p\""+password+"\""
    argument=argument+" -o"+output_directory
    argument=argument+" "+file_name
    return execute(unzip_file,argument,file_folder)

def get_internet_time():
    import ntplib
    response = ntplib.NTPClient().request('pool.ntp.org')
    return datetime.datetime.fromtimestamp(response.tx_time)

def system_time_equals_internet_time(maximal_tolerance_difference: datetime.timedelta):
    return abs(datetime.datetime.now()-get_internet_time())<maximal_tolerance_difference

def resolve_relative_path_from_current_working_directory(path:str):
    return resolve_relative_path(path, os.getcwd())

def resolve_relative_path(path:str, base_path:str):
    if(os.path.isabs(path)):
        return path
    else:
        return str(Path(os.path.join(base_path, path)).resolve())

def get_metadata_for_file_for_clone_folder_structure(file:str):
    size=os.path.getsize(file)
    last_modified_timestamp=os.path.getmtime(file)
    hash_value=get_sha256_of_file(file)
    last_access_timestamp=os.path.getatime(file)
    return f'{{"size":"{size}","sha256":"{hash_value}","mtime":"{last_modified_timestamp}","atime":"{last_access_timestamp}"}}'

def clone_folder_structure(source:str, target:str, write_information_to_file):
    source=resolve_relative_path(source,os.getcwd())
    target=resolve_relative_path(target,os.getcwd())
    length_of_source=len(source)
    for source_file in absolute_file_paths(source):
        target_file=target+source_file[length_of_source:]
        ensure_directory_exists(os.path.dirname(target_file))
        with open(target_file,'w',encoding='utf8') as f:
            f.write(get_metadata_for_file_for_clone_folder_structure(source_file))

def system_time_equals_internet_time_with_default_tolerance():
    return system_time_equals_internet_time(get_default_tolerance_for_system_time_equals_internet_time())

def check_system_time(maximal_tolerance_difference: datetime.timedelta):
    if not system_time_equals_internet_time(maximal_tolerance_difference):
        raise ValueError("System time may be wrong")

def check_system_time_with_default_tolerance():
    return check_system_time(get_default_tolerance_for_system_time_equals_internet_time())

def get_default_tolerance_for_system_time_equals_internet_time():
    return datetime.timedelta(hours=0, minutes=0, seconds=3)

def write_message_to_stderr(message:str):
    sys.stderr.write(message+"\n")
    sys.stderr.flush()

def write_message_to_stdout(message:str):
    sys.stdout.write(message+"\n")
    sys.stdout.flush()

def write_exception_to_stderr_with_traceback(exception:Exception, traceback):
    write_message_to_stderr("Exception(")
    write_message_to_stderr("Type: "+str(type(exception)))
    write_message_to_stderr("Message: "+str(exception))
    write_message_to_stderr("Traceback: {"+traceback)
    write_message_to_stderr(")")

def write_exception_to_stderr(exception:Exception):
    write_message_to_stderr("Exception(")
    write_message_to_stderr("Type: "+str(type(exception)))
    write_message_to_stderr("Message: "+str(exception))
    write_message_to_stderr(")")
