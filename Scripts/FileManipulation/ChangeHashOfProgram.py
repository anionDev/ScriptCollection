from shutil import copy2
import argparse
import internal_utilities

parser = argparse.ArgumentParser(description='Changes the hash-value of arbitrary files by appending data at the end of the file.')

parser.add_argument('--valuetoappend', default=" ", help = 'Specifies the string which should be appended to the file. The default-value is one whitespace')
parser.add_argument('--outputfile', default="", help = 'Specifies the outputfile and its location')
parser.add_argument('inputfile', help='Specifies the script/executable-file whose hash-value should be changed')

args = parser.parse_args()

inputfile = normalize_path(args.inputfile)
valuetoappend= args.valuetoappend
outputfile = args.outputfile

if(outputfile==""):
    outputfile=inputfile + '.modified'

copy2(inputfile, outputfile)
file = open(outputfile, 'a')
file.write(valuetoappend)
file.close()
