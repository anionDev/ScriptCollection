import argparse
import os
import subprocess
import shutil
from pathlib import Path
import sys

parser = argparse.ArgumentParser(description='Creates an iso file with the files in the given folder and changes their names and hash-values.')

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

parser.add_argument('--outputfile', default="files.iso", help = 'Specifies the output-iso-file and its location')
parser.add_argument('--printtableheadline', type=to_boolean, const=True, default=True,nargs='?', help='Prints column-titles in the name-mapping-csv-file')
parser.add_argument('--namemappingfile', default="NameMapping.csv", help = 'Specifies the file where the name-mapping will be written to')
parser.add_argument('inputfolder', help='Specifies the foldere where the files are stored which should be added to the iso-file')

args = parser.parse_args()

def get_files_in_directory(directory):
    files = []
    for file in os.listdir(directory):
        file_with_directory=os.path.join(directory, file)
        if os.path.isfile(file_with_directory):
            files.append(file_with_directory)
    return files

def delete_directory_and_its_content(directory:str):
    pth=Path(directory)
    for sub in pth.iterdir() :
        if sub.is_dir() :
            delete_folder(sub)
        else :
            sub.unlink()
    pth.rmdir()

d=normalize_path(args.inputfolder)
namemappingfile=normalize_path(args.namemappingfile)
outputfile=normalize_path(args.outputfile)
if (os.path.isdir(d)):
    temp_directory=d+"_temp"
    if os.path.isdir(temp_directory):
        delete_directory_and_its_content(temp_directory)
    os.mkdir(temp_directory)
    if os.path.isfile(namemappingfile):
        os.remove(namemappingfile)
    for file in get_files_in_directory(d):
        shutil.copy2(file, temp_directory)
    subprocess.call("python ObfuscateFilesFolder.py --printtableheadline " + str(to_boolean(args.printtableheadline)) + " --namemappingfile \"" + namemappingfile + "\" \""+temp_directory+"\"")
    shutil.move(args.namemappingfile, temp_directory)
    #TODO create iso with content of temp_directory
    #TODO delete temp_directory
else:
    print('Directory not found: ' + d)
    sys.exit(2)