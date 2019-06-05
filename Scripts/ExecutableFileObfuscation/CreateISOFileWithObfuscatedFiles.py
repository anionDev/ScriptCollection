"""
Tested on: Windows
This program comes with absolutely no warranty.
"""
import argparse
import os
import subprocess
import shutil
import internal_utilities
import sys

parser = argparse.ArgumentParser(description='Creates an iso file with the files in the given folder and changes their names and hash-values. This script does not process subfolders transitively.')

parser.add_argument('--outputfile', default="files.iso", help = 'Specifies the output-iso-file and its location')
parser.add_argument('--printtableheadline', type=internal_utilities.to_boolean, const=True, default=True,nargs='?', help='Prints column-titles in the name-mapping-csv-file')
parser.add_argument('--namemappingfile', default="NameMapping.csv", help = 'Specifies the file where the name-mapping will be written to')
parser.add_argument('inputfolder', help='Specifies the foldere where the files are stored which should be added to the iso-file')

args = parser.parse_args()


d=internal_utilities.normalize_path(args.inputfolder)
namemappingfile=internal_utilities.normalize_path(args.namemappingfile)
outputfile=internal_utilities.normalize_path(args.outputfile)
if (os.path.isdir(d)):
    files_directory= "files"
    if os.path.isdir(files_directory):
        internal_utilities.delete_directory_and_its_content(files_directory)
    internal_utilities.create_directory_transitively(files_directory)
    if os.path.isfile(namemappingfile):
        os.remove(namemappingfile)
    for file in internal_utilities.get_files_in_directory(d):
        shutil.copy2(file, files_directory)
    subprocess.call("python ObfuscateFilesFolder.py --printtableheadline " + str(internal_utilities.to_boolean(args.printtableheadline)) + " --namemappingfile \"" + namemappingfile + "\" \""+files_directory+"\"")
    os.rename(namemappingfile, os.path.join(files_directory, os.path.basename(namemappingfile)))
    iso_directory= "iso_content"
    if os.path.isdir(iso_directory):
        internal_utilities.delete_directory_and_its_content(iso_directory)
    internal_utilities.create_directory_transitively(iso_directory)
    os.rename(files_directory, os.path.join(iso_directory, files_directory))
    #TODO create iso with content of iso_directory
    #TODO delete iso_directory
else:
    print('Directory not found: ' + d)
    sys.exit(2)