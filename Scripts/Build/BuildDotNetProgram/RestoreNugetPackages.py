import sys
import argparse
import os
from os.path import abspath
import shutil
sys.path.append(abspath(os.path.join(os.path.dirname(os.path.realpath(__file__)),f"..{os.path.sep}..{os.path.sep}Miscellaneous")))
from Utilities import *
write_message_to_stdout("Start " + os.path.basename(__file__))
start_directory=os.getcwd()
os.chdir(os.path.dirname(os.path.abspath(__file__)))

try:
    parser = argparse.ArgumentParser(description='Downloads missing nuget-packages')
    parser.add_argument('--inputfolder', help='Specifies the folder of the .csproj-file')
    parser.add_argument('--solutiondirectory', default="..", help='Specifies the folder of the .sln-file')

    args = parser.parse_args()
    packages_config_file=os.path.join(args.inputfolder,"packages.config")
    if(os.path.isfile(packages_config_file)):
        exit_code=execute("nuget", "restore -SolutionDirectory "+args.solutiondirectory, args.inputfolder)
        if exit_code!=0:
            sys.stderr.write("nuget had exitcode " +str(exit_code)+"\n")
            sys.exit(exit_code)

    write_message_to_stdout("Finished " + os.path.basename(__file__) + " without errors")
finally:
    os.chdir(start_directory)
