"""
Tested on: Windows
This program comes with absolutely no warranty.
"""
import argparse
import os
import hashlib

parser = argparse.ArgumentParser(description='Replaces certain substrings in filenames.')

parser.add_argument('folder', help='Folder where the files are stored which should be renamed')
parser.add_argument('substringInFilename', help='String to be replaced')
parser.add_argument('newSubstringInFilename', help='new string value for filename')

args = parser.parse_args()

def absolute_file_paths(directory:str):
   for dirpath,_,filenames in os.walk(directory):
       for f in filenames:
           yield os.path.abspath(os.path.join(dirpath, f))

def process_file(file:str):
    new_filename=os.path.join(os.path.dirname(file),os.path.basename(file).replace(args.substringInFilename, args.newSubstringInFilename))
    if file != new_filename:
        if os.path.isfile(new_filename):
            print("Warning: " + new_filename + " does already exist")
        else:
            os.rename(file, new_filename)

for file in absolute_file_paths(args.folder):
    process_file(file)
