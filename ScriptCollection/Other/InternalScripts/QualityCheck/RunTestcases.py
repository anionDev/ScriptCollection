import os
from pathlib import Path
from ScriptCollection.GeneralUtilities import GeneralUtilities
from ScriptCollection.ScriptCollectionCore import ScriptCollectionCore

def run_testcases_for_python_project(self:ScriptCollectionCore,repository_folder:str,codeunitname:str):
    codeunif_folder=os.path.join(repository_folder,codeunitname)
    self.start_program_synchronously("coverage","run -m pytest",codeunif_folder,prevent_using_epew=True)
    self.start_program_synchronously("coverage","xml",codeunif_folder,prevent_using_epew=True)
    coveragefile=os.path.join(repository_folder,codeunitname,"Other/TestCoverage/TestCoverage.xml")
    GeneralUtilities.ensure_file_does_not_exist(coveragefile)
    os.rename(os.path.join(repository_folder,codeunitname,"coverage.xml"),coveragefile)

def generate_coverage_report(self:ScriptCollectionCore,repository_folder:str,codeunitname:str, generate_badges:bool=True):
    """This script expects that the file '<repositorybasefolder>/<codeunitname>/Other/TestCoverage/TestCoverage.xml' exists.
This script expectes that the testcoverage-reportfolder is '<repositorybasefolder>/Other/TestCoverage/Report'.
This script expectes that a test-coverage-badges should be added to '<repositorybasefolder>/TestCoverage/Badges'."""
    GeneralUtilities.ensure_directory_does_not_exist(os.path.join(repository_folder,codeunitname,"Other/TestCoverage/Report"))
    GeneralUtilities.ensure_directory_exists(os.path.join(repository_folder,codeunitname,"Other/TestCoverage/Report"))
    self.start_program_synchronously("reportgenerator","-reports:Other/TestCoverage/TestCoverage.xml -targetdir:Other/TestCoverage/Report",os.path.join(repository_folder,codeunitname))
    if generate_badges:
        self.start_program_synchronously("reportgenerator","-reports:Other/TestCoverage/TestCoverage.xml -targetdir:Other/TestCoverage/Badges -reporttypes:Badges",
            os.path.join(repository_folder,codeunitname))

def run_testcases_for_project_in_common_project_structure(self:ScriptCollectionCore,repository_folder:str,codeunitname:str, generate_badges:bool=True):
    run_testcases_for_python_project(self,repository_folder,codeunitname)
    generate_coverage_report(self,repository_folder,codeunitname, generate_badges)


def run_testcases():
    run_testcases_for_project_in_common_project_structure(ScriptCollectionCore(),
        str(Path(os.path.dirname(__file__)).parent.parent.parent.parent.absolute()),"ScriptCollection", True)

if __name__=="__main__":
    run_testcases()
