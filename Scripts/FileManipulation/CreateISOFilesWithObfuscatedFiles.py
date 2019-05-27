import argparse
import os
import subprocess

parser = argparse.ArgumentParser(description='Creates an iso file with the files in the given folder and changes their names and hash-values.')

parser.add_argument('inputFolder', type=str, help='Specifies the foldere where the files are stored which should be added to the iso-file')
parser.add_argument('--outputFile', type=str, default="files.iso", help = 'Specifies the output-iso-file and its location')

args = parser.parse_args()

directory=os.fsdecode(os.fsencode(args.inputFolder))
if (os.path.isdir(directory)):
    pass#TODO
else:
    print('Directory not found: ' + directory)
    sys.exit(2)