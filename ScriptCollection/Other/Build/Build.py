import sys
from ScriptCollection.TFCPS_CodeUnitSpecific_Python import TFCPS_CodeUnitSpecific_Python_Functions,TFCPS_CodeUnitSpecific_Python_CLI
 
def build():
    
    tf:TFCPS_CodeUnitSpecific_Python_Functions=TFCPS_CodeUnitSpecific_Python_CLI.parse(__file__,sys.argv)
    tf.build({})


if __name__ == "__main__":
    build()
