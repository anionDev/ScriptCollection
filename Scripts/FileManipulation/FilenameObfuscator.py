from shutil import copy2
import argparse
import hashlib
import os

parser = argparse.ArgumentParser(description='Obfuscates the names of all files in the given folder')

parser.add_argument('inputFolder', type=str, help='Specifies the foldere where the files are stored whose names should be obfuscated')
parser.add_argument('--nameMappingFile', type=str, default="NameMapping.txt", help = 'Specifies the file where the name-mapping will be written to')

args = parser.parse_args()

def get_sha256_of_file(file:str):
    sha256 = hashlib.sha256()
    with open(file, "rb") as fileObject:
        for chunk in iter(lambda: fileObject.read(4096), b""):
            sha256.update(chunk)
    return sha256.hexdigest()

directory=os.fsdecode(os.fsencode(args.inputFolder))
files = []
for file in os.listdir(directory):
    if os.path.isfile(os.path.join(directory, file)):
        files.append(os.path.join(directory, file))
with open(args.nameMappingFile, "a") as fileObject:
    for file in files:
        process_file(file)
    hash=get_sha256_of_file(file)
    new_name="TODO"
    new_line="TODO"
    fileObject.write(new_line + file + ";" + new_name + ";" + hash)
    #TODO rename file to new_name