"""
Tested on: Windows
This program comes with absolutely no warranty.
"""
from shutil import copy2
import argparse
import internal_utilities

parser = argparse.ArgumentParser(description='Changes the hash-value of arbitrary files by appending data at the end of the file.')

parser.add_argument('--valuetoappend', default=" ", help = 'Specifies the string which should be appended to the file. The default-value is one whitespace')
parser.add_argument('--outputfile', default="", help = 'Specifies the outputfile and its location')
parser.add_argument('inputfile', help='Specifies the script/executable-file whose hash-value should be changed')

args = parser.parse_args()

inputfile = internal_utilities.normalize_path(args.inputfile)
valuetoappend = args.valuetoappend
outputfile = args.outputfile

if(outputfile==""):
    outputfile=inputfile + '.modified'

copy2(inputfile, outputfile)
file = open(outputfile, 'a')
#TODO use rcedit for .exe-files instead of appending valuetoappend ( https://github.com/electron/rcedit/ )
#background: you can retrieve the "original-filename" from the .exe-file like discussed here: https://security.stackexchange.com/questions/210843/is-it-possible-to-change-original-filename-of-an-exe
#so removing the original filename with rcedit is probably a better way to make it more difficult to detect the programname.
#this would obviously also change the hashvalue of the program so appending a whitespace is not required anymore.
file.write(valuetoappend)
file.close()
