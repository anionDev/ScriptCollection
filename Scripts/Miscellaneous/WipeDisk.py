"""
Tested on: Not tested yet!
This program comes with absolutely no warranty.
"""
import argparse
import Utilities
import os

parser = argparse.ArgumentParser(description='Wipes free disk-space')

parser.add_argument('diskpath', help='path of the disk which should be wiped')
parser.add_argument('iterations', help='number to indicate how often the disk should be overwritten')

args = parser.parse_args()

Utilities.wipe_disk(args.diskpath, args.iterations)
