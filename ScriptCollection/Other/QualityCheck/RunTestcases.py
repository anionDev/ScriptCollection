import sys
from pathlib import Path
from ScriptCollection.TFCPS_CodeUnitSpecific_Python import TFCPS_CodeUnitSpecific_Python


def run_testcases():
    tf:TFCPS_CodeUnitSpecific_Python=TFCPS_CodeUnitSpecific_Python(__file__,sys.argv)
    tf.run_testcases()


if __name__ == "__main__":
    run_testcases()
