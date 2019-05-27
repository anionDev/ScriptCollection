import argparse
import os
import subprocess

parser = argparse.ArgumentParser(description='Changes the hash-value of the files in the given folder and renames them to obfuscated names. This script does not process subfolders transitively. Caution: This script can cause harm if you pass a wrong inputFolder-argument.')

parser.add_argument('inputFolder', type=str, help='Specifies the foldere where the files are stored whose names should be obfuscated')
parser.add_argument('--printTableHeadline', default = True, help='Prints column-titles in the name-mapping-csv-file')
parser.add_argument('--nameMappingFile', type=str, default="NameMapping.csv", help = 'Specifies the file where the name-mapping will be written to')

args = parser.parse_args()

def get_files_in_directory(directory):
    files = []
    for file in os.listdir(directory):
        file_with_directory=os.path.join(directory, file)
        if os.path.isfile(file_with_directory):
            files.append(file_with_directory)
    return files

directory=os.fsdecode(os.fsencode(args.inputFolder))
if (os.path.isdir(directory)):
    for file in get_files_in_directory(directory):
        subprocess.call(["python", "ChangeHashOfProgram.py ", file])
        os.remove(file)
        os.rename(file + ".modified", file)
    subprocess.call(["python", "FilenameObfuscator.py", "--printTableHeadline=" + str(args.printTableHeadline) + " --nameMappingFile='" + args.nameMappingFile + "'", directory])
    
else:
    print('Directory not found: ' + directory)
    sys.exit(2)