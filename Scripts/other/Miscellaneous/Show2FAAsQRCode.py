"""
Tested on: Windows
This program comes with absolutely no warranty.
Requirements: qrcode (To generate a qr-code. Can be installed by "pip install qrcode".)
Description:

import argparse
import subprocess
from Utilities import *

parser = argparse.ArgumentParser(description='Generates qr-codes of 2fa-codes.')
parser.add_argument('csvfile', help='File where the 2fa-codes are stored')
args = parser.parse_args()

