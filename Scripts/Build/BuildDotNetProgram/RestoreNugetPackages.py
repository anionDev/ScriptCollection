import sys
import argparse
import os
from os.path import abspath
import shutil
sys.path.append(abspath(os.path.join(os.path.dirname(os.path.realpath(__file__)),f"..{os.path.sep}..{os.path.sep}Miscellaneous")))
from Utilities import *
sys.stdout.write("Start " + os.path.basename(__file__)+"\n")
start_directory=os.getcwd()
os.chdir(os.path.dirname(os.path.abspath(__file__)))

try:
    parser = argparse.ArgumentParser(description='Downloads missing nuget-packages')
    parser.add_argument('--inputfolder', help='Specifies the folder of the packages.config')

    args = parser.parse_args()
    packages_config_file=os.path.join(args.inputfolder,"packages.config")
    if(os.path.isfile(packages_config_file)):
        exit_code=execute("nuget", "restore -SolutionDirectory ..", args.inputfolder)
        if exit_code!=0:
            sys.stderr.write("nuget had exitcode " +str(exit_code)+"\n")
            sys.exit(exit_code)

    sys.stdout.write("Finished " + os.path.basename(__file__) + " without errors\n")
finally:
    os.chdir(start_directory)
