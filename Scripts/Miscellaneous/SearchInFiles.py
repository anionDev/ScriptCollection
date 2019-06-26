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

bytes_ascii=0#TODO
bytes_unicode=0#TODO

def absolute_file_paths(directory:str):
   for dirpath,_,filenames in os.walk(directory):
       for f in filenames:
           yield os.path.abspath(os.path.join(dirpath, f))

def file_contains_byte_array(file:str, byte_array:str):
    return false#TODO
def check_file(file:str):
    if file_contains_string(file,bytes_ascii):
        print(file)
    if file_contains_string(file,bytes_unicode):
        print(file)

for file in absolute_file_paths(args.folder):
    check_file(file)