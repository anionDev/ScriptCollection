import os
from pathlib import Path
from ScriptCollection.ScriptCollectionCore import ScriptCollectionCore
from ScriptCollection.GeneralUtilities import GeneralUtilities

def build_for_python_project_in_common_project_structure(self:ScriptCollectionCore,repository_folder:str,codeunit:str):
    self.start_program_synchronously("git","clean -dfx", repository_folder)
    target_directory=os.path.join(repository_folder,codeunit,"Other","InternalScripts","Build","Result")
    GeneralUtilities.ensure_directory_does_not_exist(target_directory)
    GeneralUtilities.ensure_directory_exists(target_directory)
    self.start_program_synchronously("python",f"Setup.py bdist_wheel --dist-dir {target_directory}",os.path.join( repository_folder,codeunit))

def build():
    build_for_python_project_in_common_project_structure(ScriptCollectionCore(),
        str(Path(os.path.dirname(__file__)).parent.parent.parent.parent.absolute()),"ScriptCollection")

if __name__=="__main__":
    build()
