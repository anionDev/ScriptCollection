from shutil import copy2
import argparse
import hashlib
import os
import uuid
import pathlib
import sys

parser = argparse.ArgumentParser(description='Obfuscates the names of all files in the given folder. Caution: This script can cause harm if you pass a wrong inputfolder-argument.')

def to_boolean(value):
    if(type(value) is bool):
        return value
    if value.lower() in ('yes', 'true', 't', 'y', '1'):
        return True
    elif value.lower() in ('no', 'false', 'f', 'n', '0'):
        return False
    else:
        raise argparse.ArgumentTypeError(str(value) + ' is not boolean value.')

def normalize_path(path:str):
    if (path.startswith("\"") and path.endswith("\"")) or (path.startswith("'") and path.endswith("'")):
        path = path[1:]
        path = path[:-1]
        return path
    else:
        return path

parser.add_argument('--printtableheadline', type=to_boolean, const=True, default=True, nargs='?', help='Prints column-titles in the name-mapping-csv-file')
parser.add_argument('--namemappingfile', default="NameMapping.csv", help = 'Specifies the file where the name-mapping will be written to')
parser.add_argument('inputfolder', help='Specifies the foldere where the files are stored whose names should be obfuscated')

args = parser.parse_args()

def get_sha256_of_file(file:str):
    sha256 = hashlib.sha256()
    with open(file, "rb") as fileObject:
        for chunk in iter(lambda: fileObject.read(4096), b""):
            sha256.update(chunk)
    return sha256.hexdigest()

def append_line_to_file(file, line_content):
    with open(file, "a") as fileObject:
        mapping_file_is_empty = os.stat(file).st_size == 0
        if mapping_file_is_empty:
            new_line=""
        else:
            new_line="\n"
        fileObject.write(new_line + line_content)

d=normalize_path(args.inputfolder)
namemappingfile=normalize_path(args.namemappingfile)
if (os.path.isdir(d)):
    printtableheadline=to_boolean(args.printtableheadline)
    files = []
    if not os.path.isfile(namemappingfile):
        with open(namemappingfile, "a"):
            pass
    with open(namemappingfile, "a") as fileObject:
        pass
    if printtableheadline:
        append_line_to_file(namemappingfile, "Original filename;new filename;SHA2-hash of file")
    for file in os.listdir(d):
        if os.path.isfile(os.path.join(d, file)):
            files.append(file)
    for file in files:
        full_file_name=os.path.join(d, file)
        hash=get_sha256_of_file(full_file_name)
        extension=pathlib.Path(file).suffix
        new_file_name=os.path.join(d, str(uuid.uuid4()) + extension)
        os.rename(full_file_name, new_file_name)
        append_line_to_file(namemappingfile, full_file_name + ";" + new_file_name + ";" + hash)
        mapping_file_is_empty=False
else:
    print('Directory not found:' + d)
    sys.exit(2)