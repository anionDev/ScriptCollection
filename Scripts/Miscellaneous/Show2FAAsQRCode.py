"""
Tested on: Windows
This program comes with absolutely no warranty.
Requirements: qrcode (To generate a qr-code. Can be installed by "pip install qrcode".)
Description:
Always when you use 2-factor-authentication you have the problem: Where to backup the secret-key so that it is easy to re-setup them when you have a new phone?
Using this script is a solution. Always when you setup a 2fa you copy and store the secret in a csv-file.
It should be obviously that this csv-file must be stored encrypted!
Now if you want to move your 2fa-codes to a new phone you simply call
python Show2FAAsQRCode.py 2FA.csv
Then the qr-codes will be displayed in the console and you can scan them on your new phone.
This script does not saving the any data anywhere.

The structure of the csv-file can be viewd here:
Website;Email-address;Displayname;Secret;Period;
Amazon.de;myemailaddress@example.com;Amazon;QWERTY;30;
Google.de;myemailaddress@example.com;Google;ASDFGH;30;

Hints:
-Since the first line of the csv-file contains headlines the first line will always be ignored
-30 is the commonly used value for the period
"""
import argparse
import subprocess
from Utilities import *

parser = argparse.ArgumentParser(description='Generates qr-codes of 2fa-codes.')
parser.add_argument('csvfile', help='File where the 2fa-codes are stored')
args = parser.parse_args()

with open(args.csvfile) as f:
    lines = f.readlines()
lines = [line.rstrip('\n') for line in lines]
def print_qr_code_by_csv_line(line:str):
    splitted=line.split(";")
    website=splitted[0]
    emailaddress=splitted[1]
    displayname=splitted[2]
    key=splitted[3]    
    period=splitted[4]
    qrcode_content=f"otpauth://totp/{website}:{emailaddress}?secret={key}&issuer={displayname}&period={period}"
    print(f"{displayname} ({emailaddress}):")
    print(qrcode_content)
    subprocess.call(["qr", qrcode_content])
def print_line():
    print("--------------------------------------------------------")
itertor = iter(lines)
next(itertor)
for line in itertor:
    print_line()
    print_qr_code_by_csv_line(line)
print_line()