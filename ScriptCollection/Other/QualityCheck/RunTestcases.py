from pathlib import Path
import os
from ScriptCollection.ScriptCollectionCore import ScriptCollectionCore
from ScriptCollection.GeneralUtilities import GeneralUtilities

class ScriptCollectionCore2:

    self2:ScriptCollectionCore=ScriptCollectionCore()

    def standardized_tasks_run_testcases_for_python_project(self, repository_folder: str, codeunitname: str):
        codeunit_folder = os.path.join(repository_folder, codeunitname)
        self.self2.run_program("coverage", "run -m pytest", codeunit_folder)
        self.self2.run_program("coverage", "xml", codeunit_folder)
        coveragefile = os.path.join(repository_folder, codeunitname, "Other/QualityCheck/TestCoverage/TestCoverage.xml")
        GeneralUtilities.ensure_file_does_not_exist(coveragefile)
        os.rename(os.path.join(repository_folder, codeunitname, "coverage.xml"), coveragefile)

    def standardized_tasks_generate_coverage_report(self, repository_folder: str, codeunitname: str, generate_badges: bool = True):
        """This script expects that the file '<repositorybasefolder>/<codeunitname>/Other/QualityCheck/TestCoverage/TestCoverage.xml' exists.
    This script expectes that the testcoverage-reportfolder is '<repositorybasefolder>/Other/QualityCheck/TestCoverage/TestCoverageReport'.
    This script expectes that a test-coverage-badges should be added to '<repositorybasefolder>other//QualityCheck/TestCoverage/Badges'."""
        GeneralUtilities.ensure_directory_does_not_exist(os.path.join(repository_folder, codeunitname, "Other/QualityCheck/TestCoverage/TestCoverageReport"))
        GeneralUtilities.ensure_directory_exists(os.path.join(repository_folder, codeunitname, "Other/QualityCheck/TestCoverage/TestCoverageReport"))
        self.self2.run_program("reportgenerator", "-reports:Other/QualityCheck/TestCoverage/TestCoverage.xml -targetdir:Other/QualityCheck/TestCoverage/TestCoverageReport", os.path.join(repository_folder, codeunitname))
        if generate_badges:
            self.self2.run_program("reportgenerator", "-reports:Other/QualityCheck/TestCoverage/TestCoverage.xml -targetdir:Other/QualityCheck/TestCoverage/Badges -reporttypes:Badges",
                                os.path.join(repository_folder, codeunitname))

    def standardized_tasks_run_testcases_for_python_project_in_common_project_structure(self,run_testcases_file:str, generate_badges: bool = True):
        repository_folder: str=str(Path(os.path.dirname(run_testcases_file)).parent.parent.parent.absolute())
        codeunitname: str=Path(os.path.dirname(run_testcases_file)).parent.parent.name
        self.standardized_tasks_run_testcases_for_python_project(repository_folder, codeunitname)
        self.standardized_tasks_generate_coverage_report(repository_folder, codeunitname, generate_badges)

def run_testcases():
    ScriptCollectionCore2().standardized_tasks_run_testcases_for_python_project_in_common_project_structure(__file__)


if __name__ == "__main__":
    run_testcases()
