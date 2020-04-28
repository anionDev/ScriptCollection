"""
Important hint: This script removes the (usually untracked) outputfolder (e.g. Debug or Release). Please make a backup of this folder before executing this script if you do not want to loose its current content.
An example how to use this file can be found here: https://github.com/anionDev/gryLibrary/blob/development/Scripts/Build.py
"""
import os
import sys
import traceback
from os.path import abspath
original_directory=os.getcwd()
current_directory = os.path.dirname(os.path.abspath(__file__))
os.chdir(current_directory)

try:

    script_folder=f"..{os.path.sep}..{os.path.sep}..{os.path.sep}Miscellaneous"
    sys.path.append(abspath(os.path.join(current_directory,f"{script_folder}")))
    from Utilities import *
    write_message_to_stdout("Start " + os.path.basename(__file__))

    start_directory=os.getcwd()
    os.chdir(os.path.dirname(os.path.abspath(__file__)))

    import argparse
    import shutil
    parser = argparse.ArgumentParser(description='Compiles a csproj-file. This scripts also download required nuget-packages.')
    parser.add_argument('--folder_of_csproj_file', help='Specifies the folder where the csproj-file is located')
    parser.add_argument('--csproj_filename', help='Specifies the csproj-file which should be compiled')
    parser.add_argument('--buildconfiguration', help='Specifies the Buildconfiguration (e.g. Debug or Release)')
    parser.add_argument('--additional_build_arguments', help='Specifies arbitrary arguments which are passed to the build-process')
    parser.add_argument('--output_directory', help='Specifies output directory for the compiled program')
    parser.add_argument('--folder_for_nuget_restore', help='Specifies folder where nuget should be executed to restore the required nuget-packages')
    parser.add_argument('--clear_output_directory', type=string_to_boolean, nargs='?', const=True, default=False,help='If true then the output directory will be cleared before compiling the program')
    parser.add_argument('--runtimeid', default="win10-x64", help='Specifies runtime-id-argument for build-process')
    parser.add_argument('--verbosity', default="minimal", help='Specifies verbosity for build-process')
    parser.add_argument('--framework', default="netcoreapp3.1", help='Specifies targetframework')
    
    args = parser.parse_args()

    #clear output-directory if desired
    if os.path.isdir(args.output_directory) and args.clear_output_directory:
        shutil.rmtree(args.output_directory)
    ensure_directory_exists(args.output_directory)

    argument = f'"{args.csproj_filename}"'
    argument = argument + f' --no-incremental'
    argument = argument + f' --verbosity {args.verbosity}'
    argument = argument + f' --configuration {args.buildconfiguration}'
    argument = argument + f' --framework {args.framework}'
    argument = argument + f' --runtime {args.runtimeid}'
    if not string_is_none_or_whitespace(args.output_directory):
        argument = argument + f' --output "{args.output_directory}"'
    argument = argument + f' {args.additional_build_arguments}'

    #run dotnet build
    execute_and_raise_exception_if_exit_code_is_not_zero("dotnet", f'build {argument}', args.folder_of_csproj_file, 120,  True, False, "Build")

finally:
    os.chdir(original_directory)
