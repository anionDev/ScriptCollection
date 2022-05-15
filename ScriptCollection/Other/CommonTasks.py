import sys
import os
from ScriptCollection.GeneralUtilities import GeneralUtilities
from ScriptCollection.ScriptCollectionCore import ScriptCollectionCore

def getversion_from_arguments_or_gitversion(self:ScriptCollectionCore, common_tasks_file: str,commandline_arguments:list[str]) -> None:
    version:str=None
    for commandline_argument in commandline_arguments:
        if commandline_argument.startswith("--version="):
            version=commandline_argument.split("=")[1]
    if version is None:
        version=self.get_semver_version_from_gitversion(GeneralUtilities.resolve_relative_path("../..", os.path.dirname(common_tasks_file)))
    return version

def common_tasks():
    file=__file__
    sc=ScriptCollectionCore()
    version=getversion_from_arguments_or_gitversion(sc,file,sys.argv)
    #sc.update_version_of_codeunit_to_project_version(file,version)
    #TODO replace "\nversion = \d+\.\d+\.\d+\n" to f"\\nversion = {version}\\n"

common_tasks()
