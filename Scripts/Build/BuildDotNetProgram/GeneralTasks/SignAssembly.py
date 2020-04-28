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

    start_directory=os.getcwd()
    os.chdir(os.path.dirname(os.path.abspath(__file__)))

    import argparse
    import shutil
    parser = argparse.ArgumentParser(description='Compiles a csproj-file. This scripts also download required nuget-packages.')
    parser.add_argument('--dllfile', help='Specifies the dllfile which should be signed')
    parser.add_argument('--snkfile', help='Specifies the .snk-file which should be used')

    args = parser.parse_args()

    file=resolve_relative_path_from_current_working_directory(args.dllfile)
    directory=os.path.dirname(file)
    filename=os.path.basename(file)
    if filename.lower().endswith(".dll"):
        filename=filename[:-4]
        extension="dll"
    elif filename.lower().endswith(".exe"):
        filename=filename[:-4]
        extension="exe"
    else:
        raise Exception("Only .dll-files and .exe-files can be signed")
    execute_and_raise_exception_if_exit_code_is_not_zero("ildasm", f'/all /typelist /text /out="{filename}.il" "{filename}.{extension}"', directory, 3600, True, False, "ildasm")
    execute_and_raise_exception_if_exit_code_is_not_zero("ilasm", f'/{extension} /res:"{filename}.res" /optimize /key="{args.snkfile}" "{filename}.il"', directory, 3600, True, False, "ilasm")
    os.remove(directory+os.path.sep+filename+".il")
    os.remove(directory+os.path.sep+filename+".res")

finally:
    os.chdir(original_directory)
