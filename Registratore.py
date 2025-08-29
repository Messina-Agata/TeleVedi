import os
import subprocess
import sys
import tkinter as tk
from tkinter import filedialog, ttk
from tkcalendar import DateEntry
from tkinter import ttk
import json
from datetime import datetime
from tkinter import messagebox
from tkinter import PhotoImage
from tkinter import scrolledtext
from subprocess import Popen
import time
import psutil
import requests
from concurrent.futures import ThreadPoolExecutor
import locale
import gettext
import webbrowser

python_base = sys.base_prefix
tcl_path = os.path.join(python_base, "tcl", "tcl8.6")
os.environ["TCL_LIBRARY"] = tcl_path

current_pid = os.getpid()
script_name = os.path.basename(__file__)

try:
    locale.setlocale(locale.LC_ALL, '')
    lang_code, encoding = locale.getlocale()
    if lang_code is None:
        lang_code = 'en_US'
except Exception as e:
    lang_code = 'en_US'
    encoding = 'UTF-8'
lang = lang_code[:2].lower() if lang_code else 'en'
localedir = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'locales')
try:
    translation = gettext.translation('messages', localedir, languages=[lang])
    translation.install()
    _ = translation.gettext
except FileNotFoundError:
    gettext.install('messages')

def is_script_running():
    global script_name
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        if 'python' in proc.info['name'] and script_name in ' '.join(proc.info['cmdline']) and proc.info["pid"] != current_pid and time.time() - proc.create_time() >= 2:
            return True
    return False

if is_script_running():
    messagebox.showinfo(_("TeleVedi - Registratore già in esecuzione"), _("Un'istanza di TeleVedi - Registratore è già avviata"))
    sys.exit()

__location__ = os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__)))
values = []
channelOk = False
filePathOk = False
startDateOk = False
endDateOk = False
sequenceNumber = "0"
FLAG_FILE = "first_run.flag"
with open(os.path.join(__location__, 'sequenceNumber.txt'), 'r') as sn:
    sequenceNumber = sn.read()

window = tk.Tk()
window.geometry("1150x620")
window.title(_("TeleVedi - Registratore"))
window.resizable(False, False)
window.configure(background="white")
icon_path = os.path.join(os.path.dirname(__file__), "img", "icona.png")
icon = PhotoImage(file=icon_path)
window.iconphoto(True, icon)
logo_path = os.path.join(os.path.dirname(__file__), "img", "logo_small.png")
logo = PhotoImage(file=logo_path)

def checkIfOld(jsonFile):
    running = False
    with open(os.path.join(__location__, jsonFile), 'r') as file:
        data = json.load(file)
    for idx, entry in enumerate(data):
        running = False
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            if proc.info["pid"] == entry["ffmpegPid"]:
                running = True
                break
        if entry["ffmpegPid"] != '0' and running == False:
            data.pop(idx)
            with open(os.path.join(__location__, jsonFile), "w") as f:
                json.dump(data, f, indent=4)

def recTypeChanged(event):
    if (input_rectype.get() == _("Programmato")):
        rec_button.grid_remove()
        viewRec_button.grid_remove()
        label_start.grid(row = 3, column = 0, padx = 10, pady = 10, sticky = "WE")
        startDay.grid(row = 4, column = 0, sticky="WE", padx = 15, pady = 10)
        startTimeFrame.grid(row = 4, column = 1, sticky="WE", padx = 15, pady = 10)
        label_end.grid(row = 5, column = 0, padx = 10, pady = 10, sticky = "WE")
        endDay.grid(row = 6, column = 0, sticky="WE", padx = 15, pady = 10)
        endTimeFrame.grid(row = 6, column = 1, sticky="WE", padx = 15, pady = 10)
        program_button.grid(row = 7, column = 1, padx = 10, pady = 10, sticky = "WE")
        history_button.grid(row = 8, column = 1, padx = 10, pady = 10, sticky = "WE")
    else:
        rec_button.grid(row = 3, column = 1, padx = 10, pady = 10, sticky = "WE")
        viewRec_button.grid(row = 4, column = 1, padx = 10, pady = 10, sticky = "WE")
       
        label_start.grid_remove()
        startDay.grid_remove()
        startTimeFrame.grid_remove()
        label_end.grid_remove()
        endDay.grid_remove()
        endTimeFrame.grid_remove()
        program_button.grid_remove()
        history_button.grid_remove()

def getRecPath():
    global file_path
    file_path = filedialog.askdirectory()
    global filePathOk
    if file_path != '':
        filePathOk = True
    else:
        filePathOk = False
    global label_filePath
    label_filePath.delete(0, tk.END)
    label_filePath.insert(0, file_path)
    enable_recording()
    enableProgrammedRecording()

def record():
    global sequenceNumber
    channelKey = nn.get()
    flusso = ''
    data = carica_canali()
    for entry in data:
        if entry["nome"] == channelKey:
            flusso = entry["flusso"]
            break

    if flusso == '':
        return
    cmd = "\"" + __location__ + "\\php\\php.exe\" -f requestStream.php \"" + flusso + "\""
    try:
        flusso = subprocess.check_output(cmd, shell = True, text = True)
    except subprocess.CalledProcessError as e:
        print("Error executing command: {e}")
        return

    if (not availability_check(flusso)):
        answer = messagebox.askyesnocancel(_("Flusso non valido", "Il canale selezionato è al momento non raggiungibile, pertanto la registrazione potrebbe non andare a buon fine. Avviare comunque la registrazione?"))
        if (not answer):
            return
        
    with open(os.path.join(__location__, 'record.json'), 'r') as programFile:
        program = json.load(programFile)

    newEntry = json.loads(json.dumps({
        "id": sequenceNumber,
        "canale": channelKey,
        "ffmpegPid": "0",
        "path": file_path
    }))

    program.append(newEntry)

    with open(os.path.join(__location__, 'record.json'), 'w') as f:
        json.dump(program, f)

    cmd = "\"" + __location__ + "\\php\\php.exe\" -f recordStream.php \"" + flusso + "\" \"" + channelKey + "\" \"" + file_path + "\" \"" + __location__ + "\" " + sequenceNumber
    try:
        p = Popen(cmd, shell = True)
        time.sleep(4)
        p.terminate()
    except subprocess.CalledProcessError as e:
        print("Error executing command: {e}")
        return

    messagebox.showinfo(_("Avvia registrazione"), _("Registrazione avviata"))

    input_channel.set('')
    label_filePath.delete(0, tk.END)

    snInt = int(sequenceNumber) + 1
    if snInt == 2147483647:
        snInt = 0

    sequenceNumber = str(snInt)
    with open(os.path.join(__location__, 'sequenceNumber.txt'), 'w') as sn:
        sn.write(sequenceNumber)

def programRec():
    channelKey = nn.get()
    flusso = ''
    data = carica_canali()
    for entry in data:
        if entry["nome"] == channelKey:
            flusso = entry["flusso"]
            break

    if flusso == '':
        return
    
    if (not availability_check(flusso)):
        answer = messagebox.askyesnocancel(_("Flusso non valido"), _("Il canale selezionato è al momento non raggiungibile, pertanto la registrazione potrebbe non andare a buon fine. Programmare comunque la registrazione?"))
        if (not answer):
            return
    
    oraInizio = str(start_nh.get()) + ":" + str(start_nm.get())
    oraFine =  str(end_nh.get()) + ":" + str(end_nm.get())
    global sequenceNumber
    flussoCoded = flusso.replace("&", "%26")

    with open(os.path.join(__location__, 'program.json'), 'r') as programFile:
        program = json.load(programFile)

    newEntry = json.loads(json.dumps({
        "id": sequenceNumber,
        "canale": channelKey,
        "dataInizio": sds.get(),
        "oraInizio": oraInizio,
        "dataFine": eds.get(),
        "oraFine": oraFine,
        "ffmpegPid": "0",
        "flusso": flussoCoded,
        "path": file_path
    }))

    program.append(newEntry)

    with open(os.path.join(__location__, 'program.json'), 'w') as f:
        json.dump(program, f)

    python = os.path.join(os.path.dirname(sys.executable), 'python.exe')
    script_path = os.path.abspath('schedulerTeleVedi.py')
    subprocess.Popen(
        [python, script_path],
        creationflags=subprocess.CREATE_NO_WINDOW
    )
    
    messagebox.showinfo(_("Programma registrazione"), _("Registrazione programmata correttamente"))

    input_channel.set('')
    label_filePath.delete(0, tk.END)
    startDay.delete(0, tk.END)
    startHour.delete(0, tk.END)
    startMinute.delete(0, tk.END)
    endDay.delete(0, tk.END)
    endHour.delete(0, tk.END)
    endMinute.delete(0, tk.END)

    snInt = int(sequenceNumber) + 1
    if snInt == 2147483647:
        snInt = 0

    sequenceNumber = str(snInt)
    with open(os.path.join(__location__, 'sequenceNumber.txt'), 'w') as sn:
        sn.write(sequenceNumber)

def viewLiveRecs():
    checkIfOld('record.json')
    with open(os.path.join(__location__, 'record.json'), 'r') as file:
        dataR = json.load(file)
    if not dataR:
        messagebox.showinfo(_("Registrazioni in corso"), _("Nessuna registrazione in corso"))
        return
    
    xR = window.winfo_x()
    yR = window.winfo_y()
    wR = window.winfo_width()
    hR = window.winfo_height()

    finestraR = tk.Toplevel(window)
    finestraR.geometry(f"900x400+{xR + wR//2 - 450}+{yR + hR//2 - 200}")

    finestraR.title(_("Registrazioni in corso"))
    finestraR.configure(background="white")

    canvasR = tk.Canvas(finestraR, bg="white")
    v_scrollR = ttk.Scrollbar(finestraR, orient="vertical", command=canvasR.yview)
    h_scrollR = ttk.Scrollbar(finestraR, orient="horizontal", command=canvasR.xview)

    canvasR.configure(yscrollcommand=v_scrollR.set, xscrollcommand=h_scrollR.set)

    v_scrollR.pack(side="right", fill="y")
    h_scrollR.pack(side="bottom", fill="x")
    canvasR.pack(side="left", fill="both", expand=True)

    scrollable_frameR = ttk.Frame(canvasR, padding=10, relief="ridge", style="Bianco.TFrame")
    canvasR.create_window((0, 0), window=scrollable_frameR, anchor="nw")

    def on_configureR(event):
        canvasR.configure(scrollregion=canvasR.bbox("all"))

    scrollable_frameR.bind("<Configure>", on_configureR)

    def on_mousewheelR(event):
        bboxR = canvasR.bbox("all")
        if bboxR:
            content_heightR = bboxR[3] - bboxR[1]
            canvas_heightR = canvasR.winfo_height()
            if content_heightR > canvas_heightR:
                canvasR.yview_scroll(int(-1*(event.delta/120)), "units")

    def on_close_finestraR():
        canvasR.unbind_all("<MouseWheel>")
        finestraR.destroy()  

    canvasR.bind("<Enter>", lambda e: canvasR.bind_all("<MouseWheel>", on_mousewheelR))
    canvasR.bind("<Leave>", lambda e: canvasR.unbind_all("<MouseWheel>"))

    for indx, entryR in enumerate(dataR):
        frame_contenitoreR = ttk.Frame(scrollable_frameR, padding=10, relief="ridge", style="Bianco.TFrame")
        frame_contenitoreR.pack(fill="x", padx=10, pady=5)
        frame_labelR = ttk.Frame(frame_contenitoreR, style="Bianco.TFrame")
        frame_labelR.pack(side="left", fill="both", expand=True, padx = 15)
        frame_bottoneR = ttk.Frame(frame_contenitoreR, style="Bianco.TFrame")
        frame_bottoneR.pack(side="right")

        lblR = ttk.Label(frame_labelR, text=_("Canale: %s") % entryR["canale"], anchor="w", background="white")
        lblR.pack(anchor="w")
        lblR = ttk.Label(frame_labelR, text=f"Path download: {entryR["path"]}", anchor="w", background="white")
        lblR.pack(anchor="w")

        def crea_callbackR(id):
            stopRecording(id)
            time.sleep(1)
            canvasR.unbind_all("<MouseWheel>")
            finestraR.destroy()
            viewLiveRecs()

        btnR = ttk.Button(frame_bottoneR, text=_("Ferma registrazione"), command=lambda id=entryR["id"]: crea_callbackR(id))
        btnR.pack()
    finestraR.protocol("WM_DELETE_WINDOW", on_close_finestraR)

def viewRecs():
    checkIfOld('program.json')
    with open(os.path.join(__location__, 'program.json'), 'r') as file:
        data = json.load(file)
    if not data:
        messagebox.showinfo(_("Registrazioni programmate"), _("Non ci sono registrazioni programmate"))
        return
    
    x = window.winfo_x()
    y = window.winfo_y()
    w = window.winfo_width()
    h = window.winfo_height()

    finestra = tk.Toplevel(window)
    finestra.geometry(f"900x400+{x + w//2 - 450}+{y + h//2 - 200}")

    finestra.title(_("Registrazioni programmate"))
    finestra.configure(background="white")

    canvas = tk.Canvas(finestra, bg="white")
    v_scroll = ttk.Scrollbar(finestra, orient="vertical", command=canvas.yview)
    h_scroll = ttk.Scrollbar(finestra, orient="horizontal", command=canvas.xview)

    canvas.configure(yscrollcommand=v_scroll.set, xscrollcommand=h_scroll.set)

    v_scroll.pack(side="right", fill="y")
    h_scroll.pack(side="bottom", fill="x")
    canvas.pack(side="left", fill="both", expand=True)

    scrollable_frame = ttk.Frame(canvas, padding=10, relief="ridge", style="Bianco.TFrame")
    canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")

    def on_configure(event):
        canvas.configure(scrollregion=canvas.bbox("all"))

    scrollable_frame.bind("<Configure>", on_configure)

    def on_mousewheel(event):
        bbox = canvas.bbox("all")
        if bbox:
            content_height = bbox[3] - bbox[1]
            canvas_height = canvas.winfo_height()
            if content_height > canvas_height:
                canvas.yview_scroll(int(-1*(event.delta/120)), "units")

    def on_close_finestra():
        canvas.unbind_all("<MouseWheel>")
        finestra.destroy()  

    canvas.bind("<Enter>", lambda e: canvas.bind_all("<MouseWheel>", on_mousewheel))
    canvas.bind("<Leave>", lambda e: canvas.unbind_all("<MouseWheel>"))
    finestra.protocol("WM_DELETE_WINDOW", on_close_finestra)

    for idx, entry in enumerate(data):
        frame_contenitore = ttk.Frame(scrollable_frame, padding=10, relief="ridge", style="Bianco.TFrame")
        frame_contenitore.pack(fill="x", padx=10, pady=5)
        frame_label = ttk.Frame(frame_contenitore, style="Bianco.TFrame")
        frame_label.pack(side="left", fill="both", expand=True)
        frame_bottone = ttk.Frame(frame_contenitore, style="Bianco.TFrame")
        frame_bottone.pack(side="right")

        lbl = ttk.Label(frame_label, text=_("Canale: %s") % entry["canale"], anchor="w", background="white")
        lbl.pack(anchor="w")
        lbl = ttk.Label(frame_label, text=_("Data inizio: %s") % entry["dataInizio"], anchor="w", background="white")
        lbl.pack(anchor="w")
        lbl = ttk.Label(frame_label, text=_("Ora inizio: %s") % entry["oraInizio"], anchor="w", background="white")
        lbl.pack(anchor="w")
        lbl = ttk.Label(frame_label, text=_("Data fine: %s") % entry["dataFine"], anchor="w", background="white")
        lbl.pack(anchor="w")
        lbl = ttk.Label(frame_label, text=_("Ora fine: %s") % entry["oraFine"], anchor="w", background="white")
        lbl.pack(anchor="w")
        lbl = ttk.Label(frame_label, text=f"Path download: {entry["path"]}", anchor="w", background="white")
        lbl.pack(anchor="w")

        def crea_callback(chiave_locale):
            def rimuovi():
                conferma = messagebox.askyesno(_("Conferma"), _("Vuoi davvero cancellare la registrazione programmata?"), parent=finestra)
                if conferma:
                    data.pop(chiave_locale)
                    with open(os.path.join(__location__, 'program.json'), "w") as f:
                        json.dump(data, f, indent=4)
                    canvas.unbind_all("<MouseWheel>")
                    finestra.destroy()
                    viewRecs()
            return rimuovi

        btn = ttk.Button(frame_bottone, text=_("Cancella"), command=crea_callback(idx))
        btn.pack()

def stopRecording(sequenceNumber):
    cmd = "\"" + __location__ + "\\php\\php.exe\" -f stopRecording.php \"" + __location__ + "\" " + sequenceNumber
    try:
        subprocess.check_output(cmd, shell = True, text = True)
    except subprocess.CalledProcessError as e:
        print("Error executing command: {e}")
        return

def enable_recording():
    if channelOk == True and filePathOk == True:
        rec_button["state"] = "active"
    else:
        rec_button["state"] = "disabled"

def on_change(*args):          
    global channelOk
    channelOk = False

    canali = carica_canali()
    values = [c["nome"] for c in canali]
    if nn.get() in values:
        channelOk = True

    enable_recording()
    enableProgrammedRecording()

def enableProgrammedRecording():
    if channelOk == True and filePathOk == True and startDateOk == True and endDateOk == True:
        program_button["state"] = "active"
    else:
        program_button["state"] = "disabled"

def checkStartDate(*args):
    global startDateOk
    selectedDate = sds.get()
    if selectedDate == '' or start_nh.get() == '' or start_nm.get() == '' or start_nh.get() not in startHourValues or start_nm.get() not in startMinuteValues:
        startDateOk = False
        return
    currentDateTime = datetime.today().strftime("%d/%m/%Y %H:%M:%S")
    selectedDateTime = selectedDate + " " + start_nh.get() + ":" + start_nm.get() + ":00"
    formato = '%d/%m/%Y %H:%M:%S'
    dt1 = datetime.strptime(selectedDateTime, formato)
    dt2 = datetime.strptime(currentDateTime, formato)
    if (dt1 < dt2):
        startDateOk = False
    else:
        startDateOk = True
    checkEndDate()

def checkEndDate(*args):
    global endDateOk
    selectedDate = eds.get()
    if selectedDate == '' or end_nh.get() == '' or end_nm.get() == '' or end_nh.get() not in endHourValues or end_nm.get() not in endMinuteValues:
        endDateOk = False
        return
    if startDateOk == True:
        startDateTime = sds.get() + " " + start_nh.get() + ":" + start_nm.get() + ":00"
        selectedDateTime = selectedDate + " " + end_nh.get() + ":" + end_nm.get() + ":00"
        formato = '%d/%m/%Y %H:%M:%S'
        dt1 = datetime.strptime(selectedDateTime, formato)
        dt2 = datetime.strptime(startDateTime, formato)
        if (dt1 <= dt2):
            endDateOk = False
        else:
            endDateOk = True
    else:
        endDateOk = False

    enableProgrammedRecording()

def carica_canali():
    if os.path.exists(os.path.join(__location__, 'canali.json')):
        with open(os.path.join(__location__, 'canali.json'), "r", encoding="utf-8") as f:
            return json.load(f)
    return []

def salva_canali(canali):
    with open(os.path.join(__location__, 'canali.json'), "w", encoding="utf-8") as f:
        json.dump(canali, f, indent=4, ensure_ascii=False)

def aggiorna_tabella(tree):
    tree.delete(*tree.get_children())
    for canale in carica_canali():
        tree.insert("", "end", values=(canale["nome"], canale["flusso"]))

def availability_check(flusso):
    TIMEOUT = 5
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                    "(KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36"
    }
    def ensure_schema(url):
        if not url.startswith(("http://", "https://")):
            return "http://" + url
        return url

    try:
        flusso = ensure_schema(flusso)
        response = requests.head(flusso, headers=headers, timeout=TIMEOUT)
        status = response.status_code
        if status == 200:
            return True
        elif status == 302:
            redirect_url = response.headers.get("Location")
            try:
                redirect_url = ensure_schema(redirect_url)
                redirected_response = requests.get(redirect_url, headers=headers, timeout=TIMEOUT)
                redirected_status = redirected_response.status_code
                if redirected_status == 200:
                    return True
                else:
                    return False
            except requests.RequestException:
                return False
        elif status == 301:
            redirect_url = response.headers.get("Location")
            try:
                redirect_url = ensure_schema(redirect_url)
                redirected_response = requests.get(redirect_url, headers=headers, timeout=TIMEOUT)
                redirected_status = redirected_response.status_code
                if redirected_status == 200:
                    return True
                else:
                    return False
            except requests.RequestException:
                return False
        elif status == 403:
            response = requests.get(flusso, headers=headers, timeout=TIMEOUT)
            status = response.status_code
            if status == 200:
                return True
            else:
                return False
        elif status == 404:
            response_get = requests.get(flusso, headers=headers, timeout=TIMEOUT, allow_redirects=True)
            if response_get.status_code == 200:
                return True
            else:
                return False
        elif status == 405:
            response_get = requests.get(flusso, headers=headers, timeout=TIMEOUT, allow_redirects=True)
            if response_get.status_code == 200:
                return True
            else:
                return False
        elif status == 307:
            redirect_url = response.headers.get("Location")
            try:
                redirect_url = ensure_schema(redirect_url)
                redirected_response = requests.get(redirect_url, headers=headers, timeout=TIMEOUT)
                if redirected_response.status_code == 200:
                    return True
                else:
                    return False
            except requests.RequestException:
                return False
        else:
            return False
    except requests.RequestException:
        return False

def importa_da_m3u(tree, finestra_canali):
    m3u_path = filedialog.askopenfilename(
        title=_("Seleziona un file M3U"),
        filetypes=[("Playlist M3U", "*.m3u"), (_("Tutti i file"), "*.*")],
        parent=finestra_canali
    )
    nuovi_canali = []
    nuovi_canali_non_duplicati = []
    if os.path.exists(m3u_path) and os.path.splitext(m3u_path)[1].lower() == '.m3u':
        with open(m3u_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        nome = None
        for line in lines:
            line = line.strip()
            if line.startswith("#EXTINF:"):
                # Il nome è dopo la virgola
                parts = line.split(",", 1)
                nome = parts[1].strip() if len(parts) > 1 else "Senza nome"
            elif line and not line.startswith("#"):
                flusso = line
                if nome:
                    nuovi_canali.append({
                        "nome": nome,
                        "flusso": flusso
                    })
                    nome = None  # Reset per la prossima entry

        if os.path.exists(os.path.join(__location__, 'canali.json')):
            with open(os.path.join(__location__, 'canali.json'), 'r', encoding='utf-8') as f:
                dati = json.load(f)
        else:
            dati = []

        nuovi_canali_non_duplicati = [c for c in nuovi_canali if not any(c["nome"] == d["nome"] and c["flusso"] == d["flusso"] for d in dati)]

        dati.extend(nuovi_canali_non_duplicati)

        messagebox.showinfo(_("Importazione completata"), _("Nuovi canali aggiunti: %s") % len(nuovi_canali_non_duplicati), parent=finestra_canali)
        salva_canali(dati)
        aggiorna_tabella(tree)
    else:
        messagebox.showinfo(_("Errore"), _("Il file selezionato non è valido"), parent=finestra_canali)


def apri_finestra_aggiunta(tree, toplevel, canale=None, indice=None):
    finestra_aggiunta = tk.Toplevel(toplevel)
    finestra_aggiunta.title(_("Aggiungi canale") if canale is None else _("Modifica canale"))
    finestra_aggiunta.geometry(f"600x200+{(toplevel.winfo_x() + toplevel.winfo_width()//2 - 300)}+{(toplevel.winfo_y() + toplevel.winfo_height()//2 - 100)}")

    tk.Label(finestra_aggiunta, text=_("Nome canale")).grid(row=0, column=0, padx=10, pady=10, sticky="e")
    nome_var = tk.StringVar(value=canale["nome"] if canale else "")
    nome_entry = tk.Entry(finestra_aggiunta, textvariable=nome_var, width=80)
    nome_entry.grid(row=0, column=1, padx=10, pady=10)

    tk.Label(finestra_aggiunta, text=_("Flusso")).grid(row=1, column=0, padx=10, pady=10, sticky="e")
    flusso_var = tk.StringVar(value=canale["flusso"] if canale else "")
    flusso_entry = tk.Entry(finestra_aggiunta, textvariable=flusso_var, width=80)
    flusso_entry.grid(row=1, column=1, padx=10, pady=10)

    def validazione():
        return nome_var.get().strip() and flusso_var.get().strip()

    def salva():
        if not validazione():
            return
        nuovo = {"nome": nome_var.get().strip(), "flusso": flusso_var.get().strip()}
        canali = carica_canali()
        if canale and indice is not None:
            canali[indice] = nuovo
        else:
            canali.append(nuovo)
        salva_canali(canali)
        aggiorna_tabella(tree)
        finestra_aggiunta.destroy()

    style_finestrella = ttk.Style()
    style_finestrella.configure("Finestrella.TButton", font=("Segoe UI", 10))

    btn_frame = ttk.Frame(finestra_aggiunta)
    btn_frame.grid(row=2, column=0, columnspan=5, pady=20)

    salva_btn = ttk.Button(btn_frame, text="OK", style="Finestrella.TButton", command=salva, state="disabled")
    salva_btn.pack(side="left", padx=10)
    annulla_btn = ttk.Button(btn_frame, text=_("Annulla"), style="Finestrella.TButton", command=finestra_aggiunta.destroy)
    annulla_btn.pack(side="right", padx=10)

    def aggiorna_stato(*_):
        salva_btn.config(state="normal" if validazione() else "disabled")

    nome_var.trace_add("write", aggiorna_stato)
    flusso_var.trace_add("write", aggiorna_stato)

def rimuovi_canali(tree, finestra_canali):
    selezionati = tree.selection()
    if not selezionati:
        return
    count = len(selezionati)
    conferma = messagebox.askyesno(_("Canali selezionati: %s") % count, _("Sei sicuro di voler procedere con l'eliminazione?"), parent=finestra_canali)
    if not conferma:
        return
    canali = carica_canali()
    valori_selezionati = [tree.item(i)["values"] for i in selezionati]
    valori_selezionati = [[str(v[0]), str(v[1])] for v in valori_selezionati]
    nuovi_canali = [c for c in canali if [c["nome"], c["flusso"]] not in valori_selezionati]
    salva_canali(nuovi_canali)
    aggiorna_tabella(tree)

def controlla(tree, finestra_canali):
    tree.tag_configure("rosso", background="tomato")
    tree.tag_configure("verde", background="lightgreen")
    counter = 0
    with ThreadPoolExecutor(max_workers=20) as executor:
        available = list(executor.map(availability_check, [tree.item(item, "values")[1] for item in tree.get_children()]))
    for i, item in enumerate(tree.get_children()):
        if (not available[i]):
            counter += 1
            tree.item(item, tags=("rosso",))
        else:
            tree.item(item, tags=("verde",))
    if counter > 0:
        messagebox.showinfo(_("Controllo disponibilità"), _("Controllo terminato. I flussi non raggiungibili (%s) sono evidenziati in rosso") % counter, parent=finestra_canali)
    else:
        messagebox.showinfo(_("Controllo disponibilità"), _("Controllo terminato. Tutti i flussi sono raggiungibili"), parent=finestra_canali)

def gestisci_canali():
    finestra_canali = tk.Toplevel(window)
    finestra_canali.title(_("Gestione canali"))
    larghezza_canali, altezza_canali = 1000, 400
    x_canali = (window.winfo_x() + window.winfo_width() // 2) - (larghezza_canali // 2)
    y_canali = (window.winfo_y() + window.winfo_height() // 2) - (altezza_canali // 2)
    finestra_canali.geometry(f"{larghezza_canali}x{altezza_canali}+{x_canali}+{y_canali}")
    
    style_finestrella = ttk.Style()
    style_finestrella.configure("Finestrella.TButton", font=("Segoe UI", 10))

    tree = ttk.Treeview(finestra_canali, columns=("Nome", "Flusso"), show="headings", selectmode="extended")
    tree.heading("Nome", text=_("Nome canale"))
    tree.heading("Flusso", text=_("Flusso"))
    tree.column("Nome", width=100)
    tree.column("Flusso", width=700)
    scroll_y = ttk.Scrollbar(finestra_canali, orient="vertical", command=tree.yview)
    tree.configure(yscrollcommand=scroll_y.set)
    tree.grid(row=0, columnspan=2, column=0, padx=(10, 0), pady=10, sticky="nsew")
    finestra_canali.grid_rowconfigure(0, weight=1)
    scroll_y.grid(row=0, column=2, sticky="ns")

    btn_frame = ttk.Frame(finestra_canali)
    btn_frame.grid(row=0, column=3, padx=(0, 10), pady=10, sticky="ns")

    btn_importa = ttk.Button(btn_frame, text=_("Importa m3u"), width=20, style="Finestrella.TButton", command=lambda: importa_da_m3u(tree, finestra_canali))
    btn_importa.pack(pady=5)

    btn_aggiungi = ttk.Button(btn_frame, text=_("Aggiungi"), width=20, style="Finestrella.TButton", command=lambda: apri_finestra_aggiunta(tree, finestra_canali))
    btn_aggiungi.pack(pady=5)

    def modifica():
        selezionati = tree.selection()
        if len(selezionati) == 1:
            indice = tree.index(selezionati[0])
            valore = tree.item(selezionati[0])["values"]
            apri_finestra_aggiunta(tree, finestra_canali, {"nome": valore[0], "flusso": valore[1]}, indice)

    btn_modifica = ttk.Button(btn_frame, text=_("Modifica"), width=20, style="Finestrella.TButton", command=modifica)
    btn_modifica.pack(pady=5)

    def aggiorna_modifica(*_):
        btn_modifica.config(state="normal" if len(tree.selection()) == 1 else "disabled")
        btn_rimuovi.config(state="normal" if len(tree.selection()) >= 1 else "disabled")
        btn_check.config(state="normal" if len(tree.get_children()) >= 1 else "disabled")

    tree.bind("<<TreeviewSelect>>", aggiorna_modifica)

    btn_rimuovi = ttk.Button(btn_frame, text=_("Rimuovi"), width=20, style="Finestrella.TButton", command=lambda: rimuovi_canali(tree, finestra_canali))
    btn_rimuovi.pack(pady=5)
    btn_modifica.config(state="disabled")
    btn_rimuovi.config(state="disabled")

    btn_check = ttk.Button(btn_frame, text=_("Controlla disponibilità"), width=20, style="Finestrella.TButton", command=lambda: controlla(tree, finestra_canali))
    btn_check.pack(pady=5)

    aggiorna_tabella(tree)


def on_closing():
    checkIfOld('record.json')
    with open(os.path.join(__location__, 'record.json'), 'r') as file:
        data = json.load(file)
    if data:
        messagebox.showinfo(_("Attenzione"), _("Impossibile chiudere il programma perché c'è almeno una registrazione in corso. Ferma le registrazioni in corso."))
    else:
        window.destroy()

def aggiorna_valori():
    values = []
    with open(os.path.join(__location__, 'canali.json'), 'r', encoding="utf-8") as file:
        data = json.load(file)
    for entry in data:
        values.append(entry["nome"])
    filter = nn.get().lower()
    filteredValues = []

    for entry in values:
        if filter in entry.lower():
            filteredValues.append(entry)

    input_channel['values'] = filteredValues

def report_issue():
    webbrowser.open("https://github.com/Messina-Agata/TeleVedi/issues")

def accetto(finestra):
    with open(FLAG_FILE, "w") as f:
        f.write("avviato")
    finestra.destroy()

def non_accetto():
    sys.exit()

def accetta_condizioni_di_utilizzo(window):
    finestra = tk.Toplevel(window)
    finestra.title(_("Termini e Condizioni"))

    larghezza_disc = 600
    altezza_disc = 500

    schermo_larghezza_disc = finestra.winfo_screenwidth()
    schermo_altezza_disc = finestra.winfo_screenheight()

    x_disc = (schermo_larghezza_disc // 2) - (larghezza_disc // 2)
    y_disc = (schermo_altezza_disc // 2) - (altezza_disc // 2)

    finestra.geometry(f"{larghezza_disc}x{altezza_disc}+{x_disc}+{y_disc}")

    finestra.attributes('-topmost', True)
    finestra.lift()
    finestra.focus_force()

    finestra.columnconfigure(0, weight=1)
    finestra.rowconfigure(0, weight=1)

    finestra.grab_set()
    finestra.transient(window)

    area_testo = scrolledtext.ScrolledText(finestra, wrap=tk.WORD, width=70, height=20)
    if lang == 'it':
        area_testo.insert(tk.INSERT, """\
        LICENZA D'USO (EULA) – CONTRATTO DI LICENZA CON L'UTENTE FINALE
    ATTENZIONE: L'installazione e l'utilizzo del presente software implicano l'accettazione integrale dei termini e delle condizioni qui esposti. Se non si accettano tali condizioni, l'uso del software non è consentito.
    1. Finalità d'uso
    Il software è concesso in licenza esclusivamente per la registrazione e la copia, a fini personali e non commerciali, dei flussi caricati dall'utente. Qualsiasi utilizzo diverso, inclusa la distribuzione o la condivisione dei contenuti registrati, è vietato salvo espressa autorizzazione da parte dei titolari dei diritti.
    2. Origine lecita dei flussi
    L’utente è tenuto a utilizzare esclusivamente flussi provenienti da fonti lecite e legalmente autorizzate. È vietato l’inserimento e la registrazione di flussi che violino diritti d’autore, licenze o altre normative vigenti. L’utente dichiara di avere il diritto legale di accedere e registrare i contenuti trasmessi.
    3. Divieto di elusione delle protezioni
    È severamente vietato eludere, aggirare o compromettere le misure tecnologiche di protezione applicate ai flussi streaming, inclusi sistemi DRM, cifrature, restrizioni geografiche o qualsiasi altra tecnologia volta a tutelare i diritti dei contenuti trasmessi.
    4. Responsabilità dell’utente
    L’utente è l’unico responsabile per l’utilizzo del software in violazione della Legge sul Diritto d’Autore (LdA) o di altre normative. Il titolare del software declina ogni responsabilità per eventuali conseguenze civili, penali o amministrative derivanti da un uso illecito o improprio da parte dell’utente.

        """)
    else:
            area_testo.insert(tk.INSERT, """\
        END USER LICENSE AGREEMENT (EULA)
    WARNING: Installing and using this software implies full acceptance of the terms and conditions set forth herein. If you do not accept these conditions, use of the software is not permitted.
    1. Purpose of Use
    The software is licensed exclusively for the recording and copying, for personal and non-commercial purposes, of streams uploaded by the user. Any other use, including distribution or sharing of the recorded content, is prohibited unless expressly authorized by the rights holders.
    2. Lawful Origin of Streams
    The user is required to use only streams originating from lawful and legally authorized sources. Uploading and recording streams that infringe copyright, licenses, or other applicable regulations is strictly prohibited. The user declares to have the legal right to access and record the transmitted content.
    3. Prohibition of Circumvention of Protections
    It is strictly forbidden to bypass, circumvent, or compromise technological protection measures applied to streaming content, including DRM systems, encryption, geographic restrictions, or any other technology designed to safeguard the rights of the transmitted content.
    4. User Responsibility
    The user is solely responsible for any use of the software that violates Copyright Law or other regulations. The software owner disclaims all liability for any civil, criminal, or administrative consequences resulting from unlawful or improper use by the user.
        """)

    area_testo.configure(state='disabled')  # testo non modificabile
    area_testo.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")

    frame_bottoni = tk.Frame(finestra)
    frame_bottoni.grid(row=1, column=0, pady=10)

    btn_accetto = tk.Button(frame_bottoni, text=_("Accetto"), width=15, command=lambda: accetto(finestra))
    btn_accetto.grid(row=0, column=0, padx=10)

    btn_non_accetto = tk.Button(frame_bottoni, text=_("Non accetto"), width=15, command=non_accetto)
    btn_non_accetto.grid(row=0, column=1, padx=10)

style = ttk.Style()
style.configure("TButton", padding=6, font=("Segoe UI", 18))
style.configure("TLabel", font=("Segoe UI", 18))
style.configure("Bianco.TFrame", background="white")

bigfont = tk.font.Font(family = "Segoe UI", size = 15)
window.option_add("*TCombobox*Listbox*Font", bigfont)

if not os.path.exists(FLAG_FILE):
    accetta_condizioni_di_utilizzo(window)

label_rectype = ttk.Label(window, text = _("Controllo registrazione"), foreground = "black", background = "white")
label_rectype.grid(row = 0, column = 0, padx = 10, pady = 10, sticky = "WE")
label_logo = ttk.Label(window, image=logo)
label_logo.grid(row=0, column=2, rowspan=4, padx=10, pady=10)

n = tk.StringVar(value = _("Manuale"))
input_rectype = ttk.Combobox(window, width = 28, font = 20, textvariable = n)
input_rectype['values'] = (_("Manuale"), _("Programmato"))
input_rectype['state'] = 'readonly'
input_rectype.bind('<<ComboboxSelected>>', recTypeChanged)
input_rectype.grid(row = 0, column = 1, sticky = "WE", padx = 10, pady = 10)

label_channel = ttk.Label(window, text = _("Canale"), foreground = "black", background = "white")
label_channel.grid(row = 1, column = 0, padx = 10, pady = 10, sticky = "WE")

nn = tk.StringVar()
nn.trace_add('write', on_change)
input_channel = ttk.Combobox(window, width = 28, font = 20, textvariable = nn)
with open(os.path.join(__location__, 'canali.json'), 'r', encoding="utf-8") as file:
    data = json.load(file)
for entry in data:
    values.append(entry["nome"])
input_channel['values'] = values
input_channel.bind("<Button-1>", lambda e: aggiorna_valori())
input_channel.grid(row = 1, column = 1, sticky = "WE", padx = 10, pady = 10)

file_path = ''
label_filePath = ttk.Entry(window, text = file_path, foreground = "black", width=40, font=("Segoe UI", 18))
label_filePath.grid(row = 2, column = 1, padx = 10, pady = 10, sticky = "WE")
save_button = ttk.Button(window, text = _("Salva registrazione in..."), command = getRecPath)
save_button.grid(row = 2, column = 0, padx = 10, pady = 10, sticky = "WE")

rec_button = ttk.Button(text = _("Avvia registrazione"), command = record)
rec_button["state"] = "disabled"
rec_button.grid(row = 3, column = 1, padx = 10, pady = 10, sticky = "WE")

viewRec_button = ttk.Button(text = _("Vedi registrazioni in corso"), command = viewLiveRecs)
viewRec_button.grid(row = 4, column = 1, padx = 10, pady = 10, sticky = "WE")

channels_button = ttk.Button(text = _("Gestisci canali"), command = gestisci_canali)
channels_button.grid(row = 4, column = 2, padx = 10, pady = 10, sticky = "WE")

problem_button = ttk.Button(text = _("Segnala un problema"), command = report_issue)
problem_button.grid(row = 5, column = 2, padx = 10, pady = 10, sticky = "WE")

label_start = ttk.Label(window, text = _("Data e ora d'inizio"), foreground = "black", background = "white")

startDay = DateEntry(window, date_pattern='dd/mm/yyyy', font = 20, selectmode = 'day')
sds = tk.StringVar()
sds.trace_add("write", checkStartDate)
startDay.configure(textvariable = sds)
startTimeFrame = tk.Frame(window, borderwidth = 1, relief = "solid")
start_nh = tk.StringVar()
start_nh.trace_add('write', checkStartDate)
startHour = ttk.Combobox(startTimeFrame, width = 18, font = 20, textvariable = start_nh)
startHourValues = ("00", "01", "02", "03", "04", "05", "06", "07", "08", "09", "10", "11", "12", "13", "14", "15", "16", "17", "18", "19", "20", "21", "22", "23")
startHour['values'] = startHourValues
startHour.pack(side = "left", fill = "both", expand = True)
label_startTime = ttk.Label(startTimeFrame, text = ":", foreground = "black", background="white")
label_startTime.pack(side = "left", fill = "both", expand = True)
start_nm = tk.StringVar()
start_nm.trace_add('write', checkStartDate)
startMinute = ttk.Combobox(startTimeFrame, width = 18, font = 20, textvariable = start_nm)
startMinuteValues = ("00", "01", "02", "03", "04", "05", "06", "07", "08", "09", "10", "11", "12", "13", "14", "15", "16", "17", "18", "19", "20", "21", "22", "23", "24", "25", "26", "27", "28", "29", "30", "31", "32", "33", "34", "35", "36", "37", "38", "39", "40", "41", "42", "43", "44", "45", "46", "47", "48", "49", "50", "51", "52", "53", "54", "55", "56", "57", "58", "59")
startMinute['values'] = startMinuteValues
startMinute.pack(side = "right", fill = "both", expand = True)

label_end = ttk.Label(window, text = _("Data e ora di fine"), foreground = "black", background = "white")

endDay = DateEntry(window, date_pattern='dd/mm/yyyy', font = 20, selectmode = 'day')
eds = tk.StringVar()
eds.trace_add("write", checkEndDate)
endDay.configure(textvariable = eds)
endTimeFrame = tk.Frame(window, borderwidth = 1, relief = "solid")
end_nh = tk.StringVar()
end_nh.trace_add('write', checkEndDate)
endHour = ttk.Combobox(endTimeFrame, width = 18, font = 20, textvariable = end_nh)
endHourValues = ("00", "01", "02", "03", "04", "05", "06", "07", "08", "09", "10", "11", "12", "13", "14", "15", "16", "17", "18", "19", "20", "21", "22", "23")
endHour['values'] = endHourValues
endHour.pack(side = "left", fill = "both", expand = True)
label_endTime = ttk.Label(endTimeFrame, text = ":", foreground = "black", background="white")
label_endTime.pack(side = "left", fill = "both", expand = True)
end_nm = tk.StringVar()
end_nm.trace_add('write', checkEndDate)
endMinute = ttk.Combobox(endTimeFrame, width = 18, font = 20, textvariable = end_nm)
endMinuteValues = ("00", "01", "02", "03", "04", "05", "06", "07", "08", "09", "10", "11", "12", "13", "14", "15", "16", "17", "18", "19", "20", "21", "22", "23", "24", "25", "26", "27", "28", "29", "30", "31", "32", "33", "34", "35", "36", "37", "38", "39", "40", "41", "42", "43", "44", "45", "46", "47", "48", "49", "50", "51", "52", "53", "54", "55", "56", "57", "58", "59")
endMinute['values'] = endMinuteValues
endMinute.pack(side = "right", fill = "both", expand = True)

program_button = ttk.Button(text = _("Programma registrazione"), command = programRec)
program_button["state"] = "disabled"

history_button = ttk.Button(text = _("Vedi registrazioni programmate"), command = viewRecs)

window.protocol("WM_DELETE_WINDOW", on_closing)

if __name__ == "__main__":
    window.mainloop()