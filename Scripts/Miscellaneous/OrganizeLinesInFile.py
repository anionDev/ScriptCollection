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
parser.add_argument("--ignore_first_line", type=string_to_boolean, nargs='?', const=True, default=False, help="Ignores the first line in the file")

args = parser.parse_args()

if os.path.isfile(args.file):
    with open(args.file, 'r', encoding=args.encoding) as f:
        content=f.read()
    lines=content.splitlines()
    if(args.ignore_first_line):
        del l[lines]
    x=[]
    for line in lines:
     x.append(line.replace('\r','').replace('\n',''))
    lines=x
    if args.remove_duplicated_lines:
        lines.sort()
    if args.sort:
        lines=remove_duplicates(lines)
    is_first_line=True
    result=""
    for line in lines:
        if(is_first_line):
            is_first_line=False
        else:
            result=result+"\n"
        result=result+line
    with open(args.file, 'w', encoding=args.encoding) as f:
        f.write(result)
else:
    print(f"File '{args.file}' does not exist")
    sys.exit(1)
