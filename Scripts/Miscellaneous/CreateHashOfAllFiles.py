"""
Tested on: Windows
This program comes with absolutely no warranty.
"""
import argparse
import os
import hashlib

parser = argparse.ArgumentParser(description='Calculates the SHA-256-value of all files in the given folder and stores the hash-value in a file next to the hashed file.')

parser.add_argument('folder', help='Folder where the files are stored which should be hashed')

args = parser.parse_args()

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

for file in absolute_file_paths(args.folder):
    with open(file+".sha256","w+") as f:
        f.write(get_sha256_of_file(file))