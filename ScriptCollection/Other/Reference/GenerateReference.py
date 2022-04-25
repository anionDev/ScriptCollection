import os
from ScriptCollection.ScriptCollectionCore import ScriptCollectionCore
from ScriptCollection.GeneralUtilities import GeneralUtilities


def standardized_tasks_generate_reference_by_docfx(self:ScriptCollectionCore,generate_reference_script_file:str)->None:
    folder_of_current_file=os.path.dirname(generate_reference_script_file)
    generated_reference_folder=os.path.join(folder_of_current_file,"GeneratedReference")
    GeneralUtilities.ensure_directory_does_not_exist(generated_reference_folder)
    GeneralUtilities.ensure_directory_exists(generated_reference_folder)
    self.run_program("docfx","docfx.json",folder_of_current_file)

def run_testcases():
    standardized_tasks_generate_reference_by_docfx(ScriptCollectionCore(),__file__)

if __name__ == "__main__":
    run_testcases()
