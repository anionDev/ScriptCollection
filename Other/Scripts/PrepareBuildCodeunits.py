from pathlib import Path
from ScriptCollection.GeneralUtilities import GeneralUtilities
from ScriptCollection.ScriptCollectionCore import ScriptCollectionCore
from ScriptCollection.TFCPS_Tools_General import TFCPS_Tools_General


def prepare_build_codeunits():
    t = TFCPS_Tools_General(ScriptCollectionCore())
    current_file = str(Path(__file__).absolute())
    repository_folder = GeneralUtilities.resolve_relative_path( "../../..", current_file)
    t.generate_tasksfile_from_workspace_file(repository_folder)
    t.generate_codeunits_overview_diagram(repository_folder)
    t.generate_svg_files_from_plantuml_files_for_repository(repository_folder)


if __name__ == "__main__":
    prepare_build_codeunits()
