@echo off
setlocal EnableDelayedExpansion
set "startup_dir=%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup"
set "auto_start_script=%startup_dir%\AutoStartScriptTeleVedi.vbs"

if exist "%auto_start_script%" (
    del "%auto_start_script%"
)

for /f "usebackq tokens=*" %%a in (`powershell -NoProfile -Command "'{0:x4}' -f (Get-Culture).LCID"`) do set locale=%%a
if "%locale%"=="0410" (
    echo TeleVedi - Registratore disinstallato con successo.
) else if "%locale%"=="0407" (
    echo TeleVedi – Recorder erfolgreich deinstalliert.
) else (
    echo TeleVedi - Recorder successfully uninstalled.
)

endlocal
pause