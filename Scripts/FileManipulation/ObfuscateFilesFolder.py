import argparse
import os
import subprocess
import internal_utilities
import sys

parser = argparse.ArgumentParser(description='Changes the hash-value of the files in the given folder and renames them to obfuscated names. This script does not process subfolders transitively. Caution: This script can cause harm if you pass a wrong inputfolder-argument.')

parser.add_argument('--printtableheadline', type=internal_utilities.to_boolean, const=True, default=True, nargs='?', help='Prints column-titles in the name-mapping-csv-file')
parser.add_argument('--namemappingfile', default="NameMapping.csv", help = 'Specifies the file where the name-mapping will be written to')
parser.add_argument('inputfolder', help='Specifies the foldere where the files are stored whose names should be obfuscated')

args = parser.parse_args()

d=internal_utilities.normalize_path(args.inputfolder)
namemappingfile=internal_utilities.normalize_path(args.namemappingfile)
if (os.path.isdir(d)):
    for file in internal_utilities.get_files_in_directory(d):
        subprocess.call("python ChangeHashOfProgram.py \"" + file + "\"")
        os.remove(file)
        os.rename(file + ".modified", file)
    subprocess.call("python FilenameObfuscator.py --printtableheadline " + str(internal_utilities.to_boolean(args.printtableheadline)) + " --namemappingfile \"" + namemappingfile + "\" \""+d+"\"")
else:
    print('Directory not found: ' + d)
    sys.exit(2)