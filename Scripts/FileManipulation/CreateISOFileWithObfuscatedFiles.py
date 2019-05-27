import argparse
import os
import subprocess
from shutil import copy2
parser = argparse.ArgumentParser(description='Creates an iso file with the files in the given folder and changes their names and hash-values.')

parser.add_argument('inputFolder', type=str, help='Specifies the foldere where the files are stored which should be added to the iso-file')
parser.add_argument('--outputFile', type=str, default="files.iso", help = 'Specifies the output-iso-file and its location')

args = parser.parse_args()

def get_files_in_directory(directory):
    files = []
    for file in os.listdir(directory):
        file_with_directory=os.path.join(directory, file)
        if os.path.isfile(file_with_directory):
            files.append(file_with_directory)
    return files

directory=os.fsdecode(os.fsencode(args.inputFolder))
if (os.path.isdir(directory)):
    temp_directory=directory+"_temp"
    if not os.path.exists(temp_directory):
        os.makedirs(temp_directory)
    for file in get_files_in_directory(directory):
        copy2(file, temp_directory)
    #TODO
else:
    print('Directory not found: ' + directory)
    sys.exit(2)