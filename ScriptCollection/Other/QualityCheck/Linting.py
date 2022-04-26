from ScriptCollection.ScriptCollection.ScriptCollectionCore import ScriptCollectionCore

def linting():
    ScriptCollectionCore().standardized_tasks_linting_for_python_project_in_common_project_structure(__file__)


if __name__ == "__main__":
    linting()
