' Lanzador 100% invisible para Selenium Background Updater
' Ejecuta PowerShell sin parpadeo de consola CMD (SW_HIDE = 0)
Set objShell = CreateObject("WScript.Shell")
strCommand = "powershell.exe -NoProfile -ExecutionPolicy Bypass -File ""C:\thorium\selenium_updater.ps1"" -Silent"
objShell.Run strCommand, 0, False
