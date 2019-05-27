import argparse
import os
import subprocess
import sys

parser = argparse.ArgumentParser(description='Changes the hash-value of the files in the given folder and renames them to obfuscated names. This script does not process subfolders transitively. Caution: This script can cause harm if you pass a wrong inputfolder-argument.')

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

parser.add_argument('--printtableheadline', type=to_boolean, const=True, default=True, nargs='?', help='Prints column-titles in the name-mapping-csv-file')
parser.add_argument('--namemappingfile', default="NameMapping.csv", help = 'Specifies the file where the name-mapping will be written to')
parser.add_argument('inputfolder', help='Specifies the foldere where the files are stored whose names should be obfuscated')

args = parser.parse_args()

def get_files_in_directory(directory):
    files = []
    for file in os.listdir(directory):
        file_with_directory=os.path.join(directory, file)
        if os.path.isfile(file_with_directory):
            files.append(file_with_directory)
    return files

d=normalize_path(args.inputfolder)
namemappingfile=normalize_path(args.namemappingfile)
if (os.path.isdir(d)):
    for file in get_files_in_directory(d):
        subprocess.call("python ChangeHashOfProgram.py \"" + file + "\"")
        os.remove(file)
        os.rename(file + ".modified", file)
    subprocess.call("python FilenameObfuscator.py --printtableheadline " + str(to_boolean(args.printtableheadline)) + " --namemappingfile \"" + namemappingfile + "\" \""+d+"\"")
else:
    print('Directory not found: ' + d)
    sys.exit(2)