@echo off
net session >nul 2>&1
if %errorLevel% == 0 (
    echo Administrator permissions confirmed.
    powershell.exe -Command "Add-MpPreference -ExclusionPath 'C:\src', 'C:\thorium', 'C:\helium'"
    echo.
    echo =========================================================
    echo  Folders C:\src, C:\thorium and C:\helium have been
    echo  successfully added to Windows Defender exclusions.
    echo =========================================================
    timeout /t 3
) else (
    powershell -Command "Start-Process cmd -ArgumentList '/c %~fn0' -Verb RunAs"
)
