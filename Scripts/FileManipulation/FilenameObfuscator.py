from shutil import copy2
import argparse

parser = argparse.ArgumentParser(description='Obfuscates the names of all files in the given folder')

parser.add_argument('inputFolder', type=str, help='Specifies the foldere where the files are stored whose names should be obfuscated')
parser.add_argument('--nameMappingFile', type=str, default="NameMapping.txt", help = 'Specifies the file where the name-mapping will be written to')

args = parser.parse_args()

#TODO