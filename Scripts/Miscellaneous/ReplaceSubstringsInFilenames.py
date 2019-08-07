"""
Tested on: Windows
This program comes with absolutely no warranty.
This program requires "pip install Send2Trash".
"""
import argparse
import os
import filecmp
parser = argparse.ArgumentParser(description='Replaces certain substrings in filenames. This program requires "pip install Send2Trash" in certain cases.')

parser.add_argument('folder', help='Folder where the files are stored which should be renamed')
parser.add_argument('substringInFilename', help='String to be replaced')
parser.add_argument('newSubstringInFilename', help='new string value for filename')
parser.add_argument('conflictResolveMode', help='Set a method how to handle cases where a file with the new filename already exits and the files have not the same content. Possible values are: ignore, preservenewest, merge')

args = parser.parse_args()

def absolute_file_paths(directory:str):
   for dirpath,_,filenames in os.walk(directory):
       for filename in filenames:
           yield os.path.abspath(os.path.join(dirpath, filename))

def move_to_bin(file:str):
    import send2trash
    send2trash.send2trash(file)

merge_separator=[0x0A]
def merge_files(sourcefile:str, targetfile:str):
    with open(sourcefile, "rb") as f:
        source_data = f.read()
    fout = open(targetfile, "ab")
    fout.write(bytes(merge_separator))
    fout.write(source_data)
    fout.close()

def process_file(file:str):
    new_filename=os.path.join(os.path.dirname(file),os.path.basename(file).replace(args.substringInFilename, args.newSubstringInFilename))
    if file != new_filename:
        if os.path.isfile(new_filename):
            if(filecmp.cmp(file, new_filename)):
                move_to_bin(file)
            else:
                if(args.conflictResolveMode=="ignore"):
                    pass
                elif(args.conflictResolveMode=="preservenewest"):
                    if(os.path.getmtime(file) - os.path.getmtime(new_filename) > 0):
                        move_to_bin(file)
                    else:
                        move_to_bin(new_filename)
                        os.rename(file, new_filename)
                elif(args.conflictResolveMode=="merge"):
                    merge_files(file, new_filename)
                    move_to_bin(file)
                else:
                    raise Exception('Unknown conflict resolve mode')
        else:
            os.rename(file, new_filename)

for file in absolute_file_paths(args.folder):
    process_file(file)
