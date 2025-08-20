# data_gui_tk.py — GUI for your Tactile Data Tool (Tkinter version)
# Requires: pyserial, pillow, your existing data_cli.py in the same folder
# Linux users may need: sudo apt install python3-tk

import os, sys, threading, time
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
        self.geometry("950x720")
        self.minsize(900, 640)

        self.ser = None
        self.conn_state = "DISCONNECTED"  # CONNECTING | CONNECTED | ERROR

        self._build_ui()
        self._wire_events()

        self.after(1000, self._auto_refresh_ports)  # hot-plug polling

    # ---- UI construction ----
    def _build_ui(self):
        pad = dict(padx=8, pady=6)

        # STATUS BAR
        bar = ttk.Frame(self); bar.pack(fill="x", **pad)
        self.led = tk.Canvas(bar, width=14, height=14, highlightthickness=0)
        self.led.create_oval(2,2,12,12, fill="red", outline="")
        self.led.pack(side="left")
        self.status_lbl = ttk.Label(bar, text="Disconnected", foreground="red")
        self.status_lbl.pack(side="left", padx=(6,0))
        ttk.Button(bar, text="Clear Log", command=self._clear_log).pack(side="right")

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
        self.bank_cmb = ttk.Combobox(row2, values=["human","generated","GENERA~1"], state="readonly", width=12)
        self.bank_cmb.set("human"); self.bank_cmb.pack(side="left", padx=(6,10))
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

        # FILE TABLE
        tblf = ttk.Frame(self); tblf.pack(fill="both", expand=True, **pad)
        self.tree = ttk.Treeview(tblf, columns=("name","size"), show="headings", selectmode="browse")
        self.tree.heading("name", text="Filename"); self.tree.column("name", width=520, anchor="w")
        self.tree.heading("size", text="Size"); self.tree.column("size", width=120, anchor="e")
        self.tree.pack(side="left", fill="both", expand=True)
        vs = ttk.Scrollbar(tblf, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=vs.set); vs.pack(side="right", fill="y")

        ttk.Separator(self, orient="horizontal").pack(fill="x")

        # TRANSFERS
        upf = ttk.Frame(self); upf.pack(fill="x", **pad)
        ttk.Label(upf, text="Upload single:").pack(side="left")
        self.put_path = tk.StringVar()
        ttk.Entry(upf, textvariable=self.put_path).pack(side="left", fill="x", expand=True)
        ttk.Button(upf, text="Browse", command=self._browse_file).pack(side="left", padx=(6,10))
        ttk.Label(upf, text="as").pack(side="left")
        self.put_name = tk.StringVar(value="001.mp3")
        ttk.Entry(upf, textvariable=self.put_name, width=16).pack(side="left")
        self.btn_put = ttk.Button(upf, text="Upload", command=self._put)
        self.btn_put.pack(side="left", padx=(8,0))

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

        getf = ttk.Frame(self); getf.pack(fill="x", **pad)
        ttk.Label(getf, text="Download selected to:").pack(side="left")
        self.out_dir = tk.StringVar()
        ttk.Entry(getf, textvariable=self.out_dir).pack(side="left", fill="x", expand=True)
        ttk.Button(getf, text="Browse", command=self._browse_outdir).pack(side="left", padx=(6,10))
        self.btn_get = ttk.Button(getf, text="Download", command=self._get)
        self.btn_get.pack(side="left")
        self.btn_del = ttk.Button(getf, text="Delete", command=self._delete)
        self.btn_del.pack(side="left", padx=(6,0))

        # PROGRESS + LOG
        bot = ttk.Frame(self); bot.pack(fill="both", expand=True, **pad)
        self.pbar = ttk.Progressbar(bot, mode="indeterminate")
        self.pbar.pack(fill="x")
        self.log = tk.Text(bot, height=10, font=("Consolas",10), wrap="none")
        self.log.pack(fill="both", expand=True)

        self._apply_enable(False)  # disabled until connected

    def _wire_events(self):
        self.tree.bind("<Double-1>", lambda e: self._get())
        
        ttk.Button(conn_frame, text="Refresh", command=self.refresh_ports).pack(side=tk.LEFT, padx=5)
        
        ttk.Label(conn_frame, text="Baud:").pack(side=tk.LEFT, padx=(10,0))
        self.baud_var = tk.StringVar(value=str(DEFAULT_BAUD))
        ttk.Entry(conn_frame, textvariable=self.baud_var, width=8).pack(side=tk.LEFT, padx=5)
        
        self.connect_btn = ttk.Button(conn_frame, text="Connect", command=self.connect)
        self.connect_btn.pack(side=tk.LEFT, padx=5)
        
        self.disconnect_btn = ttk.Button(conn_frame, text="Disconnect", command=self.disconnect)
        self.disconnect_btn.pack(side=tk.LEFT, padx=5)
        
        self.status_var = tk.StringVar(value="Not connected")
        ttk.Label(conn_frame, textvariable=self.status_var).pack(side=tk.LEFT, padx=10)
        
        # Control frame
        ctrl_frame = ttk.Frame(self.root)
        ctrl_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(ctrl_frame, text="Bank:").pack(side=tk.LEFT)
        self.bank_var = tk.StringVar(value="human")
        bank_combo = ttk.Combobox(ctrl_frame, textvariable=self.bank_var, values=["human", "generated", "GENERA~1"], width=12)
        bank_combo.pack(side=tk.LEFT, padx=5)
        
        ttk.Label(ctrl_frame, text="Key:").pack(side=tk.LEFT, padx=(10,0))
        self.key_var = tk.StringVar(value="A")
        ttk.Entry(ctrl_frame, textvariable=self.key_var, width=12).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(ctrl_frame, text="List Files", command=self.list_files).pack(side=tk.LEFT, padx=5)
        ttk.Button(ctrl_frame, text="Exit Data Mode", command=self.exit_data_mode).pack(side=tk.LEFT, padx=5)
        ttk.Button(ctrl_frame, text="Create Flag", command=self.create_flag).pack(side=tk.LEFT, padx=5)
        
        # File table
        table_frame = ttk.Frame(self.root)
        table_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        self.tree = ttk.Treeview(table_frame, columns=("Size",), show="tree headings")
        self.tree.heading("#0", text="Filename")
        self.tree.heading("Size", text="Size")
        self.tree.column("#0", width=300)
        self.tree.column("Size", width=100)
        
        scrollbar = ttk.Scrollbar(table_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Upload frame
        upload_frame = ttk.Frame(self.root)
        upload_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(upload_frame, text="Upload:").pack(side=tk.LEFT)
        self.upload_path_var = tk.StringVar()
        ttk.Entry(upload_frame, textvariable=self.upload_path_var, width=40).pack(side=tk.LEFT, padx=5)
        ttk.Button(upload_frame, text="Browse", command=self.browse_file).pack(side=tk.LEFT, padx=5)
        
        ttk.Label(upload_frame, text="as:").pack(side=tk.LEFT, padx=(10,0))
        self.upload_name_var = tk.StringVar(value="001.mp3")
        ttk.Entry(upload_frame, textvariable=self.upload_name_var, width=15).pack(side=tk.LEFT, padx=5)
        ttk.Button(upload_frame, text="Upload", command=self.upload_file).pack(side=tk.LEFT, padx=5)
        
        # Sync frame
        sync_frame = ttk.Frame(self.root)
        sync_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(sync_frame, text="Sync folder:").pack(side=tk.LEFT)
        self.folder_var = tk.StringVar()
        ttk.Entry(sync_frame, textvariable=self.folder_var, width=40).pack(side=tk.LEFT, padx=5)
        ttk.Button(sync_frame, text="Browse", command=self.browse_folder).pack(side=tk.LEFT, padx=5)
        
        ttk.Label(sync_frame, text="Ext:").pack(side=tk.LEFT, padx=(10,0))
        self.ext_var = tk.StringVar(value="mp3")
        ttk.Entry(sync_frame, textvariable=self.ext_var, width=6).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(sync_frame, text="Sync (001,002...)", command=self.sync_seq).pack(side=tk.LEFT, padx=5)
        ttk.Button(sync_frame, text="Sync (preserve)", command=self.sync_preserve).pack(side=tk.LEFT, padx=5)
        
        # Download frame
        dl_frame = ttk.Frame(self.root)
        dl_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(dl_frame, text="Download to:").pack(side=tk.LEFT)
        self.download_path_var = tk.StringVar()
        ttk.Entry(dl_frame, textvariable=self.download_path_var, width=40).pack(side=tk.LEFT, padx=5)
        ttk.Button(dl_frame, text="Browse", command=self.browse_download_folder).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(dl_frame, text="Download", command=self.download_file).pack(side=tk.LEFT, padx=5)
        ttk.Button(dl_frame, text="Delete", command=self.delete_file).pack(side=tk.LEFT, padx=5)
        
        # Log frame
        log_frame = ttk.Frame(self.root)
        log_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        ttk.Label(log_frame, text="Log:").pack(anchor=tk.W)
        self.log_text = scrolledtext.ScrolledText(log_frame, height=8, font=("Consolas", 10))
        self.log_text.pack(fill=tk.BOTH, expand=True)
        
        ttk.Button(log_frame, text="Clear Log", command=self.clear_log).pack(pady=5)
        
    def log(self, message):
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.see(tk.END)
        self.root.update_idletasks()
        
    def refresh_ports(self):
        ports = [(p.device, f"{p.device} — {p.description}") for p in list_ports.comports()]
        self.port_combo['values'] = [label for _, label in ports]
        if ports:
            self.port_combo.set(ports[0][1])
        self.port_data = ports
        self.log(f"Found {len(ports)} serial ports")
        
    def connect(self):
        try:
            # Get actual port device from label
            label = self.port_var.get()
            port = None
            for dev, lab in self.port_data:
                if lab == label:
                    port = dev
                    break
            
            if not port:
                self.log("[err] No port selected")
                return
                
            baud = int(self.baud_var.get())
            self.ser = cli.open_serial(port, baud)
            cli.handshake(self.ser)
            
            self.status_var.set(f"Connected {port}@{baud}")
            self.log(f"[ok] Connected {port}@{baud}")
            
        except Exception as e:
            self.status_var.set("Connection failed")
            self.log(f"[err] Connect failed: {e}")
            
    def disconnect(self):
        if self.ser:
            try:
                self.ser.close()
            except:
                pass
            self.ser = None
            self.status_var.set("Disconnected")
            self.log("[i] Disconnected")
            
    def exit_data_mode(self):
        if not self.ser:
            self.log("[err] Not connected")
            return
        try:
            cli.cmd_exit(self.ser)
            self.log("[ok] EXIT sent (device leaves data mode)")
        except Exception as e:
            self.log(f"[err] EXIT failed: {e}")
            
    def create_flag(self):
        if not self.ser:
            self.log("[err] Not connected")
            return
        try:
            self.log("[flag] Creating /config/allow_writes.flag")
            cli.cmd_put(self.ser, "config", "", "allow_writes.flag", None, use_crc=False, empty_file=True)
            self.log("[ok] Write flag created - PUT/DELETE now enabled")
        except Exception as e:
            self.log(f"[err] Flag creation failed: {e}")
            
    def list_files(self):
        if not self.ser:
            self.log("[err] Not connected")
            return
        try:
            bank = self.bank_var.get()
            key = self.key_var.get().strip()
            self.log(f"[i] Listing /audio/{bank}/{key}")
            
            items = cli.cmd_ls(self.ser, bank, key)
            self.current_items = items
            
            # Clear and populate tree
            for item in self.tree.get_children():
                self.tree.delete(item)
                
            for name, size in items:
                self.tree.insert("", tk.END, text=name, values=(f"{size:,}",))
                
            self.log(f"[ok] {len(items)} item(s)")
            
        except Exception as e:
            self.log(f"[err] List failed: {e}")
            
    def browse_file(self):
        filename = filedialog.askopenfilename(
            filetypes=[("Audio files", "*.mp3 *.wav *.ogg"), ("All files", "*.*")]
        )
        if filename:
            self.upload_path_var.set(filename)
            
    def browse_folder(self):
        folder = filedialog.askdirectory()
        if folder:
            self.folder_var.set(folder)
            
    def browse_download_folder(self):
        folder = filedialog.askdirectory()
        if folder:
            self.download_path_var.set(folder)
            
    def upload_file(self):
        if not self.ser:
            self.log("[err] Not connected")
            return
            
        path = self.upload_path_var.get()
        dest = self.upload_name_var.get().strip()
        
        if not path or not os.path.isfile(path):
            self.log("[err] Choose a file to upload")
            return
        if not dest:
            self.log("[err] Choose a destination filename")
            return
            
        bank = self.bank_var.get()
        key = self.key_var.get().strip()
        
        def _upload():
            try:
                self.log(f"[put] {path} -> /audio/{bank}/{key}/{dest}")
                cli.cmd_put(self.ser, bank, key, dest, path, use_crc=True)
                self.log("[ok] Upload complete")
            except Exception as e:
                self.log(f"[err] Upload failed: {e}")
                
        threading.Thread(target=_upload, daemon=True).start()
        
    def sync_seq(self):
        self._sync(preserve=False)
        
    def sync_preserve(self):
        self._sync(preserve=True)
        
    def _sync(self, preserve=False):
        if not self.ser:
            self.log("[err] Not connected")
            return
            
        folder = self.folder_var.get()
        ext = self.ext_var.get().lstrip(".") or "mp3"
        
        if not folder or not os.path.isdir(folder):
            self.log("[err] Choose a folder to sync")
            return
            
        bank = self.bank_var.get()
        key = self.key_var.get().strip()
        
        def _sync_thread():
            try:
                if preserve:
                    self.log(f"[sync] Preserve names from {folder} (*.{ext})")
                    cli.cmd_sync_preserve(self.ser, bank, key, folder, ext=ext, dry_run=False)
                else:
                    self.log(f"[sync] Sequential from {folder} as 001.{ext}, 002.{ext}...")
                    cli.cmd_sync_seq(self.ser, bank, key, folder, ext=ext, start=1, dry_run=False)
                self.log("[ok] Sync complete")
            except Exception as e:
                self.log(f"[err] Sync failed: {e}")
                
        threading.Thread(target=_sync_thread, daemon=True).start()
        
    def download_file(self):
        if not self.ser:
            self.log("[err] Not connected")
            return
            
        selection = self.tree.selection()
        if not selection:
            self.log("[err] Select a file in the table")
            return
            
        item = self.tree.item(selection[0])
        filename = item['text']
        
        outdir = self.download_path_var.get() or "."
        os.makedirs(outdir, exist_ok=True)
        outpath = os.path.join(outdir, filename)
        
        bank = self.bank_var.get()
        key = self.key_var.get().strip()
        
        def _download():
            try:
                self.log(f"[get] {filename} -> {outpath}")
                cli.cmd_get(self.ser, bank, key, filename, outpath)
                self.log("[ok] Download complete")
            except Exception as e:
                self.log(f"[err] Download failed: {e}")
                
        threading.Thread(target=_download, daemon=True).start()
        
    def delete_file(self):
        if not self.ser:
            self.log("[err] Not connected")
            return
            
        selection = self.tree.selection()
        if not selection:
            self.log("[err] Select a file in the table")
            return
            
        item = self.tree.item(selection[0])
        filename = item['text']
        
        if not messagebox.askyesno("Confirm Delete", f"Delete {filename}?"):
            return
            
        bank = self.bank_var.get()
        key = self.key_var.get().strip()
        
        def _delete():
            try:
                self.log(f"[del] {filename}")
                cli.cmd_del(self.ser, bank, key, filename)
                self.log("[ok] Delete complete")
                # Refresh file list
                self.root.after(100, self.list_files)
            except Exception as e:
                self.log(f"[err] Delete failed: {e}")
                
        threading.Thread(target=_delete, daemon=True).start()
        
    def clear_log(self):
        self.log_text.delete(1.0, tk.END)

def main():
    root = tk.Tk()
    app = TactileDataGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()
