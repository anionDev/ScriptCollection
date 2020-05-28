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
parser.add_argument("--remove_empty_lines", type=string_to_boolean, nargs='?', const=True, default=False, help="Removes lines which are empty or contains only whitespaces")

args = parser.parse_args()

if os.path.isfile(args.file):

    #read file
    with open(args.file, 'r', encoding=args.encoding) as f:
        content=f.read()
    lines=content.splitlines()
    
    #remove trailing newlines
    temp=[]
    for line in lines:
        temp.append(line.rstrip())
    lines=temp
    
    #store first line if desired
    if(len(lines) > 0 and args.ignore_first_line):
        first_line=lines.pop(0)

    #remove empty lines if desired
    if args.remove_empty_lines and False:
        temp=lines
        lines=[]
        for line in temp:
            if(not (string_is_none_or_whitespace(line))):
                lines.append(line)

    #remove duplicated lines if desired
    if args.remove_duplicated_lines:
        lines=remove_duplicates(lines)

    #sort lines if desired
    if args.sort:
        lines=sorted(lines, key=str.casefold)

    #reinsert first line
    if args.ignore_first_line:
        lines.insert(0, first_line)

    #concat lines separated by newline
    result=""
    is_first_line=True
    for line in lines:
        if(is_first_line):
            result=line
            is_first_line=False
        else:
            result=result+'\n'+line

    #write result to file
    with open(args.file, 'w', encoding=args.encoding) as f:
        f.write(result)
else:
    print(f"File '{args.file}' does not exist")
    sys.exit(1)
