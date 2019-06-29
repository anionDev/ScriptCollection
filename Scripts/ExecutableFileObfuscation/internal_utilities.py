"""
Tested on: Windows
This functions come with absolutely no warranty.
"""
import os
import hashlib
from pathlib import Path

def normalize_path(path:str):
    if (path.startswith("\"") and path.endswith("\"")) or (path.startswith("'") and path.endswith("'")):
        path = path[1:]
        path = path[:-1]
        return path
    else:
        return path

def to_boolean(value):
    if(type(value) is bool):
        return value
    if value.lower() in ('yes', 'true', 't', 'y', '1'):
        return True
    elif value.lower() in ('no', 'false', 'f', 'n', '0'):
        return False
    else:
        raise argparse.ArgumentTypeError(str(value) + ' is not boolean value.')

def get_files_in_directory(directory:str):
    files = []
    for file in os.listdir(directory):
        file_with_directory=os.path.join(directory, file)
        if os.path.isfile(file_with_directory):
            files.append(file_with_directory)
    return files

def delete_directory_and_its_content(directory:str):
    pth=Path(directory)
    for sub in pth.iterdir() :
        if sub.is_dir() :
            delete_directory_and_its_content(sub)
        else :
            sub.unlink()
    pth.rmdir()

def get_sha256_of_file(file:str):
    sha256 = hashlib.sha256()
    with open(file, "rb") as fileObject:
        for chunk in iter(lambda: fileObject.read(4096), b""):
            sha256.update(chunk)
    return sha256.hexdigest()

def append_line_to_file(file:str, line_content:str):
    with open(file, "a") as fileObject:
        mapping_file_is_empty = os.stat(file).st_size == 0
        if mapping_file_is_empty:
            new_line=""
        else:
            new_line="\n"
        fileObject.write(new_line + line_content)

def create_directory_transitively(path:str):
    os.makedirs(path)
