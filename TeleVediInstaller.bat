@echo off
setlocal enabledelayedexpansion

cd /d "%~dp0"

for /f "tokens=2 delims==" %%a in ('"wmic os get locale /value"') do set locale=%%a

:: Verifica se il batch è stato avviato come amministratore
powershell -Command "if (-not ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) { exit 1 }"
if %errorlevel% neq 0 (
    :: Non è in modalità admin, rilancia se stesso con privilegi elevati
    powershell -Command "Start-Process '%~f0' -Verb runAs"
    exit /b
)

:: Italiano
if "%locale%"=="0410" (
    echo Privilegi amministratore confermati.
) else if "%locale%"=="0407" (
    echo Administratorrechte bestätigt.
) else (
    echo Admin rights confirmed.
)

set "dllPath=%SystemRoot%\System32\vcruntime140.dll"
set "minVersion=14.40.0.0"
set "downloadUrl=https://aka.ms/vs/17/release/vc_redist.x64.exe"
set "installer=VC_redist.x64.exe"

if "%locale%"=="0410" (
    echo Controllo della libreria vcruntime140.dll...
) else if "%locale%"=="0407" (
    echo Überprüfung der Bibliothek vcruntime140.dll...
) else (
    echo vcruntime140.dll library check...
)

:: Verifica se il file esiste
if exist "%dllPath%" (
    for /f %%v in ('powershell -Command "(Get-Item '%dllPath%').VersionInfo.FileVersion"') do (
        if "%locale%"=="0410" (
            echo Versione rilevata: %%v
        ) else if "%locale%"=="0407" (
            echo Erkannte Version: %%v
        ) else (
            echo Detected version: %%v
        )
        set "currentVersion=%%v"
    )
) else (
    if "%locale%"=="0410" (
        echo Il file vcruntime140.dll non è presente.
    ) else if "%locale%"=="0407" (
        echo Die Datei vcruntime140.dll ist nicht vorhanden.
    ) else (
        echo vcruntime140.dll does not exist.
    )
    set "currentVersion=0.0.0.0"
)
:: Confronto versioni
:: Separazione in componenti
for /f "tokens=1-4 delims=." %%a in ("%currentVersion%") do (
    set "curVer1=00000%%a"
    set "curVer2=00000%%b"
    set "curVer3=00000%%c"
    set "curVer4=00000%%d"
)
for /f "tokens=1-4 delims=." %%a in ("%minVersion%") do (
    set "minVer1=00000%%a"
    set "minVer2=00000%%b"
    set "minVer3=00000%%c"
    set "minVer4=00000%%d"
)

:: Prende solo le ultime 5 cifre per il confronto numerico
set "curVer1=!curVer1:~-5!"
set "curVer2=!curVer2:~-5!"
set "curVer3=!curVer3:~-5!"
set "curVer4=!curVer4:~-5!"

set "minVer1=!minVer1:~-5!"
set "minVer2=!minVer2:~-5!"
set "minVer3=!minVer3:~-5!"
set "minVer4=!minVer4:~-5!"

set "isCurrentVersionGreaterOrEqual=false"

if !curVer1! GTR !minVer1! (
    set "isCurrentVersionGreaterOrEqual=true"
) else if !curVer1! EQU !minVer1! (
    if !curVer2! GTR !minVer2! (
        set "isCurrentVersionGreaterOrEqual=true"
    ) else if !curVer2! EQU !minVer2! (
        if !curVer3! GTR !minVer3! (
            set "isCurrentVersionGreaterOrEqual=true"
        ) else if !curVer3! EQU !minVer3! (
            if !curVer4! GEQ !minVer4! (
                set "isCurrentVersionGreaterOrEqual=true"
            )
        )
    )
)

if "%isCurrentVersionGreaterOrEqual%"=="false" (
    if "%locale%"=="0410" (
        echo Versione insufficiente. Scarico e installo Visual C++ Redistributable...
    ) else if "%locale%"=="0407" (
        echo Unzureichende Version. Visual C++ Redistributable wird heruntergeladen und installiert...
    ) else (
        echo Insufficient version. Downloading and installing Visual C++ Redistributable...
    )

    :: Scarica il file
    powershell -Command "Invoke-WebRequest -Uri '%downloadUrl%' -OutFile '%installer%'"

    if exist "%installer%" (
        if "%locale%"=="0410" (
            echo Installer scaricato con successo.
            echo Avvio dell'installer...
        ) else if "%locale%"=="0407" (
            echo Installer erfolgreich heruntergeladen.
            echo Installer wird gestartet...
        ) else (
            echo Installer successfully downloaded.
            echo Starting the installer...
        )
        start /wait "" "%installer%" /install /quiet /norestart
    ) else (
        if "%locale%"=="0410" (
            echo Errore: il file non è stato scaricato correttamente.
        ) else if "%locale%"=="0407" (
            echo Fehler: Die Datei wurde nicht korrekt heruntergeladen.
        ) else (
            echo Error: the file was not downloaded correctly.
        )
        exit
    )

    if "%locale%"=="0410" (
        echo Installazione completata.
        :: Cancella l'installer
        echo Pulizia...
    ) else if "%locale%"=="0407" (
        echo Installation abgeschlossen.
        :: Installer löschen
        echo Aufräumen...
    ) else (
        echo Install completed.
        :: Delete the installer
        echo Cleaning...
    )
    del "%installer%"
) else (
    if "%locale%"=="0410" (
        echo Versione compatibile già installata.
    ) else if "%locale%"=="0407" (
        echo Kompatible Version bereits installiert.
    ) else (
        echo Compatible version already installed.
    )
)

set "target=startRegistratore.bat"
set "shortcut=TeleVedi.lnk"
set "icon=img\icona.ico"
set "folder=%~dp0"

powershell -Command "$s=(New-Object -ComObject WScript.Shell).CreateShortcut('%folder%%shortcut%'); $s.TargetPath='%folder%%target%'; $s.WorkingDirectory='%folder%'; $s.IconLocation='%folder%%icon%'; $s.Save()"

if "%locale%"=="0410" (
    echo Collegamento TeleVedi creato con successo!
) else if "%locale%"=="0407" (
    echo TeleVedi-Verknüpfung erfolgreich erstellt!
) else (
    echo Shortcut to TeleVedi successfully created!
)

call createEnvironment.bat

python "%~dp0installScheduler.py"

endlocal
pause