from ScriptCollection.ScriptCollectionCore import ScriptCollectionCore

def common_tasks():
    ScriptCollectionCore.update_version_of_codeunit_to_project_version(__file__)

common_tasks()
