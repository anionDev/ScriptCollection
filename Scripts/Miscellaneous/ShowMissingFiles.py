"""
Tested on: Windows
This program comes with absolutely no warranty.
"""
import argparse
import Utilities
import os

parser = argparse.ArgumentParser(description='Shows all files which are in folderA but not in folder B. This program does not do any content-comparisons.')

parser.add_argument('folderA')
parser.add_argument('folderB')

args = parser.parse_args()
folderA=args.folderA
folderB=args.folderB
folderA_length=len(folderA)
for fileA in Utilities.absolute_file_paths(folderA):
    file=fileA[folderA_length:]
    fileB=folderB+file
    if not os.path.isfile(fileB):
        print(fileB)
