@echo off
rem ------------------------------------------------------------
rem Bazaar Buddy – Windows self‑updater
rem Invoked from Python as:   windows_update.bat <download_url>
rem ------------------------------------------------------------
setlocal enableextensions enabledelayedexpansion

:: --- 1. Validate input ------------------------------------------------------
if "%~1"=="" (
    echo [Updater] ERROR: No download URL supplied.
    goto :eof
)
set "DOWNLOAD_URL=%~1"

:: --- 2. Figure out important paths -----------------------------------------
rem Folder that contains this .bat
set "SCRIPT_DIR=%~dp0"
rem Resolve install folder (one level above SCRIPT_DIR)
for %%I in ("%SCRIPT_DIR%..") do set "INSTALL_DIR=%%~fI"

:: --- 3. Create temp workspace ----------------------------------------------
set "TMP_DIR=%TEMP%\BazaarBuddy_Update"
if exist "%TMP_DIR%" rmdir /s /q "%TMP_DIR%"
mkdir "%TMP_DIR%"

echo [Updater] Downloading update from:
echo   %DOWNLOAD_URL%
:: PowerShell download (fallback to curl if PS fails)
powershell -NoLogo -NoProfile -Command ^
  "Invoke-WebRequest -Uri '%DOWNLOAD_URL%' -OutFile '%TMP_DIR%\BazaarBuddy_new.exe'" ^
  2>nul || ( ^
      echo [Updater] PowerShell unavailable, trying curl… & ^
      curl -L "%DOWNLOAD_URL%" -o "%TMP_DIR%\BazaarBuddy_new.exe" ^
  )

if not exist "%TMP_DIR%\BazaarBuddy_new.exe" (
    echo [Updater] ERROR: Download failed.
    goto :CLEANUP
)

:: --- 4. Give the original app time to exit ---------------------------------
timeout /t 2 >nul

:: --- 5. Replace old binary --------------------------------------------------
if exist "%INSTALL_DIR%\BazaarBuddy.exe" (
    move /y "%INSTALL_DIR%\BazaarBuddy.exe" "%INSTALL_DIR%\BazaarBuddy_old.exe" >nul
)
move /y "%TMP_DIR%\BazaarBuddy_new.exe" "%INSTALL_DIR%\BazaarBuddy.exe"

:: --- 6. Clean‑up and relaunch ----------------------------------------------
echo [Updater] Update installed successfully.
start "" "%INSTALL_DIR%\BazaarBuddy.exe"

:CLEANUP
if exist "%TMP_DIR%" rmdir /s /q "%TMP_DIR%"
endlocal
exit /b 0
