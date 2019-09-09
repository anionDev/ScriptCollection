import os
import sys
import argparse
parser = argparse.ArgumentParser(description='Creates a file with a specific size')
parser.add_argument('name', help='Specifies the name of the created file')
parser.add_argument('size', help='Specifies the size of the created size.')

args = parser.parse_args()
size_string=args.size.lower()
if size_string.isdigit():
    size=int(size_string)
else:
    if len(size_string)>=3:
        if(size_string.endswith("kb")):
            size=int(size_string[:-2]) * pow(10, 3)
        elif(size_string.endswith("mb")):
            size=int(size_string[:-2]) * pow(10, 6)
        elif(size_string.endswith("gb")):
            size=int(size_string[:-2]) * pow(10, 9)
        elif(size_string.endswith("kib")):
            size=int(size_string[:-3]) * pow(2, 10)
        elif(size_string.endswith("mib")):
            size=int(size_string[:-3]) * pow(2, 20)
        elif(size_string.endswith("gib")):
            size=int(size_string[:-3]) * pow(2, 30)
        else:
            print("Wrong format")
    else:
        print("Wrong format")
        sys.exit(1)
with open(args.name, "wb") as f:
    f.seek(size-1)
    f.write(b"\0")
sys.exit(0)