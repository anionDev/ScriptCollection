"""
Important hint: This script is not ready for usage yet
"""
import argparse
import os
import subprocess
import utilities
import sys
import shutil
print("Start " + os.path.basename(__file__))
start_directory=os.getcwd()
os.chdir(os.path.dirname(os.path.basename(__file__)))
try:

    parser = argparse.ArgumentParser(description='Compiles a csproj-file. This scripts also download requires nuget-packages.')

    parser.add_argument('--folder_of_csproj_filename', help='Specifies the folder where the csproj-file is located')
    parser.add_argument('--csproj_filename', help='Specifies the csproj-file which should be compiled')
    parser.add_argument('--configuration', help='Specifies the Buildconfiguration (e.g. Debug or Release)')

    args = parser.parse_args()

    output_folder=os.path.abspath(os.path.join(os.path.abspath(args.folder_of_csproj_filename),"bin\\" + args.configuration))
    print(output_folder)
    exitCode=utilities.execute("python", "RestoreNugetPackages.py --inputfolder "+args.folder_of_csproj_filename, os.getcwd())
    if exitCode!=0:
        sys.exit(exitCode)
    if os.path.isdir(output_folder):
        shutil.rmtree(output_folder)
    os.makedirs(output_folder)

    exitCode=utilities.execute("msbuild", args.csproj_filename+" /t:Rebuild /verbosity:normal /p:Configuration="+args.configuration+" /p:Platform=AnyCPU /p:OutputPath="+output_folder, args.folder_of_csproj_filename)
    if exitCode!=0:
        sys.exit(exitCode)

    print("Finished " + os.path.basename(__file__) + " without errors")
    sys.exit(0)

finally:
    os.chdir(start_directory)
