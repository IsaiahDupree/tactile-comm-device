# data_cli.py — UNO R4 WiFi + VS1053 data-mode CLI (PUT/GET/DEL/LS)
# pip install pyserial

import argparse, sys, time, os, zlib, glob
from typing import Optional, Tuple, List

try:
    import serial
    from serial.tools import list_ports
except Exception as e:
    print("pyserial is required: pip install pyserial")
    raise

# ---- protocol knobs (match firmware) ----
HANDSHAKE_LINE = "^DATA? v1"
HANDSHAKE_OK   = "DATA:OK v1"
IDLE_TIMEOUT_S = 10.0
PROGRESS_MIN_INTERVAL = 0.05  # seconds between progress callbacks (~20 Hz)
LINE_TIMEOUT_S = 10
RW_CHUNK = 8192              # 512–2048 is fine
ENC = "utf-8"

def now() -> float: return time.monotonic()

def crc32_file(path: str) -> int:
    crc = 0
    with open(path, "rb") as f:
        while True:
            b = f.read(64 * 1024)
            if not b: break
            crc = zlib.crc32(b, crc)
    return crc & 0xFFFFFFFF

def human_size(n: int) -> str:
    for u in ["B","KB","MB","GB","TB"]:
        if n < 1024: return f"{n:.0f}{u}"
        n /= 1024
    return f"{n:.1f}PB"

def open_serial(port: str, baud: int = 115200, to_s: float = 1.0) -> serial.Serial:
    ser = serial.Serial(port=port, baudrate=baud, timeout=to_s, write_timeout=to_s)
    # small settle + drain
    time.sleep(0.2)
    drain_input(ser)
    return ser

def drain_input(ser: serial.Serial):
    time.sleep(0.05)
    while ser.in_waiting:
        ser.read(ser.in_waiting)
        time.sleep(0.01)

def send_line(ser: serial.Serial, line: str):
    ser.write((line + "\n").encode(ENC))

def read_line(ser: serial.Serial, timeout_s: float = LINE_TIMEOUT_S) -> Optional[str]:
    """Read a single \n-terminated ASCII line (strip CR/LF)."""
    buf = bytearray()
    deadline = now() + timeout_s
    while now() < deadline:
        b = ser.read(1)
        if not b: 
            continue
        if b == b'\n':
            # strip optional \r
            if buf.endswith(b'\r'):
                buf[:] = buf[:-1]
            try:
                return buf.decode(ENC, errors="replace")
            finally:
                buf.clear()
        else:
            buf.extend(b)
    return None

def expect_line(ser: serial.Serial, startswith: str, timeout_s: float = LINE_TIMEOUT_S) -> str:
    """Keep reading lines until we find one starting with token or timeout."""
    deadline = now() + timeout_s
    while now() < deadline:
        line = read_line(ser, timeout_s=max(0.1, deadline - now()))
        if line is None: 
            continue
        if line.startswith(startswith):
            return line
        # print spurious lines to help debugging
        print(f"[device] {line}")
    raise TimeoutError(f"Timed out waiting for line starting with: {startswith}")

def handshake(ser: serial.Serial):
    send_line(ser, HANDSHAKE_LINE)
    line = expect_line(ser, HANDSHAKE_OK, timeout_s=5.0)
    print(f"[ok] {line}")

def cmd_ls(ser: serial.Serial, bank: str, key: str) -> List[Tuple[str,int]]:
    send_line(ser, f"LS {bank} {key}")
    items = []
    while True:
        line = read_line(ser, timeout_s=LINE_TIMEOUT_S)
        if line is None:
            raise TimeoutError("No response to LS")
        if line == "LS:DONE":
            break
        if line == "LS:NODIR":
            print("[!] directory not found on SD")
            return []
        # format: "<name> <size>"
        try:
            name, size = line.rsplit(" ", 1)
            items.append((name, int(size)))
        except Exception:
            print(f"[device] {line}")
    return items

def cmd_del(ser: serial.Serial, bank: str, key: str, fname: str):
    send_line(ser, f"DEL {bank} {key} {fname}")
    line = read_line(ser, timeout_s=LINE_TIMEOUT_S)
    if line is None:
        raise TimeoutError("No response to DEL")
    if line.strip() == "DEL:OK":
        print("[ok] deleted")
    elif line.strip() == "ERR:WRITELOCK":
        print("[err] writes are locked — add /config/allow_writes.flag on SD")
        sys.exit(2)
    else:
        print(f"[device] {line}")

def cmd_exit(ser: serial.Serial):
    send_line(ser, "EXIT")
    # device replies DATA:BYE, then leaves DATA_MODE
    line = read_line(ser, timeout_s=3.0)
    if line:
        print(f"[device] {line}")

def cmd_put(ser: serial.Serial, bank: str, key: str, fname: str, local_path: str, use_crc: bool = True, empty_file: bool = False, on_progress=None):
    if empty_file:
        size = 0
        crc = 0 if use_crc else None
    else:
        if not os.path.isfile(local_path):
            print(f"[err] file not found: {local_path}")
            sys.exit(2)
        size = os.path.getsize(local_path)
        crc = crc32_file(local_path) if use_crc else None

    # announce
    if use_crc:
        send_line(ser, f"PUT {bank} {key} {fname} {size} {crc}")
    else:
        send_line(ser, f"PUT {bank} {key} {fname} {size}")

    # wait for READY or error
    while True:
        line = read_line(ser, timeout_s=LINE_TIMEOUT_S)
        if line is None:
            raise TimeoutError("No response to PUT")
        if line == "PUT:READY":
            break
        if line == "ERR:WRITELOCK":
            print("[err] writes are locked — add /config/allow_writes.flag on SD")
            sys.exit(2)
        if line.startswith("ERR:"):
            print(f"[device] {line}")
            sys.exit(2)
        print(f"[device] {line}")

    sent = 0
    t0 = now()
    last_emit = 0.0
    if empty_file:
        # No file to read for empty files
        pass
    else:
        with open(local_path, "rb") as f:
            while sent < size:
                chunk = f.read(min(RW_CHUNK, size - sent))
                if not chunk: break
                n = ser.write(chunk)
                if n != len(chunk):
                    raise IOError("Serial write short")
                sent += n

                if on_progress:
                    t = now()
                    if t - last_emit >= PROGRESS_MIN_INTERVAL or sent == size:
                        on_progress(sent, size)
                        last_emit = t
                else:
                    # progress to console only when no callback
                    pct = (sent / size) * 100
                    elapsed = max(1e-6, now() - t0)
                    rate = sent / elapsed
                    sys.stdout.write(f"\r[put] {sent}/{size} bytes ({pct:5.1f}%) @ {human_size(rate)}/s")
                    sys.stdout.flush()
    if not on_progress:
        print()

    # final status
    line = read_line(ser, timeout_s=LINE_TIMEOUT_S)
    if line is None:
        raise TimeoutError("No final response after PUT")
    if line == "PUT:DONE":
        if not on_progress:
            dt = now() - t0
            print(f"[ok] upload complete in {dt:.2f}s, avg {human_size(size/dt)}/s")
    else:
        print(f"[device] {line}")
        if line == "ERR:CRC":
            print("[err] device CRC mismatch — retry (check cable/baud).")
            sys.exit(2)
        sys.exit(2)

def cmd_get(ser: serial.Serial, bank: str, key: str, fname: str, out_path: str, on_progress=None):
    send_line(ser, f"GET {bank} {key} {fname}")
    hdr = read_line(ser, timeout_s=LINE_TIMEOUT_S)
    if hdr is None:
        raise TimeoutError("No response to GET")
    if hdr == "GET:NOK":
        print("[err] file not found on device")
        sys.exit(2)
    if not hdr.startswith("GET:SIZE "):
        print(f"[device] {hdr}")
        sys.exit(2)

    parts = hdr.split()
    expect_sz = int(parts[1])
    expect_crc = int(parts[2]) if len(parts) >= 3 else None

    t0 = now()
    got = 0
    last_emit = 0.0
    crc = 0
    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
    with open(out_path, "wb") as out:
        while got < expect_sz:
            want = min(RW_CHUNK, expect_sz - got)
            chunk = ser.read(want)
            if not chunk:
                # allow a little slack but not infinite
                if now() - t0 > IDLE_TIMEOUT_S:
                    raise TimeoutError("Timed out while receiving file")
                continue
            out.write(chunk)
            got += len(chunk)
            crc = zlib.crc32(chunk, crc)
            
            if on_progress:
                t = now()
                if t - last_emit >= PROGRESS_MIN_INTERVAL or got == expect_sz:
                    on_progress(got, expect_sz)
                    last_emit = t
            else:
                # progress to console only when no callback
                pct = (got / expect_sz) * 100
                elapsed = max(1e-6, now() - t0)
                rate = got / elapsed
                sys.stdout.write(f"\r[get] {got}/{expect_sz} bytes ({pct:5.1f}%) @ {human_size(rate)}/s")
                sys.stdout.flush()
    if not on_progress:
        print()

    if expect_crc is not None:
        crc &= 0xFFFFFFFF
        if crc != expect_crc:
            print(f"[err] CRC mismatch: host {crc:#010x} != device {expect_crc:#010x}")
            sys.exit(2)

    if not on_progress:
        dt = now() - t0
        print(f"[ok] download complete in {dt:.2f}s, avg {human_size(expect_sz/dt)}/s")

# ==== SEGMENT 1: data_cli sync helpers ====

def _iter_local(folder: str, ext: str) -> List[str]:
    ext = ext.lstrip(".")
    return sorted(glob.glob(os.path.join(folder, f"*.{ext}"), recursive=False))

def _ls_map(ser: serial.Serial, bank: str, key: str) -> dict:
    # name -> size
    return {name: sz for name, sz in cmd_ls(ser, bank, key)}

def cmd_sync_seq(ser: serial.Serial, bank: str, key: str, folder: str,
                 ext: str = "mp3", start: int = 1, dry_run: bool = False):
    if not os.path.isdir(folder):
        print(f"[err] folder not found: {folder}"); sys.exit(2)
    remote = _ls_map(ser, bank, key)
    local_files = _iter_local(folder, ext)
    if not local_files:
        print("[note] nothing to sync (no local files)"); return
    i = start
    for path in local_files:
        remote_name = f"{i:03d}.{ext}"
        local_size = os.path.getsize(path)
        remote_size = remote.get(remote_name)
        if remote_size == local_size:
            print(f"[skip] {remote_name} — up to date ({local_size} bytes)")
        else:
            print(f"[sync] {remote_name} — local {local_size} vs device {remote_size}")
            if not dry_run:
                cmd_put(ser, bank, key, remote_name, path, use_crc=True)
        i += 1

def cmd_sync_preserve(ser: serial.Serial, bank: str, key: str, folder: str,
                      ext: str = "mp3", dry_run: bool = False):
    if not os.path.isdir(folder):
        print(f"[err] folder not found: {folder}"); sys.exit(2)
    remote = _ls_map(ser, bank, key)
    local_files = _iter_local(folder, ext)
    if not local_files:
        print("[note] nothing to sync (no local files)"); return
    for path in local_files:
        name = os.path.basename(path)
        local_size = os.path.getsize(path)
        remote_size = remote.get(name)
        if remote_size == local_size:
            print(f"[skip] {name} — up to date ({local_size} bytes)")
        else:
            print(f"[sync] {name} — local {local_size} vs device {remote_size}")
            if not dry_run:
                cmd_put(ser, bank, key, name, path, use_crc=True)

# ==== SEGMENT B1: flag helpers ====
def cmd_flag(ser, on: bool):
    cli = "FLAG ON" if on else "FLAG OFF"
    send_line(ser, cli)  # reuse existing send_line from data_cli
    line = read_line(ser, timeout_s=5.0)
    if not line:
        raise TimeoutError("No response to FLAG")
    if line.startswith("FLAG:ON") and on:  return True
    if line.startswith("FLAG:OFF") and not on: return True
    if line.startswith("FLAG:ERR"):
        raise RuntimeError(line)
    return False

def cmd_stat(ser):
    send_line(ser, "STAT")
    line = expect_line(ser, "STAT ", timeout_s=5.0)   # skips unrelated lines
    _, tot, fre = line.split()
    return int(tot), int(fre)

def cmd_status(ser):
    send_line(ser, "STATUS")
    line = read_line(ser, timeout_s=5.0)
    if not line:
        raise TimeoutError("No response to STATUS")
    if line.startswith("STATUS WRITES="):
        return "ON" in line
    raise RuntimeError(line)

def main():
    ap = argparse.ArgumentParser(description="UNO R4 Data-Mode CLI (PUT/GET/DEL/LS/EXIT)")
    sub = ap.add_subparsers(dest="cmd", required=True)

    pa_ports = sub.add_parser("ports", help="list available serial ports")

    def add_common(p):
        p.add_argument("-p","--port", required=True, help="serial port (e.g., COM6 or /dev/ttyACM0)")
        p.add_argument("-b","--baud", type=int, default=115200, help="baud rate (default 115200)")
        p.add_argument("--no-handshake", action="store_true", help="skip ^DATA? v1 handshake (if already in data mode)")

    pa_ls = sub.add_parser("ls", help="list files in /audio/<bank>/<KEY>")
    add_common(pa_ls)
    pa_ls.add_argument("bank", choices=["human","generated","GENERA~1"])
    pa_ls.add_argument("key", help="KEY folder (e.g., A, SHIFT, PERIOD)")

    pa_del = sub.add_parser("del", help="delete a file on the device")
    add_common(pa_del)
    pa_del.add_argument("bank", choices=["human","generated","GENERA~1"])
    pa_del.add_argument("key")
    pa_del.add_argument("fname")

    pa_put = sub.add_parser("put", help="upload a local file to the device")
    add_common(pa_put)
    pa_put.add_argument("bank", choices=["human","generated","GENERA~1"])
    pa_put.add_argument("key")
    pa_put.add_argument("fname", help="destination filename on device (e.g., 001.mp3)")
    pa_put.add_argument("path", help="local file path")
    pa_put.add_argument("--no-crc", action="store_true", help="disable CRC32 send/verify")

    pa_get = sub.add_parser("get", help="download a file from the device")
    add_common(pa_get)
    pa_get.add_argument("bank", choices=["human","generated","GENERA~1"])
    pa_get.add_argument("key")
    pa_get.add_argument("fname")
    pa_get.add_argument("out", help="local output path")

    pa_exit = sub.add_parser("exit", help="send EXIT to leave data mode")
    add_common(pa_exit)

    # ==== SEGMENT 2: data_cli argparse for sync ====
    pa_sync_seq = sub.add_parser("sync-seq", help="sync folder → 001.ext, 002.ext... if size differs/missing")
    add_common(pa_sync_seq)
    pa_sync_seq.add_argument("bank", choices=["human","generated","GENERA~1"])
    pa_sync_seq.add_argument("key")
    pa_sync_seq.add_argument("folder")
    pa_sync_seq.add_argument("--ext", default="mp3")
    pa_sync_seq.add_argument("--start", type=int, default=1)
    pa_sync_seq.add_argument("--dry-run", action="store_true")

    pa_sync_pre = sub.add_parser("sync-preserve", help="sync folder preserving filenames if size differs/missing")
    add_common(pa_sync_pre)
    pa_sync_pre.add_argument("bank", choices=["human","generated","GENERA~1"])
    pa_sync_pre.add_argument("key")
    pa_sync_pre.add_argument("folder")
    pa_sync_pre.add_argument("--ext", default="mp3")
    pa_sync_pre.add_argument("--dry-run", action="store_true")

    # ==== SEGMENT B2: argparse for flag ====
    pa_flag = sub.add_parser("flag", help="create/remove allow_writes.flag on device")
    add_common(pa_flag)
    pa_flag.add_argument("state", choices=["on","off"])

    args = ap.parse_args()

    if args.cmd == "ports":
        for p in list_ports.comports():
            print(f"{p.device}  -  {p.description}")
        return

    # open serial
    ser = open_serial(args.port, args.baud)
    try:
        if not args.no_handshake:
            try:
                handshake(ser)
            except TimeoutError:
                # maybe already in data mode but noisy; try once more
                drain_input(ser); time.sleep(0.1)
                handshake(ser)

        if args.cmd == "ls":
            items = cmd_ls(ser, args.bank, args.key)
            if not items:
                print("(empty)")
            else:
                width = max(len(n) for n,_ in items)
                for n, sz in items:
                    print(f"{n.ljust(width)}  {human_size(sz).rjust(8)}  ({sz})")

        elif args.cmd == "del":
            cmd_del(ser, args.bank, args.key, args.fname)

        elif args.cmd == "put":
            cmd_put(ser, args.bank, args.key, args.fname, args.path, use_crc=not args.no_crc)

        elif args.cmd == "get":
            cmd_get(ser, args.bank, args.key, args.fname, args.out)

        elif args.cmd == "exit":
            cmd_exit(ser)

        elif args.cmd == "sync-seq":
            cmd_sync_seq(ser, args.bank, args.key, args.folder, ext=args.ext, start=args.start, dry_run=args.dry_run)

        elif args.cmd == "sync-preserve":
            cmd_sync_preserve(ser, args.bank, args.key, args.folder, ext=args.ext, dry_run=args.dry_run)

        elif args.cmd == "flag":
            on = (args.state == "on")
            ok = cmd_flag(ser, on)
            print("[ok] flag set" if ok else "[?] unexpected flag response")

    finally:
        ser.close()

if __name__ == "__main__":
    main()
