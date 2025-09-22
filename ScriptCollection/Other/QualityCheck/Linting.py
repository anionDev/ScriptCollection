import sys
from pathlib import Path
from ScriptCollection.TFCPS_CodeUnitSpecific_Python import TFCPS_CodeUnitSpecific_Python


def linting():
    tf:TFCPS_CodeUnitSpecific_Python=TFCPS_CodeUnitSpecific_Python(__file__,sys.argv)
    tf.linting()


if __name__ == "__main__":
    linting()
