import sys
from pathlib import Path
from ScriptCollection.ScriptCollectionCore import ScriptCollectionCore

def common_tasks():
    file=Path(__file__).absolute()
    sc=ScriptCollectionCore()
    version=sc.getversion_from_arguments_or_gitversion(file,sys.argv)
    sc.update_version_of_codeunit_to_project_version(file,version)
    #TODO replace "\nversion = \d+\.\d+\.\d+\n" to f"\\nversion = {version}\\n"

common_tasks()
