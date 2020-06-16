import os
import sys
from os.path import abspath
import traceback
import argparse
from configparser import ConfigParser
import time

def SCDotNetCreateReleasePrepare_cli():
    
    parser=argparse.ArgumentParser()
    parser.add_argument("configurationfile")
    args=parser.parse_args()
    configurationfile=args.configurationfile
    write_message_to_stdout(f"Run generic releasescript-part '{os.path.basename(__file__)}' with configurationfile '{configurationfile}'")    
    configparser=ConfigParser()
    configparser.read_file(open(configurationfile, mode="r", encoding="utf-8"))

    checkout(configparser.get('general','repository'),configparser.get('prepare','developmentbranchname'))
    version=get_semver_version_from_gitversion(configparser.get('general','repository'))
    if(configparser.getboolean('prepare','updateversionsincsprojfile')):
        csproj_file_with_path=configparser.get('build','folderofcsprojfile')+os.path.sep+configparser.get('build','csprojfilename')
        update_version_in_csproj_file(csproj_file_with_path,version)
        commit(configparser.get('general','repository'), "Updated version in '"+configparser.get('build','csprojfilename')+"'")

    commit_id=merge(configparser.get('general','repository'), configparser.get('prepare','developmentbranchname'), configparser.get('prepare','masterbranchname'),False)
    create_tag(configparser.get('general','repository'), commit_id, configparser.get('prepare','gittagprefix')+ version)
    merge(configparser.get('general','repository'), configparser.get('prepare','masterbranchname'), configparser.get('prepare','developmentbranchname'),True)


if __name__ == '__main__':
    SCDotNetCreateReleasePrepare_cli()
