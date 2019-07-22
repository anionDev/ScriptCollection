"""
Tested on: Windows
This program comes with absolutely no warranty.
"""
import argparse
import os
import subprocess
import internal_utilities
import sys
import shutil

parser = argparse.ArgumentParser(description='Changes the hash-value of the files in the given folder and renames them to obfuscated names. This script does not process subfolders transitively. Caution: This script can cause harm if you pass a wrong inputfolder-argument.')

parser.add_argument('--printtableheadline', type=internal_utilities.to_boolean, const=True, default=True, nargs='?', help='Prints column-titles in the name-mapping-csv-file')
parser.add_argument('--namemappingfile', default="NameMapping.csv", help = 'Specifies the file where the name-mapping will be written to')
parser.add_argument('--extensions', default="exe,py,sh", help = 'Comma-separated list of file-extensions of files where this tool should be applied. Use "*" to obfuscate all')
parser.add_argument('inputfolder', help='Specifies the folder where the files are stored whose names should be obfuscated')

args = parser.parse_args()

def extension_matchs(file:str,obfuscate_file_extensions):
    for extension in obfuscate_file_extensions:
        if file.lower().endswith("."+extension.lower()):
            return True
    return False

obfuscate_all_files=args.extensions=="*"
if(not obfuscate_all_files):
    if "," in args.extensions:
	    obfuscate_file_extensions=args.extensions.split(",")
    else:
        obfuscate_file_extensions=[args.extensions]
d=internal_utilities.normalize_path(args.inputfolder)
newd=d+"_Obfuscated"
if os.path.isdir(newd):
    shutil.rmtree(newd)
shutil.copytree(d, newd)
d=newd
namemappingfile=internal_utilities.normalize_path(args.namemappingfile)
if (os.path.isdir(d)):
    for file in internal_utilities.absolute_file_paths(d):
        if obfuscate_all_files or extension_matchs(file,obfuscate_file_extensions):
            subprocess.call("python ChangeHashOfProgram.py \"" + file + "\"")
            os.remove(file)
            os.rename(file + ".modified", file)
    subprocess.call("python FilenameObfuscator.py --printtableheadline " + str(internal_utilities.to_boolean(args.printtableheadline)) + " --namemappingfile \"" + namemappingfile + "\" --extensions "+args.extensions+ " "+d+"\"")
else:
    print('Directory not found: ' + d)
    sys.exit(2)