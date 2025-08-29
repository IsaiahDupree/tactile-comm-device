# data_gui.py — Tactile Data Tool (GUI)
# Requires: pip install pyserial PySimpleGUI
# Put this file alongside your existing data_cli.py

import os, threading, sys, time, queue
import PySimpleGUI as sg
from enum import Enum

# --- import your CLI pieces ---
import data_cli as cli
from serial.tools import list_ports

# === SEGMENT A: connection states, styles, helpers ===
class ConnState(Enum):
    DISCONNECTED = 0
    CONNECTING = 1
    CONNECTED = 2
    ERROR = 3

KEY_DEFAULTS = list("ABCDEFGHIJKLMNOPQRSTUVWXYZ") + ["SHIFT","YES","NO","WATER","SPACE","PERIOD"]

STATUS_COLORS = {
    ConnState.DISCONNECTED: "red",
    ConnState.CONNECTING:   "orange",
    ConnState.CONNECTED:    "green",
    ConnState.ERROR:        "firebrick",
}

APP_TITLE = "Tactile Data Tool"
DEFAULT_BAUD = 115200

# ------------------ helpers ------------------

def ui_conn(window, state: ConnState, msg: str):
    color = STATUS_COLORS[state]
    window["-LED-"].update("●", text_color=color)
    window["-STATUS-"].update(msg, text_color=color)
    # Enable controls only when connected
    enabled = (state == ConnState.CONNECTED)
    for k in ("-LS-","-PUT-","-GET-","-DEL-","-SYNCSEQ-","-SYNCPRE-","-EXIT-","-SCAN-"):
        if k in window.AllKeysDict:
            window[k].update(disabled=not enabled)

def current_ports():
    from serial.tools import list_ports
    return [(p.device, f"{p.device} — {p.description}") for p in list_ports.comports()]

def keypad_layout():
    head = [
        sg.Button("SHIFT", key="-KP_SHIFT-", size=(6,2)),
        sg.Button("YES",   key="-KP_YES-",   size=(6,2)),
        sg.Button("NO",    key="-KP_NO-",    size=(6,2)),
        sg.Button("WATER", key="-KP_WATER-", size=(8,2)),
    ]
    rows = []
    for row in ["ABCDEFG", "HIJKLMN", "OPQRSTU", "VWXYZ.-"]:
        r=[]
        for ch in row:
            name = "PERIOD" if ch == "." else ch
            r.append(sg.Button(ch, key=f"-KP_{name}-", size=(3,2)))
        rows.append(r)
    return [head] + rows

def human_bank(name):
    # Keep choices aligned with firmware
    if name in ("human", "generated", "GENERA~1"):
        return name
    return "human"

def append_log(window, text):
    window["-LOG-"].print(text, end="" if text.endswith("\n") else "\n")

def set_status(window, ok: bool, msg: str):
    window["-STATUS-"].update(value=("✅ " if ok else "⚠️ ") + msg, text_color="green" if ok else "orange")

def ensure_connected_ser(window, values, ser_holder):
    if ser_holder["ser"] is None:
        append_log(window, "[err] Not connected.")
        return None
    return ser_holder["ser"]

def refresh_ports(window):
    ports = list_serial_ports()
    window["-PORT-"].update(values=[label for _, label in ports])
    if ports:
        window["-PORT-"].update(value=ports[0][1])
    return ports

def table_rows(items):
    # items: list[(name,size)]
    return [[n, f"{sz:,}"] for (n, sz) in items]

# ------------------ threaded ops ------------------

def run_in_thread(window, key, fn, *args, **kwargs):
    """
    Run long operation in a thread. On completion, post (key, (ok, payload_or_errmsg))
    """
    def _wrap():
        try:
            out = fn(*args, **kwargs)
            window.write_event_value(key, (True, out))
        except Exception as e:
            window.write_event_value(key, (False, str(e)))
    t = threading.Thread(target=_wrap, daemon=True)
    t.start()

# ------------------ GUI layout ------------------

# === SEGMENT B: layout (replace the old 'layout = [...]') ===
# Handle PySimpleGUI theme compatibility
try:
    sg.theme("SystemDefaultForReal")
except AttributeError:
    # Fallback for older PySimpleGUI versions
    try:
        sg.change_look_and_feel("SystemDefault")
    except:
        pass  # Use default theme

port_labels = [label for _, label in current_ports()]

layout = [
    # STATUS BAR
    [sg.Text("●", key="-LED-", text_color="red", font=("Arial",14)),
     sg.Text("Disconnected", key="-STATUS-", text_color="red", size=(40,1)),
     sg.Push(),
     sg.Button("Clear Log", key="-CLRLOG-")],
    [sg.HorizontalSeparator()],
    # CONNECTION
    [sg.Text("Port"), sg.Combo(port_labels, key="-PORT-", size=(42,1), readonly=True, enable_events=True),
     sg.Button("Refresh", key="-REFRESH-"),
     sg.Text("Baud"), sg.Input(str(DEFAULT_BAUD), key="-BAUD-", size=(8,1)),
     sg.Button("Connect", key="-CONNECT-", button_color=("white","green")),
     sg.Button("Disconnect", key="-DISCONNECT-")],
    [sg.HorizontalSeparator()],
    # BANK/KEY pickers
    [sg.Text("Bank"), sg.Combo(values=["human","generated","GENERA~1"], default_value="human",
                               key="-BANK-", size=(12,1), readonly=True),
     sg.Text("Key"), sg.Combo(values=KEY_DEFAULTS, default_value="A", key="-KEY-", size=(12,1), readonly=True),
     sg.Button("Scan Keys", key="-SCAN-"),
     sg.Button("List Files", key="-LS-"),
     sg.Button("Exit Data Mode", key="-EXIT-")],
    # DEVICE-LIKE KEYPAD
    [sg.Frame("Keypad", keypad_layout(), key="-PAD-", relief=sg.RELIEF_SUNKEN)],
    # FILE TABLE
    [sg.Table(values=[], headings=["Filename","Size"], key="-TABLE-", auto_size_columns=True,
              expand_x=True, expand_y=True, enable_events=True, select_mode=sg.TABLE_SELECT_MODE_BROWSE, num_rows=8)],
    [sg.HorizontalSeparator()],
    # TRANSFERS
    [sg.Text("Upload single:"), sg.Input(key="-PUTPATH-", expand_x=True, enable_events=True),
     sg.FileBrowse(file_types=(("Audio", "*.mp3;*.wav;*.ogg"), ("All","*.*"))),
     sg.Text("as"), sg.Input("001.mp3", key="-PUTNAME-", size=(15,1)),
     sg.Button("Upload", key="-PUT-")],
    [sg.Text("Folder sync:"), sg.Input(key="-FOLDER-", expand_x=True, enable_events=True),
     sg.FolderBrowse(), sg.Text("Ext"), sg.Combo(values=["mp3","wav","ogg"], default_value="mp3",
     key="-EXT-", size=(6,1), readonly=True),
     sg.Button("Sync (001,002...)", key="-SYNCSEQ-"),
     sg.Button("Sync (preserve names)", key="-SYNCPRE-")],
    [sg.Text("Download selected to:"), sg.Input(key="-OUT-", expand_x=True), sg.FolderBrowse(),
     sg.Button("Download", key="-GET-"),
     sg.Button("Delete", key="-DEL-")],
    [sg.ProgressBar(100, orientation="h", size=(40, 20), key="-PROG-", expand_x=True)],
    [sg.Multiline(key="-LOG-", size=(10,8), autoscroll=True, expand_x=True, expand_y=True, font=("Consolas",10))]
]

window = sg.Window(APP_TITLE, layout, resizable=True)

# ------------------ state ------------------

ser_holder = {"ser": None}
current_items = []   # list[(name,size)]

# === SEGMENT C: connection state management ===
conn = {"state": ConnState.DISCONNECTED, "port": None, "baud": DEFAULT_BAUD}

def _connect_worker(port, baud):
    ser = cli.open_serial(port, baud)
    cli.handshake(ser)  # enters DATA_MODE
    return ser

# Initialize connection state
ui_conn(window, ConnState.DISCONNECTED, "Disconnected")

# ------------------ main loop ------------------

while True:
    event, values = window.read(timeout=500)
    if event == sg.WINDOW_CLOSED:
        break

    # === SEGMENT C: connection event handling ===
    if event == "-REFRESH-":
        ports = current_ports()
        window["-PORT-"].update(values=[label for _, label in ports])
        ui_conn(window, conn["state"], f"{len(ports)} port(s) found")

    elif event == "-CONNECT-":
        ports = current_ports()
        label = values["-PORT-"]
        port = None
        for dev, lab in ports:
            if lab == label: port = dev; break
        port = port or (ports[0][0] if ports else None)
        if not port:
            append_log(window, "[err] no serial ports found")
            continue
        try:
            baud = int(values["-BAUD-"])
        except:
            append_log(window, "[err] invalid baud")
            continue
        ui_conn(window, ConnState.CONNECTING, f"Connecting to {port}@{baud} …")
        run_in_thread(window, "-CONNECT-DONE-", _connect_worker, port, baud)

    elif event == "-CONNECT-DONE-":
        ok, payload = values["-CONNECT-DONE-"]
        if ok:
            ser_holder["ser"] = payload
            conn.update({"state": ConnState.CONNECTED})
            ui_conn(window, ConnState.CONNECTED, "Connected")
            append_log(window, "[ok] connected & in data mode")
        else:
            conn.update({"state": ConnState.ERROR})
            ui_conn(window, ConnState.ERROR, f"Connect failed: {payload}")
            append_log(window, f"[err] connect: {payload}")

    elif event == "-DISCONNECT-":
        if ser_holder["ser"]:
            try: ser_holder["ser"].close()
            except: pass
            ser_holder["ser"] = None
        conn.update({"state": ConnState.DISCONNECTED})
        ui_conn(window, ConnState.DISCONNECTED, "Disconnected")
        append_log(window, "[i] disconnected")

    # === SEGMENT D: keypad clicks & key scan ===
    elif isinstance(event, str) and event.startswith("-KP_") and event.endswith("-"):
        keyname = event[4:-1]          # e.g., "A" or "PERIOD" or "SHIFT"
        # The device uses "PERIOD" name even though the cap shows "."
        window["-KEY-"].update(value=keyname)
        append_log(window, f"[i] key selected: {keyname}")

    elif event == "-SCAN-":
        ser = ensure_connected_ser(window, values, ser_holder)
        if not ser: continue
        bank = values["-BANK-"]
        # Probe the default key set to see which exist on device
        found = set()
        for k in KEY_DEFAULTS:
            try:
                items = cli.cmd_ls(ser, bank, k)
                if items: found.add(k)
            except Exception:
                pass
        if found:
            opts = sorted(found, key=lambda s: (len(s) > 1, s))  # A..Z then specials
            window["-KEY-"].update(values=opts, value=opts[0])
            append_log(window, f"[ok] found {len(opts)} key(s) on device")
        else:
            append_log(window, "[i] no keys with files found; using defaults")

    # === SEGMENT E: hot-plug detection ===
    elif event == "__TIMEOUT__":
        # Compare current list to dropdown; update if changed
        labels = [label for _, label in current_ports()]
        if set(labels) != set(window["-PORT-"].Values or []):
            window["-PORT-"].update(values=labels)


    elif event == "-EXIT-":
        ser = ensure_connected_ser(window, values, ser_holder)
        if not ser: continue
        try:
            cli.cmd_exit(ser)
            append_log(window, "[ok] EXIT sent (device leaves data mode)")
        except Exception as e:
            append_log(window, f"[err] EXIT failed: {e}")

    elif event == "-LS-":
        ser = ensure_connected_ser(window, values, ser_holder)
        if not ser: continue
        bank = human_bank(values["-BANK-"]); key = values["-KEY-"].strip()
        append_log(window, f"[i] listing /audio/{bank}/{key}")
        def _ls():
            return cli.cmd_ls(ser, bank, key)
        run_in_thread(window, "-LS-DONE-", _ls)

    elif event == "-LS-DONE-":
        ok, payload = values["-LS-DONE-"]
        if ok:
            current_items = payload
            window["-TABLE-"].update(values=table_rows(current_items))
            append_log(window, f"[ok] {len(current_items)} item(s)")
        else:
            append_log(window, f"[err] {payload}")

    elif event == "-PUT-":
        ser = ensure_connected_ser(window, values, ser_holder)
        if not ser: continue
        bank = human_bank(values["-BANK-"]); key = values["-KEY-"].strip()
        path = values["-PUTPATH-"]; dest = values["-PUTNAME-"].strip()
        if not path or not os.path.isfile(path):
            append_log(window, "[err] choose a file to upload"); continue
        if not dest:
            append_log(window, "[err] choose a destination filename"); continue
        append_log(window, f"[put] {path} -> /audio/{bank}/{key}/{dest}")
        def _put():
            cli.cmd_put(ser, bank, key, dest, path, use_crc=True)
        run_in_thread(window, "-PUT-DONE-", _put)

    elif event == "-PUT-DONE-":
        ok, payload = values["-PUT-DONE-"]
        if ok:
            append_log(window, "[ok] upload complete")
        else:
            append_log(window, f"[err] {payload}")

    elif event == "-GET-":
        ser = ensure_connected_ser(window, values, ser_holder)
        if not ser: continue
        bank = human_bank(values["-BANK-"]); key = values["-KEY-"].strip()
        sel = values["-TABLE-"]
        outdir = values["-OUT-"] or "."
        if not sel or not current_items:
            append_log(window, "[err] select a file in the table"); continue
        name, _ = current_items[sel[0]]
        os.makedirs(outdir, exist_ok=True)
        outpath = os.path.join(outdir, name)
        append_log(window, f"[get] {name} -> {outpath}")
        def _get():
            cli.cmd_get(ser, bank, key, name, outpath)
        run_in_thread(window, "-GET-DONE-", _get)

    elif event == "-GET-DONE-":
        ok, payload = values["-GET-DONE-"]
        append_log(window, "[ok] download complete" if ok else f"[err] {payload}")

    elif event == "-DEL-":
        ser = ensure_connected_ser(window, values, ser_holder)
        if not ser: continue
        bank = human_bank(values["-BANK-"]); key = values["-KEY-"].strip()
        sel = values["-TABLE-"]
        if not sel or not current_items:
            append_log(window, "[err] select a file in the table"); continue
        name, _ = current_items[sel[0]]
        append_log(window, f"[del] {name}")
        def _del():
            cli.cmd_del(ser, bank, key, name)
        run_in_thread(window, "-DEL-DONE-", _del)

    elif event == "-DEL-DONE-":
        ok, payload = values["-DEL-DONE-"]
        append_log(window, "[ok] delete done" if ok else f"[err] {payload}")

    elif event == "-SYNCSEQ-":
        ser = ensure_connected_ser(window, values, ser_holder)
        if not ser: continue
        bank = human_bank(values["-BANK-"]); key = values["-KEY-"].strip()
        folder = values["-FOLDER-"]; ext = values["-EXT-"].lstrip(".") or "mp3"
        if not folder or not os.path.isdir(folder):
            append_log(window, "[err] choose a folder to sync"); continue
        append_log(window, f"[sync] seq from {folder} as 001.{ext}, 002.{ext} ...")
        def _sync():
            cli.cmd_sync_seq(ser, bank, key, folder, ext=ext, start=1, dry_run=False)
        run_in_thread(window, "-SYNC-DONE-", _sync)

    elif event == "-SYNCPRE-":
        ser = ensure_connected_ser(window, values, ser_holder)
        if not ser: continue
        bank = human_bank(values["-BANK-"]); key = values["-KEY-"].strip()
        folder = values["-FOLDER-"]; ext = values["-EXT-"].lstrip(".") or "mp3"
        if not folder or not os.path.isdir(folder):
            append_log(window, "[err] choose a folder to sync"); continue
        append_log(window, f"[sync] preserve names from {folder} (*.{ext})")
        def _sync_pre():
            cli.cmd_sync_preserve(ser, bank, key, folder, ext=ext, dry_run=False)
        run_in_thread(window, "-SYNC-DONE-", _sync_pre)

    elif event == "-SYNC-DONE-":
        ok, payload = values["-SYNC-DONE-"]
        append_log(window, "[ok] sync complete" if ok else f"[err] {payload}")

    elif event == "-FLAG-":
        ser = ensure_connected_ser(window, values, ser_holder)
        if not ser: continue
        append_log(window, "[flag] creating /config/allow_writes.flag")
        def _flag():
            # Create empty flag file to enable writes
            cli.cmd_put(ser, "config", "", "allow_writes.flag", None, use_crc=False, empty_file=True)
        run_in_thread(window, "-FLAG-DONE-", _flag)

    elif event == "-FLAG-DONE-":
        ok, payload = values["-FLAG-DONE-"]
        if ok:
            append_log(window, "[ok] write flag created - PUT/DELETE now enabled")
        else:
            append_log(window, f"[err] flag creation failed: {payload}")

    elif event == "-CLRLOG-":
        window["-LOG-"].update("")

window.close()
