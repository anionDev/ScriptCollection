import os
import sys
import argparse
from Utilities import *

parser = argparse.ArgumentParser(description='Clones a repository if not already done')
parser.add_argument('folder', help='Clone-targetfolder', required=True)
parser.add_argument('link', help='Remote-repository', required=True)
args = parser.parse_args()

ensure_directory_exists(args.folder)
clone_if_not_already_done(args.folder, args.link)
