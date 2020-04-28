import re
import base64
import os
from subprocess import Popen, PIPE
import hashlib
import time
import shutil
import io
import tempfile
import uuid
from pathlib import Path
import codecs
import sys
import xml.dom.minidom
import datetime
from os import listdir
from os.path import isfile, join, isdir

def rename_names_of_all_files_and_folders(folder:str, replace_from:str, replace_to:str, replace_only_full_match=False):
    for file in get_direct_files_of_folder(folder):
        replace_in_filename(file, replace_from, replace_to, replace_only_full_match)
    for sub_folder in get_direct_folders_of_folder(folder):
        rename_names_of_all_files_and_folders(sub_folder, replace_from, replace_to, replace_only_full_match)
    replace_in_foldername(folder, replace_from, replace_to, replace_only_full_match)

def get_direct_files_of_folder(folder:str):
    result = [os.path.join(folder,f) for f in listdir(folder) if isfile(join(folder, f))]
    return result

def get_direct_folders_of_folder(folder:str):
    result = [os.path.join(folder,f) for f in listdir(folder) if isdir(join(folder, f))]
    return result

def replace_in_filename(file:str, replace_from:str, replace_to:str, replace_only_full_match=False):
    filename=Path(file).name
    if(should_get_replaced_helper(filename, replace_from, replace_only_full_match)):
        folder_of_file=os.path.dirname(file)
        os.rename(file,os.path.join(folder_of_file, filename.replace(replace_from, replace_to)))

def replace_in_foldername(folder:str, replace_from:str, replace_to:str, replace_only_full_match=False):
    foldername=Path(folder).name
    if(should_get_replaced_helper(foldername, replace_from, replace_only_full_match)):
        folder_of_folder=os.path.dirname(folder)
        os.rename(folder,os.path.join(folder_of_folder, foldername.replace(replace_from, replace_to)))

def should_get_replaced_helper(input_text, search_text, replace_only_full_match):
    if replace_only_full_match:
        return input_text==search_text
    else:
        return search_text in input_text

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

def string_to_boolean(value:str):
    value=value.strip().lower()
    if value in ('yes', 'true', 't', 'y', '1'):
        return True
    elif value in ('no', 'false', 'f', 'n', '0'):
        return False
    else:
        raise argparse.ArgumentTypeError(f"Can not convert '{value}' to a boolean value")

def file_is_empty(file:str):
    return os.stat(file).st_size == 0

def execute_and_raise_exception_if_exit_code_is_not_zero(program:str, arguments:str, workingdirectory:str="",timeoutInSeconds:int=3600,verbosity=1, addLogOverhead:bool=False, title:str=None, print_errors_as_information:bool=False, log_file:str=None,write_strerr_of_program_to_local_strerr_when_exitcode_is_not_zero:bool=False):
    result=execute_full(program, arguments, workingdirectory,print_errors_as_information, log_file, timeoutInSeconds, verbosity, addLogOverhead, title)
    if result[0]==0:
        return result
    else:
        if(write_strerr_of_program_to_local_strerr_when_exitcode_is_not_zero):
            write_message_to_stderr(result[2])
        raise Exception(f"'{workingdirectory}>{program} {arguments}' had exitcode {str(result[0])}")
def execute(program:str, arguments:str, workingdirectory:str="",timeoutInSeconds:int=3600,verbosity=1, addLogOverhead:bool=False, title:str=None, print_errors_as_information:bool=False, log_file:str=None):
    result = execute_raw(program, arguments, workingdirectory, timeoutInSeconds, verbosity, addLogOverhead, title, print_errors_as_information, log_file)
    return result[0]

def execute_raw(program:str, arguments:str, workingdirectory:str="",timeoutInSeconds:int=3600,verbosity=1, addLogOverhead:bool=False, title:str=None, print_errors_as_information:bool=False, log_file:str=None):
    return execute_full(program,arguments,workingdirectory,print_errors_as_information,log_file,timeoutInSeconds, verbosity, addLogOverhead, title)

def execute_full(program:str, arguments:str, workingdirectory:str="", print_errors_as_information:bool=False, log_file:str=None,timeoutInSeconds=3600,verbosity=1, addLogOverhead:bool=False, title:str=None):
    if string_is_none_or_whitespace(title):
        title_for_message=""
    else:
        title_for_message=f"for task '{title}' "
    title_local=f"epew {title_for_message}('{workingdirectory}>{program} {arguments}')"
    if verbosity==2:
        write_message_to_stdout(f"Start executing {title_local}")
    
    if workingdirectory=="":
        workingdirectory=os.getcwd()
    else:
        if not os.path.isabs(workingdirectory):
            workingdirectory=os.path.abspath(workingdirectory)
    
    output_file_for_stdout=tempfile.gettempdir() + os.path.sep+str(uuid.uuid4()) + ".temp.txt"
    output_file_for_stderr=tempfile.gettempdir() + os.path.sep+str(uuid.uuid4()) + ".temp.txt"

    argument=" -p "+program
    argument=argument+" -a "+base64.b64encode(arguments.encode('utf-8')).decode('utf-8')
    argument=argument+" -b "
    argument=argument+" -w "+'"'+workingdirectory+'"'
    if print_errors_as_information:
        argument=argument+" -i"
    if addLogOverhead:
        argument=argument+" -h"
    if verbosity==0:
        argument=argument+" -v Quiet"
    if verbosity==1:
        argument=argument+" -v Normal"
    if verbosity==2:
        argument=argument+" -v Verbose"
    argument=argument+" -o "+'"'+output_file_for_stdout+'"'
    argument=argument+" -e "+'"'+output_file_for_stderr+'"'
    if not string_is_none_or_whitespace(log_file):
        argument=argument+" -l "+'"'+log_file+'"'
    argument=argument+" -d "+str(timeoutInSeconds*1000)
    argument=argument+' -t "'+str_none_safe(title)+'"'
    process = Popen("epew "+argument)
    exit_code = process.wait()
    stdout=private_load_text(output_file_for_stdout)
    stderr=private_load_text(output_file_for_stderr)
    if verbosity==2:
        write_message_to_stdout(f"Finished executing {title_local} with exitcode "+str(exit_code))
    return (exit_code, stdout, stderr)
    
def private_load_text(file:str):
    if os.path.isfile(file):
        with io.open(file, mode='r', encoding="utf-8") as f:
            content = f.read()
        os.remove(file)
        return content
    else:
        return ""

def ensure_directory_exists(path:str):
    if(not os.path.isdir(path)):
        os.makedirs(path)

def ensure_file_exists(path:str):
    if(not os.path.isfile(path)):
        with open(path,"a+") as f:
            pass

def ensure_directory_does_not_exist(path:str):
    if(os.path.isdir(path)):
        shutil.rmtree(path)

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
    content_char=ord(0)
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
    return abs(datetime.datetime.now() - get_internet_time()) < maximal_tolerance_difference

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

def write_message_to_stdout(message:str):
    message=str(message)
    sys.stdout.write(message+"\n")
    sys.stdout.flush()

def write_message_to_stderr(message:str):
    message=str(message)
    sys.stderr.write(message+"\n")
    sys.stderr.flush()

def write_exception_to_stderr(exception: Exception, extra_message=None):
    write_message_to_stderr("Exception(")
    write_message_to_stderr("Type: "+str(type(exception)))
    write_message_to_stderr("Message: "+str(exception))
    if str is not None:
        write_message_to_stderr("Extra-message: "+str(extra_message))
    write_message_to_stderr(")")

def write_exception_to_stderr_with_traceback(exception:Exception, traceback, extra_message=None):
    write_message_to_stderr("Exception(")
    write_message_to_stderr("Type: "+str(type(exception)))
    write_message_to_stderr("Message: "+str(exception))
    if str is not None:
        write_message_to_stderr("Extra-message: "+str(extra_message))
    write_message_to_stderr("Traceback: "+traceback.format_exc())
    write_message_to_stderr(")")

def string_is_none_or_empty(string:str):
    if string is None:
        return True
    if type(string) == str:
        string == ""
    else:
        raise Exception("expected string-variable in argument of string_is_none_or_empty but the type was 'str'")

def string_is_none_or_whitespace(string:str):
    if string_is_none_or_empty(string):
        return True 
    else:
        return string.strip()=="" 

def strip_new_lines_at_begin_and_end(string:str):
    return string.lstrip('\r').lstrip('\n').rstrip('\r').rstrip('\n')

def get_semver_version_from_gitversion(folder:str):
    return get_version_from_gitversion(folder,"MajorMinorPatch")

def get_version_from_gitversion(folder:str, variable:str):
    return strip_new_lines_at_begin_and_end(execute_and_raise_exception_if_exit_code_is_not_zero("gitversion", "/showVariable "+variable,folder,30,0)[1])

def encapsulate_with_quotes(value:str):
    return '"'+value+'"'

def move_content_of_folder(srcDir, dstDir):
   srcDirFull=resolve_relative_path_from_current_working_directory(srcDir)
   dstDirFull=resolve_relative_path_from_current_working_directory(dstDir)
   for file in get_direct_files_of_folder(srcDirFull):
       shutil.move(file,dstDirFull)
   for sub_folder in get_direct_folders_of_folder(srcDirFull):
       shutil.move(sub_folder,dstDirFull)

def replace_xmltag_in_file(file, tag:str, new_value:str):
    with open(file, encoding="utf-8", mode="r") as f:
      content=f.read()
      content=re.sub(f"<{tag}>.*<\/{tag}>",f"<{tag}>{new_value}</{tag}>", content)
    with open(file, encoding="utf-8", mode="w") as f:
      f.write(content)

def update_version_in_csproj_file(file:str, version:str):
    replace_xmltag_in_file(file, "Version", version)
    replace_xmltag_in_file(file, "AssemblyVersion", version + ".0")
    replace_xmltag_in_file(file, "FileVersion", version + ".0")
