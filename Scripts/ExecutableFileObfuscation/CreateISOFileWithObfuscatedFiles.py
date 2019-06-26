"""
Tested on: Windows
This program comes with absolutely no warranty.
This program requires pycdlib (you can install pycdlib using 'pip install pycdlib')
"""
import argparse
import os
import subprocess
import shutil
import sys
import internal_utilities
try:
    from cStringIO import StringIO as BytesIO
except ImportError:
    from io import BytesIO
import pycdlib

parser = argparse.ArgumentParser(description='Creates an iso file with the files in the given folder and changes their names and hash-values. This script does not process subfolders transitively.')

parser.add_argument('--outputfile', default="files.iso", help = 'Specifies the output-iso-file and its location')
parser.add_argument('--printtableheadline', type=internal_utilities.to_boolean, const=True, default=True,nargs='?', help='Prints column-titles in the name-mapping-csv-file')
parser.add_argument('inputfolder', help='Specifies the foldere where the files are stored which should be added to the iso-file')

args = parser.parse_args()

d=internal_utilities.normalize_path(args.inputfolder)
outputfile=internal_utilities.normalize_path(args.outputfile)

def create_iso(folder, iso_file):
    files_directory="files"
    iso = pycdlib.PyCdlib()
    iso.new()
    files_directory=files_directory.upper()
    iso.add_directory("/"+files_directory)
    for root, dirs, files in os.walk(folder):
        for file in files:
            fullpath=os.path.join(root, file)
            content=open(fullpath, "rb").read()
            iso.add_fp(BytesIO(content), len(content), '/'+files_directory+'/'+file.upper()+';1')
    iso.write(iso_file)
    iso.close()

if (os.path.isdir(d)):
    namemappingfile="name_map.csv"
    files_directory=args.inputfolder
    if os.path.isfile(namemappingfile):
        os.remove(namemappingfile)
    subprocess.call("python ObfuscateFilesFolder.py --printtableheadline " + str(internal_utilities.to_boolean(args.printtableheadline)) + " --namemappingfile \"" + namemappingfile + "\" \""+files_directory+"\"")
    files_directory=files_directory+"_Obfuscated"
    os.rename(namemappingfile, os.path.join(files_directory,namemappingfile))
    create_iso(files_directory, outputfile)
    shutil.rmtree(files_directory)
else:
    print('Directory not found: ' + d)
    sys.exit(2)