import os
import sys
print("test: hello from SCpythonCreateRelease")
sys.exit(0)
from os.path import abspath
import traceback
import argparse
error_occurred=False
original_directory=os.getcwd()
current_directory = os.path.dirname(os.path.abspath(__file__))

def execute_task(name:str, configurationfile:str):
    execute_and_raise_exception_if_exit_code_is_not_zero("python", f"{name}.py {configurationfile}",os.getcwd(), 3600, 1, False, f"Run {name}.py")

try:
    sys.path.append(abspath(os.path.join(current_directory,f"..{os.path.sep}..{os.path.sep}Miscellaneous")))
    from Utilities import *
    from configparser import ConfigParser

    parser=argparse.ArgumentParser()
    parser.add_argument("configurationfile")
    args=parser.parse_args()
    configurationfile=args.configurationfile
    write_message_to_stdout(f"Run generic releasescript with configurationfile '{configurationfile}'")
    os.chdir(f"{current_directory}{os.path.sep}CreateReleaseTasks")
    configparser=ConfigParser()
    configparser.read_file(open(configurationfile, mode="r", encoding="utf-8"))

    if configparser.getboolean('prepare','prepare'):
        execute_task("01_Prepare", configurationfile)
    execute_task("02_Build", configurationfile)
    execute_task("03_Release", configurationfile)
    if configparser.getboolean('reference','generatereference'):
        execute_task("04_Reference", configurationfile)

except Exception as exception:
    write_exception_to_stderr_with_traceback(exception, traceback)
    error_occurred=True

finally:
    os.chdir(original_directory)

message="CreateRelease exits with exitcode "
if(error_occurred):
    write_message_to_stderr(message+"1")
    sys.exit(1)
else:
    write_message_to_stdout(message+"0")
    sys.exit(0)
