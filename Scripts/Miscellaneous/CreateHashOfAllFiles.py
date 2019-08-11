"""
Tested on: Windows
This program comes with absolutely no warranty.
"""
import argparse
from Utilities import *

parser = argparse.ArgumentParser(description='Calculates the SHA-256-value of all files in the given folder and stores the hash-value in a file next to the hashed file.')

parser.add_argument('folder', help='Folder where the files are stored which should be hashed')

args = parser.parse_args()

for file in absolute_file_paths(args.folder):
    with open(file+".sha256","w+") as f:
        f.write(get_sha256_of_file(file))
