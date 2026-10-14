@echo off
setlocal EnableDelayedExpansion

call createEnvironment.bat

for /f "usebackq tokens=*" %%a in (`powershell -NoProfile -Command "'{0:x4}' -f (Get-Culture).LCID"`) do set locale=%%a

:: Italiano
if "%locale%"=="0410" (
    echo Avvio del programma...
    echo ATTENZIONE: Non chiudere questa finestra se è ancora aperto TeleVedi - Registratore!
) else if "%locale%"=="0407" (
    echo Programmstart...
    echo ACHTUNG: Schließen Sie dieses Fenster nicht, wenn TeleVedi – Recorder noch geöffnet ist!
) else (
    echo Starting the program...
    echo WARNING: Do not close this window if TeleVedi - Recorder is still running!
)
python Registratore.py
endlocal
exit