import argparse
import os
import subprocess
import shutil
from pathlib import Path

parser = argparse.ArgumentParser(description='Creates an iso file with the files in the given folder and changes their names and hash-values.')

parser.add_argument('inputFolder', type=str, help='Specifies the foldere where the files are stored which should be added to the iso-file')
parser.add_argument('--outputFile', type=str, default="files.iso", help = 'Specifies the output-iso-file and its location')
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

def delete_directory_and_its_content(directory:str):
    pth=Path(directory)
    for sub in pth.iterdir() :
        if sub.is_dir() :
            delete_folder(sub)
        else :
            sub.unlink()
    pth.rmdir()

directory=os.fsdecode(os.fsencode(args.inputFolder))
if (os.path.isdir(directory)):
    temp_directory=directory+"_temp"
    if os.path.isdir(temp_directory):
        delete_directory_and_its_content(temp_directory)
    os.makedirs(temp_directory)
    if os.path.isfile(args.nameMappingFile):
        os.remove(args.nameMappingFile)
    for file in get_files_in_directory(directory):
        shutil.copy2(file, temp_directory)
    subprocess.call(["python", "ObfuscateFilesFolder.py", "--printTableHeadline=" + str(args.printTableHeadline) + " --nameMappingFile='" + args.nameMappingFile + "'", temp_directory])
    shutil.move(args.nameMappingFile, temp_directory)
    #TODO
else:
    print('Directory not found: ' + directory)
    sys.exit(2)