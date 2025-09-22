import sys
from pathlib import Path
from ScriptCollection.TFCPS_CodeUnitSpecific_Python import TFCPS_CodeUnitSpecific_Python


def update_dependencies():
    TFCPS_CodeUnitSpecific_Python(sys.argv).update_dependencies()


if __name__ == "__main__":
    update_dependencies()
