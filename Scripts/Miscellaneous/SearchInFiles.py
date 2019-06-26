"""
Tested on: Windows
This program comes with absolutely no warranty.
"""
import argparse
import os

parser = argparse.ArgumentParser(description='Searchs for the given searchstrings in the content of all files in the given folder. This program prints all files where the given searchstring was found to the console')

parser.add_argument('folder', help='Folder for search')
parser.add_argument('searchstring', help = 'string to look for')

args = parser.parse_args()

bytes_ascii = bytes(args.searchstring,"ascii")
bytes_utf16 = bytes(args.searchstring,"utf-16")#often called "unicode-encoding"
def absolute_file_paths(directory:str):
   for dirpath,_,filenames in os.walk(directory):
       for f in filenames:
           yield os.path.abspath(os.path.join(dirpath, f))

def file_contains_byte_array(file:str, byte_array:str):
    try:
        with open(file, mode='rb') as file:
           return byte_array in file.read()
    except:
        pass
def check_file(file:str):
    if file_contains_byte_array(file,bytes_ascii):
        print(file)
    elif file_contains_byte_array(file,bytes_utf16):
        print(file)

for file in absolute_file_paths(args.folder):
    check_file(file)