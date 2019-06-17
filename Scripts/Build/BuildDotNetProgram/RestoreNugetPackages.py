"""
Important hint: This script is not ready for usage yet
"""
import sys
import argparse
import utilities
import os
print("Start " + os.path.basename(__file__))
start_directory=os.getcwd()
os.chdir(os.path.dirname(os.path.basename(__file__)))
try:

	parser = argparse.ArgumentParser(description='Downloads missing nuget-packages')
	parser.add_argument('--inputfolder', help='Specifies the folder of the packages.config')

	args = parser.parse_args()
	##TODO do this only if packages.config-file exists in projectfolder
	exitCode=utilities.execute("nuget", "restore -SolutionDirectory ..", args.inputfolder)
	if exitCode!=0:
		sys.exit(exitCode)

	print("Finished " + os.path.basename(__file__) + " without errors")
    sys.exit(0)

finally:
    os.chdir(start_directory)
