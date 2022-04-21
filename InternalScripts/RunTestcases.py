import os
from pathlib import Path
from ScriptCollection.ScriptCollectionCore import ScriptCollectionCore

def RunTestcasesStarter():
    sc=ScriptCollectionCore()
    sc.run_testcases_for_python_project(str(Path(os.path.dirname(__file__)).parent.absolute()))
    sc.generate_coverage_report(str(Path(os.path.dirname(__file__)).parent.absolute()))

if __name__=="__main__":
    RunTestcasesStarter()
