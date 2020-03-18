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

    script_folder=f"..{os.path.sep}..{os.path.sep}..{os.path.sep}Miscellaneous"
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
    parser.add_argument('--clear_publish_directory', type = string_to_boolean, nargs = '?', const = True, default = False, help='If true then the publish directory will be cleared before compiling the program')
    parser.add_argument('--output_directory', help='Specifies output directory for the compiled program')
    parser.add_argument('--runtimeid', default="win10-x64", help='Specifies runtime-id-argument for build-process')
    parser.add_argument('--framework', default="netstandard2.1", help='Specifies targetframework')
    parser.add_argument('--publish_coverage', type = string_to_boolean, nargs = '?', const = True, default = False, help='Specifies whether the testcoverage-result should be copied to the publish-directory')

    #parameter for testproject 
    parser.add_argument('--folder_of_test_csproj_file', help='Specifies the folder where the test-csproj-file is located')
    parser.add_argument('--test_csproj_filename', help='Specifies the test-csproj-file-name which should be compiled')
    parser.add_argument('--test_output_directory', help='Specifies output directory for the compiled test-dll')
    parser.add_argument('--additional_test_arguments', default="", help='Specifies arbitrary arguments which are passed to vstest')
    parser.add_argument('--test_runtimeid', default="win10-x64", help='Specifies runtime-id-argument for build-process of the testproject')
    parser.add_argument('--test_framework', default="netcoreapp3.1", help='Specifies targetframework of the testproject')
    parser.add_argument('--code_coverage_folder', help='Specifies the folder for the code-coverage-file')
   
    #parameter for build project and testproject
    parser.add_argument('--buildconfiguration', help='Specifies the Buildconfiguration (e.g. Debug or Release)')
    parser.add_argument('--folder_for_nuget_restore', help='Specifies folder where nuget should be executed to restore the required nuget-packages')
    parser.add_argument('--additional_build_arguments', default="", help='Specifies arbitrary arguments which are passed to msbuild')
    parser.add_argument('--clear_output_directory', type = string_to_boolean, nargs = '?', const = True, default = False, help='If true then the output directory will be cleared before compiling the program')
    parser.add_argument('--verbosity', default="minimal", help='Specifies verbosity for build-process')
    parser.add_argument('--productname', help='Specifies the name of the product')
    
    args = parser.parse_args()

    write_message_to_stdout("arguments:")    
    write_message_to_stdout("folder_of_csproj_file:"+args.folder_of_csproj_file)
    write_message_to_stdout("csproj_filename:"+args.csproj_filename)
    write_message_to_stdout("publish_directory:"+args.publish_directory)
    write_message_to_stdout("clear_publish_directory:"+str(args.clear_publish_directory))
    write_message_to_stdout("output_directory:"+args.output_directory)
    write_message_to_stdout("folder_of_test_csproj_file:"+args.folder_of_test_csproj_file)
    write_message_to_stdout("test_csproj_filename:"+args.test_csproj_filename)
    write_message_to_stdout("additional_test_arguments:"+args.additional_test_arguments)
    write_message_to_stdout("buildconfiguration:"+args.buildconfiguration)
    write_message_to_stdout("folder_for_nuget_restore:"+args.folder_for_nuget_restore)
    write_message_to_stdout("additional_build_arguments:"+args.additional_build_arguments)
    write_message_to_stdout("clear_output_directory:"+str(args.clear_output_directory))
    write_message_to_stdout("code_coverage_folder:"+str(args.code_coverage_folder))
    write_message_to_stdout("publish_coverage:"+str(args.publish_coverage))

    #build project
    argument=""
    argument=argument+" --folder_of_csproj_file "+args.folder_of_csproj_file
    argument=argument+" --csproj_filename "+args.csproj_filename
    argument=argument+" --buildconfiguration "+args.buildconfiguration
    argument=argument+" --additional_build_arguments "+f'"{str_none_safe(args.additional_build_arguments)}"'
    argument=argument+" --output_directory "+args.output_directory
    argument=argument+" --folder_for_nuget_restore "+args.folder_for_nuget_restore
    argument=argument+" --clear_output_directory "+str_none_safe(args.clear_output_directory)
    argument=argument+" --runtimeid "+args.runtimeid
    argument=argument+" --verbosity "+args.verbosity
    argument=argument+" --framework "+args.framework
    execute_and_raise_exception_if_exit_code_is_not_zero("python", current_directory+os.path.sep+"BuildProject.py " + argument, "", 120, True, False, "Build project")
    
    #build testproject
    argument = " --folder_of_csproj_file "+args.folder_of_test_csproj_file
    argument = argument+" --csproj_filename "+args.test_csproj_filename
    argument = argument+" --buildconfiguration "+args.buildconfiguration
    argument = argument+" --additional_build_arguments "+f'"{str_none_safe(args.additional_build_arguments)}"'
    argument = argument+" --output_directory "+args.test_output_directory
    argument = argument+" --folder_for_nuget_restore "+args.folder_for_nuget_restore
    argument = argument+" --clear_output_directory "+str_none_safe(args.clear_output_directory)
    argument = argument+" --runtimeid "+args.test_runtimeid
    argument = argument+" --verbosity "+args.verbosity
    argument = argument+" --framework "+args.test_framework
    execute_and_raise_exception_if_exit_code_is_not_zero("python", current_directory+os.path.sep+"BuildProject.py " + argument, "", 120, True, False, "Build testproject")
    
    #execute testcases
    testcoveragefilename=args.productname+".TestCoverage.opencover.xml"
    execute_and_raise_exception_if_exit_code_is_not_zero("dotnet", "test "+args.test_csproj_filename+" -c " +args.buildconfiguration +" --verbosity normal --no-build /p:CollectCoverage=true /p:CoverletOutput="+testcoveragefilename+" /p:CoverletOutputFormat=opencover "+str_none_safe(args.additional_test_arguments),args.folder_of_test_csproj_file, 120, True, False, "Execute tests")
   
    #export program
    #clear publish-directory if desired
    if os.path.isdir(args.publish_directory) and args.clear_publish_directory:
        shutil.rmtree(args.publish_directory)
    ensure_directory_exists(args.publish_directory)
    
    copy_tree(args.output_directory, args.publish_directory)
    if args.publish_coverage:
        shutil.copy(args.folder_of_test_csproj_file+os.path.sep+testcoveragefilename,args.code_coverage_folder)
    
finally:
    os.chdir(original_directory)
