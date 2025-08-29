import os
import sys
import locale

try:
    locale.setlocale(locale.LC_ALL, '')
    lang_code, encoding = locale.getlocale()
    if lang_code is None:
        lang_code = 'en_US'
except Exception as e:
    lang_code = 'en_US'
    encoding = 'UTF-8'
lang = lang_code[:2].lower() if lang_code else 'en'

def get_python_path():
    return sys.executable

def register_autostart(script_path):
    startup_dir = os.path.join(os.getenv('APPDATA'), 'Microsoft', 'Windows', 'Start Menu', 'Programs', 'Startup')
    os.makedirs(startup_dir, exist_ok=True)

    vbs_path = os.path.join(startup_dir, 'AutoStartScriptTeleVedi.vbs')
    current_dir = os.path.dirname(os.path.abspath(__file__))
    target_dir = os.path.join(current_dir, 'rec_env', 'Scripts')
    python_exe = os.path.join(target_dir, 'python.exe')

    with open(vbs_path, 'w', encoding='utf-8') as f:
        f.write(f'Set fso = CreateObject("Scripting.FileSystemObject")\n')
        f.write(f'If Not fso.FileExists("{python_exe}") Then\n')
        if lang == 'it':
            f.write(f'    MsgBox "Impossibile trovare {python_exe}. Eseguire TeleVediInstaller.bat per correggere l\'errore."\n')
        else:
            f.write(f'    MsgBox "Cannot find {python_exe}. Run TeleVediInstaller.bat to fix the error."\n')
        f.write(f'    WScript.Quit\n')
        f.write(f'End If\n')
        f.write(f'If Not fso.FileExists("{script_path}") Then\n')
        if lang == 'it':
            f.write(f'    MsgBox "Impossibile trovare {script_path}. Eseguire TeleVediInstaller.bat per correggere l\'errore."\n')
        else:
            f.write(f'    MsgBox "Cannot find {script_path}. Run TeleVediInstaller.bat to fix the error."\n')
        f.write(f'    WScript.Quit\n')
        f.write(f'End If\n')
        f.write(f'Set WshShell = CreateObject("WScript.Shell")\n')
        f.write(f'WshShell.Run """{python_exe}"" ""{script_path}""", 0, False\n')

    if lang == 'it':
        print(f"Script registrato per l'avvio automatico su Windows (silenzioso): {vbs_path}")
    else:
        print(f"Script registered for automatic startup on Windows (silent mode): {vbs_path}")

def main():
    script_path = os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__))) + "\\schedulerTeleVedi.py"
    register_autostart(script_path)
    if lang == 'it':
        input("Fine")
    else:
        input("Done")

if __name__ == "__main__":
    main()