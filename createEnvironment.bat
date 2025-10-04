@echo off
setlocal enabledelayedexpansion

for /f "tokens=2 delims==" %%a in ('"wmic os get locale /value"') do set locale=%%a

where python >nul 2>nul
if errorlevel 1 (
    if "%locale%"=="0410" (
        echo Python non è installato o non è nel PATH.
    ) else if "%locale%"=="0407" (
        echo Python ist nicht installiert oder befindet sich nicht im PATH.
    ) else (
        echo Python is not installed or is not in the PATH.
    )
    exit /b 1
)

for /f "tokens=2 delims= " %%i in ('python --version 2^>nul') do set "pyver=%%i"
for /f "tokens=1,2 delims=." %%a in ("!pyver!") do (
    set "major=%%a"
    set "minor=%%b"
)

if !major! LSS 3 (
    if "%locale%"=="0410" (
        echo Python deve essere almeno alla versione 3.10. La versione rilevata è la !pyver!
    ) else if "%locale%"=="0407" (
        echo Python muss mindestens in Version 3.10 vorliegen. Erkannte Version: !pyver!
    ) else (
        echo Python must be at least version 3.10. The detected version is !pyver!
    )
    exit /b 1
)

if !major! EQU 3 if !minor! LSS 10 (
    if "%locale%"=="0410" (
        echo Python deve essere almeno alla versione 3.10. La versione rilevata è la !pyver!
    ) else if "%locale%"=="0407" (
        echo Python muss mindestens in Version 3.10 vorliegen. Erkannte Version: !pyver!
    ) else (
        echo Python must be at least version 3.10. The detected version is !pyver!
    )
    exit /b 1
)

python -m pip --version >nul 2>nul
if errorlevel 1 (
    if "%locale%"=="0410" (
        echo pip non è disponibile per la versione di Python usata in questo computer !pyver!. Assicurati che sia installato.
    ) else if "%locale%"=="0407" (
        echo pip ist für die auf diesem Computer verwendete Python-Version !pyver! nicht verfügbar. Bitte stelle sicher, dass es installiert ist.
    ) else (
        echo pip is not available for the Python version installed in this computer !pyver!. Make sure that it is installed.
    )
    exit /b 1
)

if not exist "rec_env" (
    if "%locale%"=="0410" (
        echo Creazione ambiente virtuale...
    ) else if "%locale%"=="0407" (
        echo Virtuelle Umgebung wird erstellt...
    ) else (
        echo Creating virtual environment...
    )
    python -m venv rec_env
)

if "%locale%"=="0410" (
    echo Attivazione ambiente...
) else if "%locale%"=="0407" (
    echo Umgebung wird aktiviert...
) else (
    echo Activating environment...
)
call rec_env\Scripts\activate.bat

if "%locale%"=="0410" (
    echo Installazione moduli...
) else if "%locale%"=="0407" (
    echo Module werden installiert...
) else (
    echo Installing modules...
)
pip install -r requirements.txt

setlocal

IF NOT EXIST "ffmpeg.exe" (
    if "%locale%"=="0410" (
        echo Estrazione di ffmpeg.exe da ffmpeg.zip...
    ) else if "%locale%"=="0407" (
        echo Extrahieren von ffmpeg.exe aus ffmpeg.zip...
    ) else (
        echo Extracting ffmpeg.exe from ffmpeg.zip...
    )

    IF EXIST "ffmpeg.zip" (
        powershell -Command "Expand-Archive -Path 'ffmpeg.zip' -DestinationPath '.'"
        if "%locale%"=="0410" (
            echo Estrazione completata.
        ) else if "%locale%"=="0407" (
            echo Extraktion abgeschlossen.
        ) else (
            echo Extraction completed.
        )
    ) ELSE (
        if "%locale%"=="0410" (
            echo ERRORE: ffmpeg.zip non trovato!
        ) else if "%locale%"=="0407" (
            echo FEHLER: ffmpeg.zip nicht gefunden!
        ) else (
            echo ERROR: ffmpeg.zip not found!
        )
    )
)

IF NOT EXIST "ffprobe.exe" (
    if "%locale%"=="0410" (
        echo Estrazione di ffprobe.exe da ffprobe.zip...
    ) else if "%locale%"=="0407" (
        echo Extrahieren von ffprobe.exe aus ffprobe.zip...
    ) else (
        echo Extracting ffprobe.exe from ffprobe.zip...
    )

    IF EXIST "ffprobe.zip" (
        powershell -Command "Expand-Archive -Path 'ffprobe.zip' -DestinationPath '.'"
        if "%locale%"=="0410" (
            echo Estrazione completata.
        ) else if "%locale%"=="0407" (
            echo Extraktion abgeschlossen.
        ) else (
            echo Extraction completed.
        )
    ) ELSE (
        if "%locale%"=="0410" (
            echo ERRORE: ffprobe.zip non trovato!
        ) else if "%locale%"=="0407" (
            echo FEHLER: ffprobe.zip nicht gefunden!
        ) else (
            echo ERROR: ffprobe.zip not found!
        )
    )
)

endlocal

setlocal

set "file=%~dp0sequenceNumber.txt"

if not exist "%file%" (
    echo 0 > "%file%"
)

for %%A in ("%file%") do (
    if %%~zA==0 (
        echo 0 > "%file%"
    )
)

endlocal

setlocal

set "file=%~dp0program.json"

if not exist "%file%" (
    echo [] > "%file%"
)

for %%A in ("%file%") do (
    if %%~zA==0 (
        echo [] > "%file%"
    )
)

endlocal

setlocal

set "file=%~dp0record.json"

if not exist "%file%" (
    echo [] > "%file%"
)

for %%A in ("%file%") do (
    if %%~zA==0 (
        echo [] > "%file%"
    )
)

endlocal

setlocal

set "file=%~dp0canali.json"

if not exist "%file%" (
    echo [] > "%file%"
)

for %%A in ("%file%") do (
    if %%~zA==0 (
        echo [] > "%file%"
    )
)

endlocal