import os
import sys
import traceback
from os.path import abspath
import argparse
import shutil

def SCDotNetCreateReleaseSignAssembly_cli():

    parser = argparse.ArgumentParser(description='Compiles a csproj-file. This scripts also download required nuget-packages.')
    parser.add_argument('--dllfile', help='Specifies the dllfile which should be signed')
    parser.add_argument('--snkfile', help='Specifies the .snk-file which should be used')

    args = parser.parse_args()
    snk_file=resolve_relative_path_from_current_working_directory(args.snkfile)
    if(os.path.isfile(snk_file)):
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
        execute_and_raise_exception_if_exit_code_is_not_zero("ilasm", f'/{extension} /res:"{filename}.res" /optimize /key="{snk_file}" "{filename}.il"', directory, 3600, True, False, "ilasm")
        os.remove(directory+os.path.sep+filename+".il")
        os.remove(directory+os.path.sep+filename+".res")
    else:
        raise Exception(f".snk-file '{snk_file}' does not exist")


if __name__ == '__main__':
    SCDotNetCreateReleaseSignAssembly_cli()
