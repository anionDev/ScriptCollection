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

    script_folder=f"..{os.path.sep}..{os.path.sep}Miscellaneous"
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
    parser.add_argument('--additional_msbuild_arguments', help='Specifies arbitrary arguments which are passed to msbuild')
    parser.add_argument('--output_directory', help='Specifies output directory for the compiled program')
    parser.add_argument('--folder_for_nuget_restore', help='Specifies folder where nuget should be executed to restore the required nuget-packages')
    parser.add_argument('--msbuild_verbosity', default="normal", help='Specifies verbosity-argument for msbuild')
    parser.add_argument('--clear_output_directory', type=string_to_boolean, nargs='?', const=True, default=False,help='If true then the output directory will be cleared before compiling the program')
    args = parser.parse_args()

    #nuget restore
    execute_and_raise_exception_if_exit_code_is_not_zero("nuget", "restore", args.folder_for_nuget_restore)

    #clear output-directory if desired
    if os.path.isdir(args.output_directory) and args.clear_output_directory:
        shutil.rmtree(args.output_directory)
        os.makedirs(args.output_directory)
    ensure_directory_exists(args.output_directory)

    #run msbuild
    execute_and_raise_exception_if_exit_code_is_not_zero("msbuild", f'{args.csproj_filename} /t:Rebuild /verbosity:{args.msbuild_verbosity} /p:Configuration={args.buildconfiguration} /p:Platform=AnyCPU /p:OutputPath="{args.output_directory}" {str_none_safe(args.additional_msbuild_arguments)}', args.folder_of_csproj_file)
    
except Exception as exception:
    write_exception_to_stderr_with_traceback(exception, traceback)

finally:
    os.chdir(original_directory)
