from pathlib import Path
from ScriptCollection.ScriptCollectionCore import ScriptCollectionCore

def run_testcases():
    ScriptCollectionCore().standardized_tasks_run_testcases_for_python_project_in_common_project_structure(Path(__file__).absolute())


if __name__ == "__main__":
    run_testcases()
