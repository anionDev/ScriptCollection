import sys
import argparse
import utilities
import os
print("Start " + os.path.basename(__file__))
start_directory=os.getcwd()
os.chdir(os.path.dirname(os.path.abspath(__file__)))
try:

    parser = argparse.ArgumentParser(description='Downloads missing nuget-packages')
    parser.add_argument('--inputfolder', help='Specifies the folder of the packages.config')

    args = parser.parse_args()
    packages_config_file=os.path.join(args.inputfolder,"packages.config")
    if(os.path.isfile(packages_config_file)):
        exit_code=utilities.execute("nuget", "restore -SolutionDirectory ..", args.inputfolder)
        if exit_code!=0:
            sys.exit(exit_code)

    print("Finished " + os.path.basename(__file__) + " without errors")
    sys.exit(0)

finally:
    os.chdir(start_directory)
