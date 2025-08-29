# data_gui_tk.py — Polished GUI for your Tactile Data Tool (Tkinter version)
# Requires: pyserial, pillow, your existing data_cli.py in the same folder

import os, sys, threading, time, re
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

# ==== SEGMENT C1: imports ====
from PIL import Image, ImageDraw, ImageFont, ImageTk  # pip install pillow

import data_cli as cli
from serial.tools import list_ports

APP_TITLE = "Tactile Data Tool"
DEFAULT_BAUD = 115200

KEY_DEFAULTS = list("ABCDEFGHIJKLMNOPQRSTUVWXYZ") + ["SHIFT","YES","NO","WATER","SPACE","PERIOD"]

# ---------- helpers ----------
def list_serial_ports():
    return [(p.device, f"{p.device} — {p.description}") for p in list_ports.comports()]

def ensure_dir(p):
    os.makedirs(p or ".", exist_ok=True)

def make_keycap(label:str, size=56) -> ImageTk.PhotoImage:
    # Draw a round white key with subtle shadow + centered label
    img = Image.new("RGBA", (size, size), (0,0,0,0))
    drw = ImageDraw.Draw(img)
    # shadow
    drw.ellipse((2,4,size-2,size), fill=(0,0,0,40))
    # cap
    drw.ellipse((0,0,size-4,size-4), fill=(245,245,245,255), outline=(180,180,180,255), width=2)
    # label
    txt = "•" if label == "PERIOD" else label
    try:
        # Try a nicer font if present; fallback safely
        font = ImageFont.truetype("Arial.ttf", size//2)
    except:
        font = ImageFont.load_default()
    tw, th = drw.textbbox((0,0), txt, font=font)[2:]
    drw.text(((size-tw)//2, (size-th)//2 - 1), txt, fill=(0,0,0,220), font=font)
    return ImageTk.PhotoImage(img)

# ---------- GUI ----------
class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(APP_TITLE)
        self.geometry("950x750")
        self.minsize(900, 680)

        self.ser = None
        self.conn_state = "DISCONNECTED"  # CONNECTING | CONNECTED | ERROR

        self._build_ui()
        self._wire_events()

        self.after(1000, self._auto_refresh_ports)  # hot-plug polling

    # ---- UI construction ----
    def _build_ui(self):
        pad = dict(padx=8, pady=6)

        # STATUS BAR with SD usage
        bar = ttk.Frame(self); bar.pack(fill="x", **pad)
        self.led = tk.Canvas(bar, width=14, height=14, highlightthickness=0)
        self.led.create_oval(2,2,12,12, fill="red", outline="")
        self.led.pack(side="left")
        self.status_lbl = ttk.Label(bar, text="Disconnected", foreground="red")
        self.status_lbl.pack(side="left", padx=(6,0))
        
        # Write status indicator
        self.write_led = tk.Canvas(bar, width=12, height=12, highlightthickness=0)
        self.write_led.create_oval(1,1,11,11, fill="gray", outline="")
        self.write_led.pack(side="right", padx=(6,2))
        self.write_lbl = ttk.Label(bar, text="Writes: --", font=("TkDefaultFont", 8))
        self.write_lbl.pack(side="right")
        
        # SD usage indicator
        self.sd_lbl = ttk.Label(bar, text="SD: -- / --")
        self.sd_lbl.pack(side="right", padx=(12,0))
        self.sdbar = ttk.Progressbar(bar, mode="determinate", length=160, maximum=100)
        self.sdbar.pack(side="right", padx=(6,6))
        
        ttk.Button(bar, text="Clear Log", command=self._clear_log).pack(side="right", padx=(0,12))

        ttk.Separator(self, orient="horizontal").pack(fill="x")

        # CONNECTION ROW
        row = ttk.Frame(self); row.pack(fill="x", **pad)
        ttk.Label(row, text="Port").pack(side="left")
        self.port_cmb = ttk.Combobox(row, width=45, state="readonly")
        self.port_cmb.pack(side="left", padx=(6,10))
        self._refresh_port_combo()

        ttk.Button(row, text="Refresh", command=self._refresh_port_combo).pack(side="left")
        ttk.Label(row, text="Baud").pack(side="left", padx=(12,2))
        self.baud_var = tk.StringVar(value=str(DEFAULT_BAUD))
        ttk.Entry(row, textvariable=self.baud_var, width=10).pack(side="left")
        self.btn_connect = ttk.Button(row, text="Connect", command=self._connect)
        self.btn_connect.pack(side="left", padx=(12,4))
        self.btn_disconnect = ttk.Button(row, text="Disconnect", command=self._disconnect)
        self.btn_disconnect.pack(side="left")

        ttk.Separator(self, orient="horizontal").pack(fill="x")

        # BANK / KEY PICKERS
        row2 = ttk.Frame(self); row2.pack(fill="x", **pad)
        ttk.Label(row2, text="Bank").pack(side="left")
        self.bank_cmb = ttk.Combobox(row2, values=["HUMAN", "GENERA~1"], width=12, state="readonly")
        self.bank_cmb.set("HUMAN"); self.bank_cmb.pack(side="left", padx=(6,10))
        ttk.Label(row2, text="Key").pack(side="left")
        self.key_cmb = ttk.Combobox(row2, values=KEY_DEFAULTS, state="readonly", width=14)
        self.key_cmb.set("A"); self.key_cmb.pack(side="left", padx=(6,10))
        self.btn_scan = ttk.Button(row2, text="Scan Keys", command=self._scan_keys)
        self.btn_scan.pack(side="left")
        self.btn_ls = ttk.Button(row2, text="List Files", command=self._ls)
        self.btn_ls.pack(side="left", padx=(8,0))
        self.btn_exit = ttk.Button(row2, text="Exit Data Mode", command=self._exit_data_mode)
        self.btn_exit.pack(side="left", padx=(8,0))
        self.btn_flag_on  = ttk.Button(row2, text="Enable Writes", command=self._flag_on)
        self.btn_flag_on.pack(side="left", padx=(12,0))
        self.btn_flag_off = ttk.Button(row2, text="Disable Writes", command=self._flag_off)
        self.btn_flag_off.pack(side="left", padx=(6,0))

        # ==== SEGMENT C2: image keypad ====
        padf = ttk.LabelFrame(self, text="Keypad"); padf.pack(fill="x", padx=8, pady=6)

        self._key_images = {}  # keep references so images don't get GC'd

        # Top row specials
        tr = ttk.Frame(padf); tr.pack()
        for label in ["SHIFT","YES","NO","WATER"]:
            img = make_keycap(label, size=60); self._key_images[label] = img
            btn = tk.Button(tr, image=img, borderwidth=0, highlightthickness=0,
                            command=lambda k=label: self._select_key(k))
            btn.pack(side="left", padx=6, pady=6)

        # Letter rows
        rows = ["ABCDEFG", "HIJKLMN", "OPQRSTU", "VWXYZ.-"]
        for r in rows:
            fr = ttk.Frame(padf); fr.pack()
            for ch in r:
                name = "PERIOD" if ch == "." else ch
                img = make_keycap(name, size=50); self._key_images[name] = img
                tk.Button(fr, image=img, borderwidth=0, highlightthickness=0,
                          command=lambda k=name: self._select_key(k)).pack(side="left", padx=4, pady=4)

        ttk.Separator(self, orient="horizontal").pack(fill="x")

        # POLISHED UPLOAD ROW with Auto-name
        upf = ttk.Frame(self); upf.pack(fill="x", **pad)
        ttk.Label(upf, text="Upload single:").pack(side="left")
        self.put_path = tk.StringVar()
        ttk.Entry(upf, textvariable=self.put_path).pack(side="left", fill="x", expand=True)
        ttk.Button(upf, text="Browse", command=self._browse_file).pack(side="left", padx=(6,10))
        ttk.Label(upf, text="as").pack(side="left")
        self.put_name = tk.StringVar(value="001.mp3")
        ttk.Entry(upf, textvariable=self.put_name, width=16).pack(side="left")
        self.btn_auto = ttk.Button(upf, text="Auto", command=self._auto_name)
        self.btn_auto.pack(side="left", padx=(6,0))
        self.btn_put = ttk.Button(upf, text="Upload", command=self._put)
        self.btn_put.pack(side="left", padx=(8,0))

        # FOLDER SYNC ROW
        syncf = ttk.Frame(self); syncf.pack(fill="x", **pad)
        ttk.Label(syncf, text="Folder sync:").pack(side="left")
        self.folder_var = tk.StringVar()
        ttk.Entry(syncf, textvariable=self.folder_var).pack(side="left", fill="x", expand=True)
        ttk.Button(syncf, text="Browse", command=self._browse_folder).pack(side="left", padx=(6,10))
        ttk.Label(syncf, text="Ext").pack(side="left")
        self.ext_cmb = ttk.Combobox(syncf, values=["mp3","wav","ogg"], state="readonly", width=6)
        self.ext_cmb.set("mp3"); self.ext_cmb.pack(side="left")
        self.btn_sync_seq = ttk.Button(syncf, text="Sync (001,002...)", command=self._sync_seq)
        self.btn_sync_seq.pack(side="left", padx=(8,0))
        self.btn_sync_pre = ttk.Button(syncf, text="Sync (preserve names)", command=self._sync_pre)
        self.btn_sync_pre.pack(side="left", padx=(8,0))

        # DOWNLOAD ROW
        getf = ttk.Frame(self); getf.pack(fill="x", **pad)
        ttk.Label(getf, text="Download selected to:").pack(side="left")
        self.out_dir = tk.StringVar()
        ttk.Entry(getf, textvariable=self.out_dir).pack(side="left", fill="x", expand=True)
        ttk.Button(getf, text="Browse", command=self._browse_outdir).pack(side="left", padx=(6,10))
        self.btn_get = ttk.Button(getf, text="Download", command=self._get)
        self.btn_get.pack(side="left")
        self.btn_del = ttk.Button(getf, text="Delete", command=self._delete)
        self.btn_del.pack(side="left", padx=(6,0))

        # PROGRESS BAR with percentage
        prog = ttk.Frame(self); prog.pack(fill="x", padx=8)
        self.pbar = ttk.Progressbar(prog, mode="determinate", maximum=100)
        self.pbar.pack(side="left", fill="x", expand=True)
        self.pct_lbl = ttk.Label(prog, text="")
        self.pct_lbl.pack(side="left", padx=(8,0))

        # NOTEBOOK with Files and Console tabs
        nb = ttk.Notebook(self); nb.pack(fill="both", expand=True, padx=8, pady=6)

        # Files tab
        files_tab = ttk.Frame(nb); nb.add(files_tab, text="Files")
        tblf = ttk.Frame(files_tab); tblf.pack(fill="both", expand=True)
        self.tree = ttk.Treeview(tblf, columns=("name","size"), show="headings", selectmode="browse")
        self.tree.heading("name", text="Filename"); self.tree.column("name", width=520, anchor="w")
        self.tree.heading("size", text="Size");     self.tree.column("size", width=120, anchor="e")
        self.tree.pack(side="left", fill="both", expand=True)
        vs = ttk.Scrollbar(tblf, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=vs.set); vs.pack(side="right", fill="y")

        # Console tab
        console_tab = ttk.Frame(nb); nb.add(console_tab, text="Console")
        self.log = tk.Text(console_tab, height=10, font=("Consolas",10), wrap="none")
        self.log.pack(fill="both", expand=True)

        self._apply_enable(False)  # disabled until connected

    def _wire_events(self):
        self.tree.bind("<Double-1>", lambda e: self._get())

    # ---- state/visuals ----
    def _set_status(self, state, msg):
        self.conn_state = state
        color = dict(DISCONNECTED="red", CONNECTING="orange",
                     CONNECTED="green", ERROR="firebrick").get(state, "black")
        self.led.itemconfig(1, fill=color)
        self.status_lbl.config(text=msg, foreground=color)
        self.update_idletasks()

    def _apply_enable(self, enabled):
        for b in (self.btn_ls, self.btn_put, self.btn_get, self.btn_del,
                  self.btn_sync_seq, self.btn_sync_pre, self.btn_exit, self.btn_scan,
                  self.btn_flag_on, self.btn_flag_off, self.btn_auto):
            b.config(state=("normal" if enabled else "disabled"))

    def _log(self, s):
        self.log.insert("end", s if s.endswith("\n") else s+"\n")
        self.log.see("end")

    def _clear_log(self):
        self.log.delete("1.0", "end")

    # ---- SD usage helpers ----
    def _sd_update(self, total, free):
        used = max(0, total - free)
        pct = int( (used / total) * 100 ) if total else 0
        self.sdbar["value"] = pct
        self.sd_lbl.config(text=f"SD: {cli.human_size(free)} free / {cli.human_size(total)}")

    def _refresh_stat(self):
        if not self.ser: return
        def task(): return cli.cmd_stat(self.ser)
        def ok(tup): self._sd_update(*tup)
        def err(e):  self._log(f"[warn] STAT: {e}")
        self._run_bg(task, ok, err)

    # ---- write status helpers ----
    def _write_update(self, enabled):
        color = "green" if enabled else "red"
        status = "ON" if enabled else "OFF"
        self.write_led.itemconfig(1, fill=color)
        self.write_lbl.config(text=f"Writes: {status}")

    def _refresh_write_status(self):
        if not self.ser: return
        def task(): return cli.cmd_status(self.ser)
        def ok(enabled): self._write_update(enabled)
        def err(e): self._log(f"[warn] STATUS: {e}")
        self._run_bg(task, ok, err)

    # ---- progress helpers ----
    def _progress(self, done, total):
        pct = int(done * 100 / max(1, total))
        self.pbar["value"] = pct
        self.pct_lbl.config(text=f"{pct}%")
        self.update_idletasks()

    def _progress_reset(self):
        self.pbar["value"] = 0
        self.pct_lbl.config(text="")

    # ---- common command wrappers (threaded) ----
    def _run_bg(self, target, on_ok=None, on_err=None):
        def _wrap():
            try:
                res = target()
                self.after(0, lambda r=res: (on_ok and on_ok(r)))
            except Exception as e:
                self.after(0, lambda err=e: (on_err and on_err(err)))
        threading.Thread(target=_wrap, daemon=True).start()

    # ---- connection ----
    def _refresh_port_combo(self):
        labels = [label for _, label in list_serial_ports()]
        self.port_cmb["values"] = labels
        if labels and not self.port_cmb.get():
            self.port_cmb.set(labels[0])

    def _auto_refresh_ports(self):
        self._refresh_port_combo()
        self.after(1500, self._auto_refresh_ports)

    def _connect(self):
        ports = list_serial_ports()
        label = self.port_cmb.get()
        port = None
        for dev, lab in ports:
            if lab == label: port = dev; break
        if not port:
            messagebox.showerror("No Port", "No serial ports found.")
            return
        try:
            baud = int(self.baud_var.get())
        except:
            messagebox.showerror("Baud", "Invalid baud rate.")
            return

        self._set_status("CONNECTING", f"Connecting to {port}@{baud} …")
        self.btn_connect.config(state="disabled")

        def task():
            ser = cli.open_serial(port, baud)
            cli.handshake(ser)  # enters DATA_MODE
            return ser

        def ok(ser):
            self.ser = ser
            self._set_status("CONNECTED", "Connected")
            self._apply_enable(True)
            self._log("[ok] connected & in data mode")
            self._refresh_stat()  # Get SD usage
            self._refresh_write_status()  # Get write status
            self.btn_connect.config(state="normal")

        def err(e):
            self._set_status("ERROR", f"Connect failed: {e}")
            self._apply_enable(False)
            self._log(f"[err] connect: {e}")
            self.btn_connect.config(state="normal")

        self._run_bg(task, ok, err)

    def _disconnect(self):
        if self.ser:
            try: self.ser.close()
            except: pass
            self.ser = None
        self._set_status("DISCONNECTED", "Disconnected")
        self._apply_enable(False)
        self._log("[i] disconnected")
        # Reset SD indicator
        self.sdbar["value"] = 0
        self.sd_lbl.config(text="SD: -- / --")
        # Reset write indicator
        self.write_led.itemconfig(1, fill="gray")
        self.write_lbl.config(text="Writes: --")

    # ---- keypad & scans ----
    def _select_key(self, keyname):
        self.key_cmb.set(keyname)
        self._log(f"[i] key selected: {keyname}")

    def _scan_keys(self):
        if not self.ser: return
        bank = self.bank_cmb.get()
        self._log(f"[i] scanning keys on /audio/{bank}/* ...")

        def task():
            found = set()
            for k in KEY_DEFAULTS:
                try:
                    if cli.cmd_ls(self.ser, bank, k):
                        found.add(k)
                except Exception:
                    pass
            return sorted(found, key=lambda s: (len(s) > 1, s))  # A..Z then specials

        def ok(keys):
            if keys:
                self.key_cmb["values"] = keys
                self.key_cmb.set(keys[0])
                self._log(f"[ok] found {len(keys)} key(s)")
            else:
                self._log("[i] no keys with files found")

        def err(e):
            self._log(f"[err] scan: {e}")

        self._run_bg(task, ok, err)

    # ---- auto-name functionality ----
    def _auto_name(self):
        ext = (os.path.splitext(self.put_path.get())[1].lstrip(".") or self.ext_cmb.get() or "mp3").lower()
        # look at current table; find largest NNN
        mx = 0
        for item in self.tree.get_children():
            name = str(self.tree.item(item)["values"][0]).upper()
            m = re.match(r"^(\d{3})\.", name)
            if m: mx = max(mx, int(m.group(1)))
        self.put_name.set(f"{mx+1:03d}.{ext}")

    # ---- device ops ----
    def _ls(self):
        if not self.ser: return
        bank = self.bank_cmb.get(); key = self.key_cmb.get()
        self._log(f"[i] listing /audio/{bank}/{key}")

        def task(): return cli.cmd_ls(self.ser, bank, key)

        def ok(items):
            # clear table and fill
            for i in self.tree.get_children(): self.tree.delete(i)
            for name, sz in items:
                self.tree.insert("", "end", values=(name, f"{sz:,}"))
            self._log(f"[ok] {len(items)} item(s)")

        def err(e):
            self._log(f"[err] ls: {e}")

        self._run_bg(task, ok, err)

    def _exit_data_mode(self):
        if not self.ser: return
        self._log("[i] exiting data mode")

        def task(): return cli.cmd_exit(self.ser)

        def ok(_):
            self._log("[ok] exited data mode")
            self._disconnect()

        def err(e):
            self._log(f"[err] exit: {e}")

        self._run_bg(task, ok, err)

    # ==== SEGMENT C3: flag button handlers ====
    def _flag_on(self):
        if not self.ser: return
        self._log("[i] creating /config/allow_writes.flag")
        def task(): return cli.cmd_flag(self.ser, True)
        def ok(_): 
            self._log("[ok] writes enabled")
            self._refresh_write_status()  # Update indicator
        def err(e): self._log(f"[err] flag on: {e}")
        self._run_bg(task, ok, err)

    def _flag_off(self):
        if not self.ser: return
        self._log("[i] removing /config/allow_writes.flag")
        def task(): return cli.cmd_flag(self.ser, False)
        def ok(_): 
            self._log("[ok] writes disabled")
            self._refresh_write_status()  # Update indicator
        def err(e): self._log(f"[err] flag off: {e}")
        self._run_bg(task, ok, err)

    def _browse_file(self):
        path = filedialog.Open(self, filetypes=[("Audio","*.mp3 *.wav *.ogg"),("All","*.*")]).show()
        if path: self.put_path.set(path)

    def _browse_folder(self):
        d = filedialog.askdirectory()
        if d: self.folder_var.set(d)

    def _browse_outdir(self):
        d = filedialog.askdirectory()
        if d: self.out_dir.set(d)

    def _put(self):
        if not self.ser: return
        bank = self.bank_cmb.get(); key = self.key_cmb.get()
        dest = (self.put_name.get() or "").strip()
        path = self.put_path.get()
        if not os.path.isfile(path):
            messagebox.showerror("Upload", "Choose a valid file."); return
        if not dest: messagebox.showerror("Upload", "Enter a destination filename."); return

        self._log(f"[put] {path} -> /audio/{bank}/{key}/{dest}")
        self._progress_reset()

        def task(): 
            return cli.cmd_put(self.ser, bank, key, dest, path, use_crc=True,
                               on_progress=lambda d,t: self.after(0, self._progress, d, t))

        def ok(_):
            self._log("[ok] upload complete"); self._refresh_stat(); self._progress_reset()

        def err(e):
            self._log(f"[err] put: {e}"); self._progress_reset()

        self._run_bg(task, ok, err)

    def _get(self):
        if not self.ser: return
        bank = self.bank_cmb.get(); key = self.key_cmb.get()
        sel = self.tree.selection()
        if not sel:
            messagebox.showinfo("Download", "Select a file in the list."); return
        name = self.tree.item(sel[0])["values"][0]
        outdir = self.out_dir.get() or "."
        ensure_dir(outdir)
        outpath = os.path.join(outdir, name)
        self._log(f"[get] {name} -> {outpath}")
        self._progress_reset()

        def task(): 
            return cli.cmd_get(self.ser, bank, key, name, outpath,
                               on_progress=lambda d,t: self.after(0, self._progress, d, t))

        def ok(_):
            self._log("[ok] download complete"); self._progress_reset()

        def err(e):
            self._log(f"[err] get: {e}"); self._progress_reset()

        self._run_bg(task, ok, err)

    def _delete(self):
        if not self.ser: return
        bank = self.bank_cmb.get(); key = self.key_cmb.get()
        sel = self.tree.selection()
        if not sel: return
        name = self.tree.item(sel[0])["values"][0]
        if not messagebox.askyesno("Delete", f"Delete {name}?"): return

        self._log(f"[del] {name}")

        def task(): return cli.cmd_del(self.ser, bank, key, name)

        def ok(_):
            self._log("[ok] delete done"); self._ls(); self._refresh_stat()

        def err(e):
            self._log(f"[err] del: {e}")

        self._run_bg(task, ok, err)

    def _sync_seq(self):
        if not self.ser: return
        folder = self.folder_var.get()
        if not os.path.isdir(folder):
            messagebox.showerror("Sync", "Choose a folder."); return
        bank = self.bank_cmb.get(); key = self.key_cmb.get(); ext = self.ext_cmb.get()
        self._log(f"[sync] seq from {folder} as 001.{ext}, 002.{ext} ...")

        def task(): return cli.cmd_sync_seq(self.ser, bank, key, folder, ext=ext)

        def ok(_):
            self._log("[ok] sync seq complete"); self._refresh_stat()

        def err(e):
            self._log(f"[err] sync seq: {e}")

        self._run_bg(task, ok, err)

    def _sync_pre(self):
        if not self.ser: return
        folder = self.folder_var.get()
        if not os.path.isdir(folder):
            messagebox.showerror("Sync", "Choose a folder."); return
        bank = self.bank_cmb.get(); key = self.key_cmb.get(); ext = self.ext_cmb.get()
        self._log(f"[sync] preserve from {folder} with .{ext} files")

        def task(): return cli.cmd_sync_preserve(self.ser, bank, key, folder, ext=ext)

        def ok(_):
            self._log("[ok] sync preserve complete"); self._refresh_stat()

        def err(e):
            self._log(f"[err] sync preserve: {e}")

        self._run_bg(task, ok, err)

def main():
    app = App()
    app.mainloop()

if __name__ == "__main__":
    main()
