@echo off
setlocal EnableDelayedExpansion
set "startup_dir=%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup"
set "auto_start_script=%startup_dir%\AutoStartScriptTeleVedi.vbs"

if exist "%auto_start_script%" (
    del "%auto_start_script%"
)

for /f "tokens=2 delims==" %%a in ('"wmic os get locale /value"') do set locale=%%a
if "%locale%"=="0410" (
    echo TeleVedi - Registratore disinstallato con successo.
) else if "%locale%"=="0407" (
    echo TeleVedi – Recorder erfolgreich deinstalliert.
) else (
    echo TeleVedi - Recorder successfully uninstalled.
)

endlocal
pause