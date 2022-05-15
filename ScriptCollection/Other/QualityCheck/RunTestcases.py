from ScriptCollection.ScriptCollectionCore import ScriptCollectionCore
import pathlib

def run_testcases():
    test=pathlib.Path(__file__).parent.resolve()
    ScriptCollectionCore().standardized_tasks_run_testcases_for_python_project_in_common_project_structure(__file__)


run_testcases()
