@echo off
setlocal EnableDelayedExpansion

rem ===– Arguments –===
set "PKG=%~f1"
set "TARGETDIR=%~f2"
set "TARGETEXE=%TARGETDIR%\BazaarBuddy.exe"
set "BACKUP=%TARGETDIR%\BazaarBuddy.old"

rem ===– Sanity checks –===
if not exist "%PKG%" (
    echo ERROR: Source file not found: "%PKG%"
    exit /b 2
)
if not exist "%TARGETDIR%" (
    echo ERROR: Target directory not found: "%TARGETDIR%"
    exit /b 3
)

echo Waiting for BazaarBuddy.exe to close...
for /l %%# in () do (
    tasklist /FI "IMAGENAME eq BazaarBuddy.exe" /FI "STATUS eq running" | ^
        findstr /I /C:"BazaarBuddy.exe" >nul || goto :closed
    timeout /t 1 >nul
)
:closed

echo Replacing old version...
if exist "%TARGETEXE%" (
    move /Y "%TARGETEXE%" "%BACKUP%" >nul || (
        echo ERROR: Could not rename old EXE – still locked?
        exit /b 4
    )
)

copy /Y "%PKG%" "%TARGETEXE%" >nul || (
    echo ERROR: Copy failed – check the paths and file locks.
    exit /b 5
)
del "%PKG%" >nul

echo Relaunching...
start "" "%TARGETEXE%"
endlocal
