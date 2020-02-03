"""
Tested on: Windows
This program comes with absolutely no warranty.
"""
import argparse
from Utilities import *
import uuid

parser = argparse.ArgumentParser(description='Generate multiple .snk-files')
parser.add_argument('outputfolder', help='Folder where the files are stored which should be hashed')
parser.add_argument('--keysize', default='4096')
parser.add_argument('--amountofkeys', default='10')

args = parser.parse_args()

ensure_directory_exists(args.outputfolder)
for number in range(int(args.amountofkeys)):
    file=os.path.join(args.outputfolder,str(uuid.uuid4())+".snk")
    argument=f"-k {args.keysize} {file}"
    execute("sn", argument, args.outputfolder)
