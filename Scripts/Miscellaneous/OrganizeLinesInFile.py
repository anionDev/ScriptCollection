"""
Tested on: Windows
This program comes with absolutely no warranty.
"""
import argparse
import os
import sys
from Utilities import *

parser = argparse.ArgumentParser(description='Processes the lines of a file with the given commands')

parser.add_argument('file', help='File which should be transformed')
parser.add_argument('--encoding', default="utf-8", help='Encoding for the file which should be transformed')
parser.add_argument("--sort", type=string_to_boolean, nargs='?', const=True, default=False, help="Sort lines")
parser.add_argument("--remove_duplicated_lines", type=string_to_boolean, nargs='?', const=True, default=False, help="Remove duplicate lines")

args = parser.parse_args()

if os.path.isfile(args.file):
    with open(args.file, 'r', encoding=args.encoding) as f:
        lines=f.readlines()
    if args.remove_duplicated_lines:
        lines.sort()
    if args.sort:
        lines=remove_duplicates(lines)
    with open(args.file, 'w', encoding=args.encoding) as f:
        for line in lines:
            f.write("%s\n" % line)
else:
    print(f"File '{args.file}' does not exist")
    sys.exit(1)
