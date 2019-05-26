from shutil import copy2
import argparse
import hashlib
import os
import uuid
import pathlib
import sys
parser = argparse.ArgumentParser(description='Obfuscates the names of all files in the given folder. Caution: This script can cause harm if you pass a wrong inputFolder-argument')

parser.add_argument('inputFolder', type=str, help='Specifies the foldere where the files are stored whose names should be obfuscated')
parser.add_argument('--nameMappingFile', type=str, default="NameMapping.csv", help = 'Specifies the file where the name-mapping will be written to')
parser.add_argument('--printTableHeadline', default = True, help='Prints column-titles in the output-csv')

args = parser.parse_args()

def toBoolean(value):
    if(type(value) is bool):
        return value
    if value.lower() in ('yes', 'true', 't', 'y', '1'):
        return True
    elif value.lower() in ('no', 'false', 'f', 'n', '0'):
        return False
    else:
        raise argparse.ArgumentTypeError(value + ' is not boolean value.')
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

directory=os.fsdecode(os.fsencode(args.inputFolder))
if (os.path.isdir(directory)):
    printTableHeadline=toBoolean(args.printTableHeadline)
    files = []
    if not os.path.isfile(args.nameMappingFile):
        with open(args.nameMappingFile, "a"):
            pass
    with open(args.nameMappingFile, "a") as fileObject:
        pass
    if printTableHeadline:
        append_line_to_file(args.nameMappingFile, "Original filename;new filename;SHA2-hash of file")
    for file in os.listdir(directory):
        if os.path.isfile(os.path.join(directory, file)):
            files.append(file)
    for file in files:
        full_file_name=os.path.join(directory, file)
        hash=get_sha256_of_file(full_file_name)
        extension=pathlib.Path(file).suffix
        new_file_name=os.path.join(directory, str(uuid.uuid4()) + extension)
        os.rename(full_file_name, new_file_name)
        append_line_to_file(args.nameMappingFile, full_file_name + ";" + new_file_name + ";" + hash)
        mapping_file_is_empty=False
else:
    sys.exit(2)