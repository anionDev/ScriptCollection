import os
from pathlib import Path
from ScriptCollection.ScriptCollectionCore import ScriptCollectionCore

def linting():
    ScriptCollectionCore().standardized_tasks_linting_for_python_project_in_common_project_structure(
        str(Path(os.path.dirname(__file__)).parent.parent.parent.parent.absolute()),"ScriptCollection")

if __name__=="__main__":
    linting()
