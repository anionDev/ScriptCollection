"""
Important hint: This script removes the (usually untracked) outputfolder (e.g. bin\debug or \bin\release). Please make a backup of this folder before executing this script if you do not want to loose its current content.
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

    import argparse
    import time
    from distutils.dir_util import copy_tree
    parser = argparse.ArgumentParser(description='Builds a program using msbuild and execute the defined testcases')

    #parameter for project
    parser.add_argument('--folder_of_csproj_file', help='Specifies the folder where the csproj-file is located')
    parser.add_argument('--csproj_filename', help='Specifies the csproj-file-name which should be compiled')
    parser.add_argument('--publish_directory', help='Specifies release-target-directory for the compiled program when the compile-process was successful.')
    parser.add_argument('--output_directory', help='Specifies output directory for the compiled program')
   
    #parameter for testproject 
    parser.add_argument('--folder_of_test_csproj_file', help='Specifies the folder where the test-csproj-file is located')
    parser.add_argument('--test_csproj_filename', help='Specifies the test-csproj-file-name which should be compiled')
    parser.add_argument('--test_dll_filename', help='Specifies the resulting Test.dll-file')
    parser.add_argument('--test_output_directory', help='Specifies output directory for the compiled test-dll')
    parser.add_argument('--additional_vstest_arguments', default="", help='Specifies arbitrary arguments which are passed to vstest')
    
    #parameter for project and testproject
    parser.add_argument('--buildconfiguration', help='Specifies the Buildconfiguration (e.g. Debug or Release)')
    parser.add_argument('--folder_for_nuget_restore', help='Specifies folder where nuget should be executed to restore the required nuget-packages')
    parser.add_argument('--additional_msbuild_arguments', default="", help='Specifies arbitrary arguments which are passed to msbuild')
    parser.add_argument('--msbuild_verbosity', default="normal", help='Specifies verbosity-argument for msbuild')
    parser.add_argument('--clear_output_directory', type = string_to_boolean, nargs = '?', const = True, default = False, help='If true then the output directory will be cleared before compiling the program')
    
    args = parser.parse_args()

    write_message_to_stdout("arguments:")    
    write_message_to_stdout("folder_of_csproj_file:"+args.folder_of_csproj_file)
    write_message_to_stdout("csproj_filename:"+args.csproj_filename)
    write_message_to_stdout("output_directory:"+args.output_directory)
    write_message_to_stdout("test_output_directory:"+args.test_output_directory)
    write_message_to_stdout("folder_of_test_csproj_file:"+args.folder_of_test_csproj_file)
    write_message_to_stdout("test_csproj_filename:"+args.test_csproj_filename)
    write_message_to_stdout("test_dll_filename:"+args.test_dll_filename)
    write_message_to_stdout("additional_vstest_arguments:"+args.additional_vstest_arguments)
    write_message_to_stdout("buildconfiguration:"+args.buildconfiguration)
    write_message_to_stdout("folder_for_nuget_restore:"+args.folder_for_nuget_restore)
    write_message_to_stdout("additional_msbuild_arguments:"+args.additional_msbuild_arguments)
    write_message_to_stdout("msbuild_verbosity:"+args.msbuild_verbosity)
    write_message_to_stdout("clear_output_directory:"+str(args.clear_output_directory))

    #build project
    argument=""
    argument=argument+" --folder_of_csproj_file "+args.folder_of_csproj_file
    argument=argument+" --csproj_filename "+args.csproj_filename
    argument=argument+" --buildconfiguration "+args.buildconfiguration
    argument=argument+" --additional_msbuild_arguments "+f'"{str_none_safe(args.additional_msbuild_arguments)}"'
    argument=argument+" --output_directory "+args.output_directory
    argument=argument+" --folder_for_nuget_restore "+args.folder_for_nuget_restore
    argument=argument+" --msbuild_verbosity "+args.msbuild_verbosity
    argument=argument+" --clear_output_directory "+str_none_safe(args.clear_output_directory)
    execute_and_raise_exception_if_exit_code_is_not_zero("python", current_directory+os.path.sep+"BuildProject.py "+argument,"", 120,  True,False, "Build project")
    
    #build testproject
    argument=""
    argument=argument+" --folder_of_csproj_file "+args.folder_of_test_csproj_file
    argument=argument+" --csproj_filename "+args.test_csproj_filename
    argument=argument+" --buildconfiguration "+args.buildconfiguration
    argument=argument+" --additional_msbuild_arguments "+f'"{str_none_safe(args.additional_msbuild_arguments)}"'
    argument=argument+" --output_directory "+args.test_output_directory
    argument=argument+" --folder_for_nuget_restore "+args.folder_for_nuget_restore
    argument=argument+" --msbuild_verbosity "+args.msbuild_verbosity
    argument=argument+" --clear_output_directory "+str_none_safe(args.clear_output_directory)
    execute_and_raise_exception_if_exit_code_is_not_zero("python", current_directory+os.path.sep+"BuildProject.py "+argument,"", 120,  True,False, "Build testproject")
    
    #execute testcases
    execute_and_raise_exception_if_exit_code_is_not_zero("vstest.console", args.test_dll_filename+" "+str_none_safe(args.additional_vstest_arguments), args.test_output_directory, 120, True,False, "vstest.console")

    #export program
    ensure_directory_exists(args.publish_directory)
    copy_tree(args.output_directory, args.publish_directory)

finally:
    os.chdir(original_directory)
