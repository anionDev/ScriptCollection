from shutil import copy2
import argparse
import hashlib
import os
import uuid
import pathlib
import sys
parser = argparse.ArgumentParser(description='Obfuscates the names of all files in the given folder. Caution: This script can cause harm if you pass a wrong inputFolder-argument')

parser.add_argument('inputFolder', type=str, help='Specifies the foldere where the files are stored whose names should be obfuscated')
parser.add_argument('--nameMappingFile', type=str, default="NameMapping.txt", help = 'Specifies the file where the name-mapping will be written to')

args = parser.parse_args()

def get_sha256_of_file(file:str):
    sha256 = hashlib.sha256()
    with open(file, "rb") as fileObject:
        for chunk in iter(lambda: fileObject.read(4096), b""):
            sha256.update(chunk)
    return sha256.hexdigest()
def remove_extension(filename, extension):
  if extension == "":
    return filename
  if filename.endswith(extension):
    return filename[:-len(extension)]
  else:
    return filename

directory=os.fsdecode(os.fsencode(args.inputFolder))
if (os.path.isdir(directory)):
    files = []
    if not os.path.isfile(args.nameMappingFile):
        with open(args.nameMappingFile, "w"):
            pass
    mapping_file_is_empty=os.stat(args.nameMappingFile).st_size == 0
    for file in os.listdir(directory):
        if os.path.isfile(os.path.join(directory, file)):
            files.append(file)
    with open(args.nameMappingFile, "a") as fileObject:
        for file in files:
            full_file_name=os.path.join(directory, file)
            hash=get_sha256_of_file(full_file_name)
            if mapping_file_is_empty:
              new_line=""
            else:
              new_line="\n"
            extension=pathlib.Path(file).suffix
            file_without_extension=remove_extension(file, extension)
            new_file_name=os.path.join(directory, str(uuid.uuid4()) + extension)
            os.rename(full_file_name, new_file_name)
            fileObject.write(new_line + full_file_name + ";" + new_file_name + ";" + hash)
            mapping_file_is_empty=False
else:
    sys.exit(2)