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
    raw_lines=[]
    for line in lines:
     raw_lines.append(line.replace('\r','').replace('\n',''))
    lines=raw_lines
    if len(lines) > 0 and args.ignore_first_line:
        firstLine=lines[0]
        del lines[0]
    if len(lines) > 0 and args.ignore_first_line:
        if args.remove_duplicated_lines:
            lines=remove_duplicates(lines)
        if args.sort:
            lines.sort()
        is_first_line=True
        result=""
        if args.ignore_first_line:
            lines.insert(0, firstLine)
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
