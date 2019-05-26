from shutil import copy2
import argparse

parser = argparse.ArgumentParser(description='Changes the hash-value of arbitrary files by appending data at the end of the file.')

parser.add_argument('inputFile', type=str, help='Specifies the script/executable-file whose hash-value should be changed')
parser.add_argument('--valueToAppend', type=str, default=" ", help = 'Specifies the string which should be appended to the file. The default-value is one whitespace')
parser.add_argument('--outputFile', type=str, default="", help = 'Specifies the outputfile and its location')

args = parser.parse_args()

inputFile = args.inputFile.replace("\"","")
valueToAppend= args.valueToAppend
outputFile = args.outputFile

if(outputFile==""):
    outputFile=inputFile+'.modified'

copy2(inputFile, outputFile)
file = open(outputFile, 'a')
file.write(valueToAppend)
file.close()
