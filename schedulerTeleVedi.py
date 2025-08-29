import sys
import schedule
import time
import os
import json
import psutil
import sys
from datetime import datetime
import subprocess

current_pid = os.getpid()
script_name = os.path.basename(__file__)

def is_script_running():
    global script_name
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        if 'python' in proc.info['name'] and script_name in ' '.join(proc.info['cmdline']) and proc.info["pid"] != current_pid and time.time() - proc.create_time() >= 60:
            return True
    return False

if is_script_running():
    sys.exit()
            
__location__ = os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__)))

def job():
    today = datetime.today()
    ora = today.strftime("%H:%M")
    with open(os.path.join(__location__, 'program.json'), 'r') as programFile:
        program = json.load(programFile)
        try:
            if not program:
                print("chiudo")
                sys.exit() # se non ci sono altre registrazioni programmate, terminare lo scheduler
        except Exception as e:
            print(e)
        for entry in program:
            data_inizio = datetime.strptime(entry["dataInizio"], "%d/%m/%Y")
            data_fine = datetime.strptime(entry["dataFine"], "%d/%m/%Y")
            # Esegui solo se è il momento giusto
            if today.day == data_inizio.day and today.month == data_inizio.month and today.year == data_inizio.year and entry["oraInizio"] == ora and entry["ffmpegPid"] == "0":
                cmd = [
                    os.path.join(__location__, "php", "php.exe"),
                    "-f",
                    os.path.join(__location__, "recordProgrammedStream.php"),
                    entry["canale"].replace(" ", "_"),
                    entry["path"],
                    entry["id"],
                    __location__
                ]
                subprocess.run(cmd)
                            
            elif today.day == data_fine.day and today.month == data_fine.month and today.year == data_fine.year and entry["oraFine"] == ora:
                cmd = [
                    os.path.join(__location__, "php", "php.exe"),
                    "-f",
                    os.path.join(__location__, "stopRecordingProgrammed.php"),
                    entry["id"],
                    __location__
                ]
                subprocess.run(cmd)

try:
    schedule.every(1).minutes.do(job)
except Exception as e:
    print(e)

while True:
    schedule.run_pending()
    time.sleep(1)