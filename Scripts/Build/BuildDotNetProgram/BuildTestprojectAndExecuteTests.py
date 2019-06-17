"""
Important hint: This script is not ready for usage yet
"""
import sys
import argparse
import utilities
import os
import time
print("Start " + os.path.basename(__file__))
start_directory=os.getcwd()
os.chdir(os.path.dirname(os.path.abspath(__file__)))
try:

    parser = argparse.ArgumentParser(description='Downloads missing nuget-packages')

    parser.add_argument('--folder_of_csproj_filename', help='Specifies the folder where the csproj-file is located')
    parser.add_argument('--csproj_filename', help='Specifies the csproj-file which should be compiled')
    parser.add_argument('--configuration', help='Specifies the Buildconfiguration (e.g. Debug or Release)')
    parser.add_argument('--test_dll_file', help='Specifies the Test.dll-file')

    args = parser.parse_args()


    exitCode=utilities.execute("python", "BuildProject.py --folder_of_csproj_filename "+args.folder_of_csproj_filename+" --csproj_filename "+args.csproj_filename+" --configuration " + args.configuration, os.getcwd())
    if exitCode!=0:
        sys.exit(exitCode)

    output_folder=os.path.abspath(args.folder_of_csproj_filename)+"\\bin\\" + args.configuration

    exitCode=utilities.execute("vstest.console.exe", args.test_dll_file, output_folder)
    if exitCode!=0:
        sys.exit(exitCode)

    print("Finished " + os.path.basename(__file__) + " without errors")
    sys.exit(0)

finally:
    os.chdir(start_directory)
