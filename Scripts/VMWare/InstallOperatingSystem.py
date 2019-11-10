"""
Tested on: Windows
This program comes with absolutely no warranty.
"""
import argparse
import shutil
import os
import sys
sys.path.append(f"..{os.path.sep}Miscellaneous")
from Utilities import *

parser = argparse.ArgumentParser(description='Installs an operating system on a virtual machine')
parser.add_argument('vmx_file', type=str,help='virtual machine')
parser.add_argument('installimage',type=str,help='Imagefile which should be installed on the vm')
args = parser.parse_args()

#todo