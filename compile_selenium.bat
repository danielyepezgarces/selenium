@echo off
title Selenium Build & Management Center (AVX2 + Helium)
color 0B

:: ==============================================================================
:: Environment Variables
:: ==============================================================================
set DEPOT_TOOLS_UPDATE=0
set DEPOT_TOOLS_WIN_TOOLCHAIN=0
set vs2022_install=C:\Program Files\Microsoft Visual Studio\2022\Community
set THOR_DIR=C:\thorium
set PATH=C:\src\depot_tools;C:\Program Files\Git\cmd;C:\Users\Daniel Yepez Garces\AppData\Local\Programs\Python\Python314;%PATH%
set SRC_DIR=C:\src\chromium\src
set OUT_DIR=C:\src\chromium\src\out\thorium
set CMD_MODE=0
set TARGET=

:: Process command line argument directly if provided
if "%1"=="1" (set BUILD_TARGET=chrome & set AUTO_LAUNCH=0 & set CMD_MODE=1 & goto :EXECUTE_BUILD)
if "%1"=="2" (set BUILD_TARGET=chrome & set AUTO_LAUNCH=1 & set CMD_MODE=1 & goto :EXECUTE_BUILD)
if "%1"=="3" (set BUILD_TARGET=mini_installer & set AUTO_LAUNCH=0 & set CMD_MODE=1 & goto :EXECUTE_BUILD)
if "%1"=="4" (set CMD_MODE=1 & goto :EXECUTE_DRY_RUN)
if "%1"=="5" (set CMD_MODE=1 & goto :RELEASE_LOCK)
if "%1"=="6" (set CMD_MODE=1 & goto :LAUNCH_DIRECT)
if "%1"=="7" exit /b 0
if not "%1"=="" (
    set BUILD_TARGET=%1
    set AUTO_LAUNCH=0
    set CMD_MODE=1
    goto :EXECUTE_BUILD
)

:MENU
cls
color 0B
echo ==============================================================================
echo           CONTROL & BUILD CENTER: SELENIUM BROWSER
echo ==============================================================================
echo.
echo  Select an option:
echo.
echo    [1] Build Selenium (chrome)              - Fast incremental compilation
echo    [2] Build and Launch Selenium            - Compiles and launches selenium.exe when done
echo    [3] Generate Installer (mini_installer)  - Creates standalone installer (.exe)
echo    [4] Quick verification (Dry Run -n)      - Checks pending build targets without compiling
echo    [5] Unlock Ninja (.ninja_lock)           - Terminates hung processes and removes lock
echo    [6] Launch Selenium directly             - Runs already built out\thorium\selenium.exe
echo    [7] Exit
echo.
echo ==============================================================================
set /p OPTION=" Enter your choice (1-7) and press Enter: "

if "%OPTION%"=="1" (
    set BUILD_TARGET=chrome
    set AUTO_LAUNCH=0
    goto :EXECUTE_BUILD
)
if "%OPTION%"=="2" (
    set BUILD_TARGET=chrome
    set AUTO_LAUNCH=1
    goto :EXECUTE_BUILD
)
if "%OPTION%"=="3" (
    set BUILD_TARGET=mini_installer
    set AUTO_LAUNCH=0
    goto :EXECUTE_BUILD
)
if "%OPTION%"=="4" (
    goto :EXECUTE_DRY_RUN
)
if "%OPTION%"=="5" (
    goto :RELEASE_LOCK
)
if "%OPTION%"=="6" (
    goto :LAUNCH_DIRECT
)
if "%OPTION%"=="7" (
    exit /b 0
)

echo.
echo  [ERROR] Invalid option. Press any key to retry...
pause >nul
goto :MENU

:EXECUTE_BUILD
cls
color 0A
echo ==============================================================================
echo  STARTING BUILD: Target = %BUILD_TARGET%
echo ==============================================================================
echo  [INFO] Directory: %SRC_DIR%
echo  [INFO] Siso/Ninja compiling with AVX2 + Helium...
echo ==============================================================================
echo.

cd /d "%SRC_DIR%"
:: Close running instances so files (.pak / .dll) are not locked
taskkill /F /IM selenium.exe >nul 2>&1
taskkill /F /IM thorium.exe >nul 2>&1

:: Clear TARGET environment variable to prevent conflict with rust bindgen
set TARGET=

call C:\src\depot_tools\autoninja.bat -C out\thorium -local_jobs 8 -k 0 %BUILD_TARGET%

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ==============================================================================
    echo  [SUCCESS] Operation completed successfully!
    echo ==============================================================================
    if "%BUILD_TARGET%"=="mini_installer" (
        if exist "%OUT_DIR%\thorium_AVX2_mini_installer.exe" (
            copy /y "%OUT_DIR%\thorium_AVX2_mini_installer.exe" "%OUT_DIR%\selenium_AVX2_installer.exe" >nul 2>&1
        )
        echo  Installer generated at: %OUT_DIR%\selenium_AVX2_installer.exe
    ) else (
        echo  Executable ready at:    %OUT_DIR%\selenium.exe
    )
    echo ==============================================================================
    
    if "%AUTO_LAUNCH%"=="1" (
        echo.
        echo [INFO] Launching Selenium Browser automatically...
        cd /d "%OUT_DIR%"
        start "" "selenium.exe"
    )
) else (
    color 0C
    echo.
    echo ==============================================================================
    echo  [WARNING] Build stopped or encountered an error.
    echo  Please review the error messages above for details.
    echo ==============================================================================
)

echo.
if "%CMD_MODE%"=="1" exit /b 0
pause
goto :MENU

:EXECUTE_DRY_RUN
cls
color 0E
echo ==============================================================================
echo  QUICK VERIFICATION (DRY RUN): Checking build graph status...
echo ==============================================================================
cd /d "%SRC_DIR%"
call C:\src\depot_tools\autoninja.bat -C out\thorium -n chrome
echo.
if "%CMD_MODE%"=="1" exit /b 0
pause
goto :MENU

:RELEASE_LOCK
cls
color 0E
echo ==============================================================================
echo  RELEASING LOCKS AND ZOMBIE PROCESSES
echo ==============================================================================
echo  Closing hanging siso, ninja, clang-cl processes...
taskkill /F /IM siso.exe >nul 2>&1
taskkill /F /IM ninja.exe >nul 2>&1
if exist "%OUT_DIR%\.ninja_lock" (
    del /f /q "%OUT_DIR%\.ninja_lock"
    echo  [OK] .ninja_lock file removed.
) else (
    echo  [OK] No active .ninja_lock file found.
)
echo.
echo  Ready! Build environment is completely unlocked.
echo.
if "%CMD_MODE%"=="1" exit /b 0
pause
goto :MENU

:LAUNCH_DIRECT
cls
echo [INFO] Launching Selenium Browser...
cd /d "%OUT_DIR%"
if exist "selenium.exe" (
    start "" "selenium.exe"
) else (
    echo [ERROR] selenium.exe not found in %OUT_DIR%. Please build it first (Option 1).
    if "%CMD_MODE%"=="1" exit /b 1
    pause
)
if "%CMD_MODE%"=="1" exit /b 0
goto :MENU
