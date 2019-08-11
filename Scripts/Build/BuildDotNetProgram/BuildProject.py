"""
Important hint: This script removes the (usually untracked) outputfolder (e.g. Debug or Release). Please make a backup of this folder before executing this script if you do not want to loose its current content.
An example how to use this file can be found here: https://github.com/anionDev/gryLibrary/blob/development/Scripts/Build.py
"""
import argparse
import os
import utilities
import sys
import shutil
print("Start " + os.path.basename(__file__))
start_directory=os.getcwd()
os.chdir(os.path.dirname(os.path.abspath(__file__)))
try:

    parser = argparse.ArgumentParser(description='Compiles a csproj-file. This scripts also download required nuget-packages.')

    parser.add_argument('--folder_of_csproj_filename', help='Specifies the folder where the csproj-file is located')
    parser.add_argument('--csproj_filename', help='Specifies the csproj-file which should be compiled')
    parser.add_argument('--configuration', help='Specifies the Buildconfiguration (e.g. Debug or Release)')
    parser.add_argument('--additional_msbuild_arguments', nargs='?', const=" ", help='Specifies arbitrary arguments which are passed to msbuild')

    args = parser.parse_args()

    output_folder=os.path.abspath(os.path.join(os.path.abspath(args.folder_of_csproj_filename),"bin\\" + args.configuration))
    exit_code=utilities.execute("python", "RestoreNugetPackages.py --inputfolder "+args.folder_of_csproj_filename, os.getcwd())
    if exit_code!=0:
        sys.exit(exit_code)
    if os.path.isdir(output_folder):
        shutil.rmtree(output_folder)
    os.makedirs(output_folder)

    exit_code=utilities.execute("msbuild", args.csproj_filename+" /t:Rebuild /verbosity:normal /p:Configuration="+args.configuration+" /p:Platform=AnyCPU /p:OutputPath="+output_folder+" "+utilities.str_none_safe(args.additional_msbuild_arguments), args.folder_of_csproj_filename)
    if exit_code!=0:
        sys.exit(exit_code)

    print("Finished " + os.path.basename(__file__) + " without errors")
    sys.exit(0)

finally:
    os.chdir(start_directory)
