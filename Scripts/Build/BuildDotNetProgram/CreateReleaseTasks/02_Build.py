import os
import sys
from os.path import abspath
import argparse
import traceback
error_occurred=False
original_directory=os.getcwd()
current_directory = os.path.dirname(os.path.abspath(__file__))
os.chdir(current_directory)

try:

    sys.path.append(abspath(os.path.join(current_directory,f"..{os.path.sep}..{os.path.sep}..{os.path.sep}Miscellaneous")))
    from Utilities import *
    from configparser import ConfigParser
    
    parser=argparse.ArgumentParser()
    parser.add_argument("configurationfile")
    args=parser.parse_args()
    configurationfile=args.configurationfile
    write_message_to_stdout(f"Run generic releasescript-part '{os.path.basename(__file__)}' with configurationfile '{configurationfile}'")
    
    configparser=ConfigParser()
    configparser.read(configurationfile)
    
    productname=configparser.get('general','productname')
    build_tools_folder=abspath(f"..{os.path.sep}GeneralTasks")
    repository_folder=configparser.get('general','repository')
    version=execute_and_raise_exception_if_exit_code_is_not_zero("gitversion","/showVariable semVer",repository_folder,120,False,False,"Gitversion",False, None )[1].replace("\r","").replace("\n","")
    publish_directory=f"{configparser.get('build','publishdirectory')}{os.path.sep}{version}{os.path.sep}Binary"
    code_coverage_folder=configparser.get('build','publishdirectory')+os.path.sep+version
    
    argument=""

    #parameter for project
    argument=argument + ' --folder_of_csproj_file "' +configparser.get('build','folderofcsprojfile')+'"'
    argument=argument + ' --csproj_filename "' +configparser.get('build','csprojfilename')+'"'
    argument=argument + " --publish_directory " + '"'+publish_directory+'"'
    argument=argument + ' --output_directory "' +configparser.get('build','buildoutputdirectory')+'"'

    #parameter for testproject
    argument=argument + ' --folder_of_test_csproj_file "' +configparser.get('build','folderoftestcsprojfile')+'"'
    argument=argument + ' --test_csproj_filename "' +configparser.get('build','testcsprojfilename')+'"'
    argument=argument + ' --test_output_directory "' +configparser.get('build','testoutputfolder')+'"'
    #argument=argument + " --additional_test_arguments " + ""
    #argument=argument + " --test_runtimeid " + ""
    argument=argument + " --test_framework " + "netcoreapp3.1"
    argument=argument + ' --code_coverage_folder "' +code_coverage_folder+'"'
 
    #parameter for project and testproject
    argument=argument + ' --buildconfiguration "' +configparser.get('build','buildconfiguration')+'"'
    argument=argument + " --folder_for_nuget_restore " + f'"{repository_folder}"'
    #argument=argument + " --additional_build_arguments " + ""
    argument=argument + " --clear_output_directory " +"true"

    #execute testcases
    execute_and_raise_exception_if_exit_code_is_not_zero("python",f"{build_tools_folder}{os.path.sep}BuildTestprojectAndExecuteTests.py {argument}",os.getcwd(), 120,  False, False, configparser.get('general','productname')+"Build")
    
    #calculate testcoverage
    #todo
    
    #sign assembly
    snkfile=configparser.get('build','snkfile')
    execute_and_raise_exception_if_exit_code_is_not_zero("python",f'{build_tools_folder}{os.path.sep}SignAssembly.py --dllfile "{publish_directory}{os.path.sep}{productname}.dll" --snkfile "{snkfile}"',os.getcwd(), 120,  False, False, configparser.get('general','productname')+"Sign")

except Exception as exception:
    write_exception_to_stderr_with_traceback(exception, traceback)
    error_occurred=True

finally:
    os.chdir(original_directory)

if(error_occurred):
    sys.exit(1)
else:
    sys.exit(0)
