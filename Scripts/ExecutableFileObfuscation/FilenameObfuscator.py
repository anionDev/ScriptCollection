"""
Tested on: Windows
This program comes with absolutely no warranty.
"""
from shutil import copy2
import argparse
import os
import uuid
import pathlib
import sys
import internal_utilities

parser = argparse.ArgumentParser(description='Obfuscates the names of all files in the given folder. Caution: This script can cause harm if you pass a wrong inputfolder-argument.')

parser.add_argument('--printtableheadline', type=internal_utilities.to_boolean, const=True, default=True, nargs='?', help='Prints column-titles in the name-mapping-csv-file')
parser.add_argument('--namemappingfile', default="NameMapping.csv", help = 'Specifies the file where the name-mapping will be written to')
parser.add_argument('inputfolder', help='Specifies the foldere where the files are stored whose names should be obfuscated')

args = parser.parse_args()

d=internal_utilities.normalize_path(args.inputfolder)
namemappingfile=internal_utilities.normalize_path(args.namemappingfile)
if (os.path.isdir(d)):
    printtableheadline=internal_utilities.to_boolean(args.printtableheadline)
    files = []
    if not os.path.isfile(namemappingfile):
        with open(namemappingfile, "a"):
            pass
    with open(namemappingfile, "a") as fileObject:
        pass
    if printtableheadline:
        internal_utilities.append_line_to_file(namemappingfile, "Original filename;new filename;SHA2-hash of file")
    for file in os.listdir(d):
        if os.path.isfile(os.path.join(d, file)):
            files.append(file)
    for file in files:
        full_file_name=os.path.join(d, file)
        hash=internal_utilities.get_sha256_of_file(full_file_name)
        extension=pathlib.Path(file).suffix
        new_file_name=os.path.join(d,str(uuid.uuid4())[0:8] + extension)
        os.rename(full_file_name, new_file_name)
        internal_utilities.append_line_to_file(namemappingfile, full_file_name + ";" + new_file_name + ";" + hash)
else:
    print('Directory not found:' + d)
    sys.exit(2)