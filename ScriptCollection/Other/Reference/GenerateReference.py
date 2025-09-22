import sys
from pathlib import Path
from ScriptCollection.TFCPS_CodeUnitSpecific_Python import TFCPS_CodeUnitSpecific_Python


def generate_reference():
    
    tf:TFCPS_CodeUnitSpecific_Python=TFCPS_CodeUnitSpecific_Python(__file__,sys.argv)
    tf.generate_reference()


if __name__ == "__main__":
    generate_reference()
