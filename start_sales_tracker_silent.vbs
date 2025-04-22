Set WshShell = CreateObject("WScript.Shell")
strPath = Replace(WScript.ScriptFullName, WScript.ScriptName, "SalesTracker.exe")
WshShell.Run Chr(34) & strPath & Chr(34), 0, False
Set WshShell = Nothing 