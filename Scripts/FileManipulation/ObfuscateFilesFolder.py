import argparse
import os
import subprocess

parser = argparse.ArgumentParser(description='Changes the hash-value of the files in the given folder and renames them to obfuscated names. This script does not process subfolders transitively. Caution: This script can cause harm if you pass a wrong inputFolder-argument.')

parser.add_argument('inputFolder', type=str, help='Specifies the foldere where the files are stored whose names should be obfuscated')

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
    subprocess.call(["python", "FilenameObfuscator.py ", directory])
else:
    print('Directory not found: ' + directory)
    sys.exit(2)