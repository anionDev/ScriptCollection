"""
Important hint: This script removes the (usually untracked) outputfolder (e.g. Debug or Release). Please make a backup of this folder before executing this script if you do not want to loose its current content.
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
    parser.add_argument('--additional_msbuild_arguments', nargs='?', const=" ", help='Specifies arbitrary arguments which are passed to msbuild')
    parser.add_argument('--additional_vstest_arguments', nargs='?', const=" ", help='Specifies arbitrary arguments which are passed to vstest')

    args = parser.parse_args()

    exit_code=utilities.execute("python", "BuildProject.py --folder_of_csproj_filename "+args.folder_of_csproj_filename+" --csproj_filename "+args.csproj_filename+" --configuration " + args.configuration+" --additional_msbuild_arguments "+utilities.str_none_safe(args.additional_msbuild_arguments), os.getcwd())
    if exit_code!=0:
        sys.exit(exit_code)

    exit_code=utilities.execute("vstest.console.exe", args.test_dll_file+" "+additional_vstest_arguments, os.path.dirname(args.test_dll_file))
    if exit_code!=0:
        sys.exit(exit_code)

    print("Finished " + os.path.basename(__file__) + " without errors")
    sys.exit(0)

finally:
    os.chdir(start_directory)
