Option Explicit 
Dim WSHShell, proxyEnableVal, username 
Set WSHShell = WScript.CreateObject("WScript.Shell")
username = WSHShell.ExpandEnvironmentStrings("%USERNAME%") 
Const PROXY_OFF = 0
if Wscript.Arguments.Count=1 Then
	dim Argument
    Argument = WScript.Arguments(0)
	If Argument="on" then
		TurnProxyOn
	elseif Argument="off" then
		TurnProxyOff
	else
		Toggle
	End if
else
	Toggle
End if
sub Toggle
	proxyEnableVal = wshshell.regread("HKCU\Software\Microsoft\Windows\CurrentVersion\Internet Settings\ProxyEnable")
	If proxyEnableVal = PROXY_OFF Then 
	  TurnProxyOn
	Else
	  TurnProxyOff
	End If
End Sub
Sub TurnProxyOn 
  WSHShell.regwrite "HKCU\Software\Microsoft\Windows\CurrentVersion\Internet Settings\ProxyEnable", 1, "REG_DWORD"
  WSHShell.Popup "Internet proxy is now ON", 1, "Proxy Settings"
End Sub
Sub TurnProxyOff 
  WSHShell.regwrite "HKCU\Software\Microsoft\Windows\CurrentVersion\Internet Settings\ProxyEnable", 0, "REG_DWORD"
  WSHShell.Popup "Internet proxy is now OFF", 1, "Proxy Settings"
End Sub
