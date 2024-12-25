takeown /F "SomeFolderPath" /R /D Y >> C:\Temp\setpermissions.log 2>&1
icacls "SomeFolderPath" /grant NameOfCurrentMachine\%USERNAME%:(OI)(CI)F /T >> C:\Temp\setpermissions.log 2>&1
