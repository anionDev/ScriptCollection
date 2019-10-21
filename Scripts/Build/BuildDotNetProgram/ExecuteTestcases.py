import argparse
import os
import sys
import shutil
from os.path import abspath
sys.path.append(abspath(os.path.join(os.path.dirname(os.path.realpath(__file__)),f"..{os.path.sep}..{os.path.sep}Miscellaneous")))
from Utilities import *

write_message_to_stdout("Start " + os.path.basename(__file__))
start_directory=os.getcwd()
os.chdir(os.path.dirname(os.path.abspath(__file__)))
try:

    parser = argparse.ArgumentParser(description='Executed tests of a given test-dll-file.')
    parser.add_argument('--testdll', help='Specifies the dll-file where the testcases are stored in')
    args = parser.parse_args()

    write_message_to_stdout(f"Arguments:")
    write_message_to_stdout("testdll: " + args.testdll)
    
    write_message_to_stdout("TODO: run 'vstest.console "+ args.testdll+"'")

    write_message_to_stdout("Finished " + os.path.basename(__file__) + " without errors")
finally:
    os.chdir(start_directory)
