from ScriptCollection.ScriptCollectionCore import ScriptCollectionCore
from pathlib import Path

def run_testcases():
    file=Path(__file__).absolute()
    print("File      Path:", file)
    ScriptCollectionCore().standardized_tasks_run_testcases_for_python_project_in_common_project_structure(file)


run_testcases()
