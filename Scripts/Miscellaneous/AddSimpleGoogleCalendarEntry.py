"""
Requirements:
- Google calendar API must obviously be enabled
- The pip packages google-api-python-client, google-auth-httplib2 and google-auth-oauthlib must be installed
"""
import argparse
import shutil
import os
import sys
import io
sys.path.append("Miscellaneous")
from Utilities import *

parser = argparse.ArgumentParser(description='Adds a new appointment to a google-calendar')
parser.add_argument('appointmentname', help='Represents the title of the appointment')
parser.add_argument('begindate',help='Represents the begin-date of the appointment as ISO-8601-string')
parser.add_argument('enddate', help='Represents the end-date of the appointment as ISO-8601-string')
parser.add_argument('location', help='Represents the location of the appointment')
parser.add_argument('apikey', help='The API-key is required to get access to the google-API. To find out how an API-key can be generated visit https://docs.simplecalendar.io/google-api-key')
parser.add_argument('calendar', help='Name of the calendar where the appointment should be inserted')
args = parser.parse_args()

#TODO

