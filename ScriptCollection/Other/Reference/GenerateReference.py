from ScriptCollection.ScriptCollectionCore import ScriptCollectionCore
from ScriptCollection.GeneralUtilities import GeneralUtilities
from pathlib import Path
import os

class ScriptCollectionCore2:

    self2:ScriptCollectionCore=ScriptCollectionCore()

    def standardized_tasks_generate_reference_by_docfx(self,generate_reference_script_file:str)->None:
        folder_of_current_file=os.path.dirname(generate_reference_script_file)
        generated_reference_folder=os.path.join(folder_of_current_file,"GeneratedReference")
        GeneralUtilities.ensure_directory_does_not_exist(generated_reference_folder)
        GeneralUtilities.ensure_directory_exists(generated_reference_folder)
        obj_folder=os.path.join(folder_of_current_file,"obj")
        GeneralUtilities.ensure_directory_does_not_exist(obj_folder)
        GeneralUtilities.ensure_directory_exists(obj_folder)
        self.self2.run_program("docfx","docfx.json",folder_of_current_file)


def generate_reference():
    ScriptCollectionCore2().standardized_tasks_generate_reference_by_docfx(__file__)


if __name__ == "__main__":
    generate_reference()
