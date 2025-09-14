Set WshShell = CreateObject("WScript.Shell")
WshShell.Run "cmd /c cd D:\Code\Python\Projects\toph-submissions && python storeSubmissionCodes.py", 0, False
WshShell.Run "powershell -ExecutionPolicy Bypass -File progress_widget.ps1", 0, False