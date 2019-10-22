import argparse
import os
import sys
import shutil
print("Start " + os.path.basename(__file__))
start_directory=os.getcwd()
os.chdir(os.path.dirname(os.path.abspath(__file__)))
try:

    parser = argparse.ArgumentParser(description='Executed tests of a given test-dll-file.')
    parser.add_argument('--testdll', help='Specifies the dll-file where the testcases are stored in')
    args = parser.parse_args()

    print("(todo)")

    sys.stdout.write("Finished " + os.path.basename(__file__) + " without errors\n")
finally:
    os.chdir(start_directory)
