import os
import sys
from os.path import abspath
import argparse
import traceback
error_occurred=False
original_directory=os.getcwd()
current_directory = os.path.dirname(os.path.abspath(__file__))
os.chdir(current_directory)

def get_publishdirectory(configparser, version:str):
    result=configparser.get('build','publishdirectory')
    result=result.replace("__version__",version)
    ensure_directory_exists(result)
    return result

def get_target_runtimes(configparser):
    result=[]
    for runtime in configparser.get('build','runtimes').split(","):
        result.append(runtime.strip())
    return result

try:

    sys.path.append(abspath(os.path.join(current_directory,f"..{os.path.sep}..{os.path.sep}..{os.path.sep}Miscellaneous")))
    from Utilities import *
    sys.path.append(abspath(os.path.join(current_directory,f"..{os.path.sep}..{os.path.sep}..{os.path.sep}Git")))
    from CommonGitFunctions import *
    from configparser import ConfigParser

    parser=argparse.ArgumentParser()
    parser.add_argument("configurationfile")
    args=parser.parse_args()
    configurationfile=args.configurationfile
    write_message_to_stdout(f"Run generic releasescript-part '{os.path.basename(__file__)}' with configurationfile '{configurationfile}'")

    configparser=ConfigParser()
    configparser.read_file(open(configurationfile, mode="r", encoding="utf-8"))

    productname=configparser.get('general','productname')
    build_tools_folder=abspath(f"..{os.path.sep}GeneralTasks")
    repository_folder=configparser.get('general','repository')
    version=get_semver_version_from_gitversion(repository_folder)
    publish_directory    = get_publishdirectory(configparser,version)
    code_coverage_folder = get_publishdirectory(configparser,version)
    runtime_for_tests=configparser.get('build','testruntime')
    
    for runtime in get_target_runtimes(configparser):     
        publish_directory_for_runtime=os.path.join(publish_directory,runtime)
        ensure_directory_exists(publish_directory_for_runtime)
        argument=""
        
        #parameter for project
        argument=argument + ' --folder_of_csproj_file '+encapsulate_with_quotes(configparser.get('build','folderofcsprojfile'))
        argument=argument + ' --csproj_filename '+encapsulate_with_quotes(configparser.get('build','csprojfilename'))
        argument=argument + ' --publish_directory '+encapsulate_with_quotes(publish_directory_for_runtime)
        argument=argument + ' --output_directory '+encapsulate_with_quotes(configparser.get('build','buildoutputdirectory'))
        argument=argument + ' --framework '+configparser.get('build','dotnetframework')
        argument=argument + ' --runtimeid '+runtime
           
        #parameter for testproject
        if configparser.getboolean('build','hastestproject') and runtime_for_tests==runtime: 
            argument=argument + ' --has_test_project'
            argument=argument + ' --folder_of_test_csproj_file '+encapsulate_with_quotes(configparser.get('build','folderoftestcsprojfile'))
            argument=argument + ' --test_csproj_filename '+encapsulate_with_quotes(configparser.get('build','testcsprojfilename'))
            argument=argument + ' --test_output_directory '+encapsulate_with_quotes(configparser.get('build','testoutputfolder'))
            argument=argument + ' --test_framework '+encapsulate_with_quotes(configparser.get('build','testdotnetframework'))
            argument=argument + ' --test_runtimeid '+encapsulate_with_quotes(runtime_for_tests)
            argument=argument + ' --publish_coverage '+str(True)
            argument=argument + ' --code_coverage_folder '+encapsulate_with_quotes(code_coverage_folder)

        #parameter for project and testproject
        argument=argument + f' --clear_output_directory {str(True)}'
        argument=argument + f' --productname "'+configparser.get('general','productname')+'"'
        argument=argument + f' --buildconfiguration "' +configparser.get('build','buildconfiguration')+'"'

        #build and execute testcases
        execute_and_raise_exception_if_exit_code_is_not_zero("python",f"{build_tools_folder}{os.path.sep}BuildTestprojectAndExecuteTests.py {argument}",os.getcwd(), 3600, 1, False, "Build "+configparser.get('general','productname'))

        #sign assembly
        if configparser.getboolean('build','signfiles'):
            for file_to_sign in configparser.get('build','filestosign').split(","):
                file_to_sign=file_to_sign.strip()
                snkfile=configparser.get('build','snkfile')
                execute_and_raise_exception_if_exit_code_is_not_zero("python",f'{build_tools_folder}{os.path.sep}SignAssembly.py --dllfile "{publish_directory_for_runtime}{os.path.sep}{file_to_sign}" --snkfile "{snkfile}"',os.getcwd(), 3600, 1, False, "Sign "+file_to_sign)

except Exception as exception:
    write_exception_to_stderr_with_traceback(exception, traceback)
    error_occurred=True

finally:
    os.chdir(original_directory)

if(error_occurred):
    sys.exit(1)
else:
    sys.exit(0)
