import sys
from pathlib import Path
from ScriptCollection.TFCPS_CodeUnitSpecific_Python import TFCPS_CodeUnitSpecific_Python

def build():
    
    tf:TFCPS_CodeUnitSpecific_Python=TFCPS_CodeUnitSpecific_Python(__file__,sys.argv)
    tf.standardized_tasks_build_for_python_codeunit(script_file)


if __name__ == "__main__":
    build()
