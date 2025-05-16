@echo on
setlocal EnableExtensions EnableDelayedExpansion
SLEEP 10
rem ---------------------------------------------------------------
rem Parameters (supplied by main.py)
rem   %1  = full path to the freshly‑downloaded package (BazaarBuddy‑x.y.z.exe)
rem   %2  = directory that already contains BazaarBuddy.exe
rem ---------------------------------------------------------------
set "PKG=%~f1"
set "TARGETDIR=%~f2"
set "TARGETEXE=%TARGETDIR%\BazaarBuddy.exe"
set "BACKUP=%TARGETDIR%\BazaarBuddy.old"
rem ---- basic sanity checks --------------------------------------
if not exist "%PKG%" (
    echo ERROR: Source file not found: "%PKG%"
    exit /b 2
)
if not exist "%TARGETDIR%" (
    echo ERROR: Target directory not found: "%TARGETDIR%"
    exit /b 3
)

echo Waiting for BazaarBuddy.exe to exit...

rem =================================================================
rem :wait_loop
rem Instead of TASKLIST we simply *try* to rename the file.
rem MOVE will fail (errorlevel 1) as long as some process still has
rem the binary open.  When the rename succeeds the file is free and we
rem can finish the update.
rem =================================================================
:wait_loop
if exist "%TARGETEXE%" move /y "%TARGETEXE%" "%BACKUP%" >nul 2>&1
if errorlevel 1 (
    call :sleep 1
    goto :wait_loop
)

rem ---- copy the new build in place --------------------------------
copy /y /v "%PKG%" "%TARGETEXE%" >nul 2>&1
if errorlevel 1 (
    echo ERROR: Copy failed – file still locked?
    move /y "%BACKUP%" "%TARGETEXE%" >nul 2>&1
    exit /b 5
)

del /q "%PKG%" 2>nul
call :sleep 2

echo Relaunching …
start "" /d "%TARGETDIR%" "%TARGETEXE%"

start "" cmd /c "ping 127.0.0.1 -n 2 >nul & del /f /q "%BACKUP%""
endlocal
exit /b 0

rem ----------------------------------------------------------------
rem :sleep  <seconds>
rem Minimal “sleep” routine without external executables.
rem Each outer loop ≈ 1 s on most PCs; adjust the inner count if you
rem need finer accuracy.
rem ----------------------------------------------------------------
:sleep
set /a _secs=%~1
if %_secs% lss 1 set /a _secs=1
for /l %%S in (1,1,%_secs%) do (
    for /l %%i in (1,1,30) do rem nop
)
exit /b
