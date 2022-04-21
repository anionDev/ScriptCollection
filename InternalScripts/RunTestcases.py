import os
from pathlib import Path
from ScriptCollection.GeneralUtilities import GeneralUtilities
from ScriptCollection.ScriptCollectionCore import ScriptCollectionCore

def RunTestcases():
    sc=ScriptCollectionCore()
    repository_folder:str=str(Path(os.path.dirname(__file__)).parent.absolute())
    sc.start_program_synchronously("coverage","run -m pytest",repository_folder)
    sc.start_program_synchronously("coverage","xml",repository_folder)
    coveragefile=os.path.join(repository_folder,"Other/TestCoverage/TestCoverage.xml")
    GeneralUtilities.ensure_file_does_not_exist(coveragefile)
    os.rename(os.path.join(repository_folder,"coverage.xml"),coveragefile)
    GeneralUtilities.ensure_directory_does_not_exist(os.path.join(repository_folder,"Other/TestCoverage/Report"))
    GeneralUtilities.ensure_directory_exists(os.path.join(repository_folder,"Other/TestCoverage/Report"))
    GeneralUtilities.ensure_file_exists(os.path.join(repository_folder,"Other/TestCoverage/.gitignore"))
    sc.start_program_synchronously("reportgenerator","-reports:Other/TestCoverage/TestCoverage.xml -targetdir:Other/TestCoverage/Report",repository_folder)
    sc.start_program_synchronously("reportgenerator","-reports:Other/TestCoverage/TestCoverage.xml -targetdir:Other/Badges/TestCoverage -reporttypes:Badges",repository_folder)

if __name__=="__main__":
    RunTestcases()
