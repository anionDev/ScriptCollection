"""
This script is suitable for small files (<200KB).
"""
import sys
import os
content=open(sys.argv[1],'rb').read()
amount_of_columns=16
column=0
for char in content:
    column=(column+1) % amount_of_columns
    sys.stdout.write('%02X'%char)
    if(column==0):
        sys.stdout.write(os.linesep)
    else:
        sys.stdout.write(' ')