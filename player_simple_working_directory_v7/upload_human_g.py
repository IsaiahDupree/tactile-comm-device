#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Upload to /AUDIO/HUMAN/G with duplicate detection and playlist maintenance.
"""

import os, time, binascii, serial

# ===== USER CONFIG =====
SERIAL_PORT = "COM5"
BAUD = 115200
READ_TIMEOUT = 1.5       # longer timeout for drains
WRITE_CHUNK = 256
PAUSE_SEC = 0.004

TARGET_BANK = "HUMAN"    # /AUDIO/HUMAN
TARGET_KEY  = "G"        # /AUDIO/HUMAN/G
SOURCE_FILE = r"C:\Users\Cypress\Music\005.mp3"
PREFER_SAME_NUMBER = True
# =======================

def crc32_file(path: str) -> int:
    crc = 0
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            crc = binascii.crc32(chunk, crc)
    return crc & 0xFFFFFFFF

def open_serial(port: str, baud: int, timeout: float) -> serial.Serial:
    ser = serial.Serial(
        port,
        baudrate=baud,
        timeout=1.5,  # bump up a bit
        write_timeout=2.0,
        inter_byte_timeout=0.2  # important on Windows CDC to catch that last byte
    )
    time.sleep(0.1)
    ser.reset_input_buffer()
    ser.reset_output_buffer()
    return ser

def wline(ser, s): ser.write((s+"\n").encode("utf-8")); ser.flush()
def rline(ser): 
    raw = ser.readline()
    return raw.decode("utf-8", errors="replace").strip() if raw else ""

def handshake(ser):
    wline(ser, "^DATA? v1")
    t0 = time.time()
    while time.time() - t0 < 5:
        ln = rline(ser)
        if ln.startswith("DATA:OK"): return
    raise RuntimeError("Handshake failed (no DATA:OK)")

def status(ser):
    wline(ser, "STATUS")
    for _ in range(20):
        ln = rline(ser)
        if ln.startswith("STATUS"): return ln
    return "(no STATUS)"

def ls_dir(ser, bank, key):
    """Return [{'name':..., 'size':...}] or None if NODIR."""
    wline(ser, f"LS {bank} {key}")
    out = []
    while True:
        ln = rline(ser)
        if not ln: continue
        if ln == "LS:DONE": return out
        if ln == "LS:NODIR": return None
        if ln.startswith("LS:"):
            parts = ln[3:].strip().split()
            if len(parts) >= 2:
                out.append({"name": parts[0], "size": parts[1]})

def drain_bytes(ser, n):
    """
    Drain exactly n bytes with a dynamic deadline:
    - Base budget from serial speed (10 bits/byte @115200) + margin
    - Extend the deadline whenever progress is made
    """
    # at 115200, ~11,520 bytes/s payload (10 bits/byte)
    # budget: payload_time + 300ms margin (min 0.6s)
    per_byte = 10.0 / BAUD
    budget = max(n * per_byte + 0.3, 0.6)
    deadline = time.time() + budget

    remaining = n
    last_progress = time.time()

    while remaining > 0:
        chunk = ser.read(min(remaining, 4096))
        if chunk:
            remaining -= len(chunk)
            last_progress = time.time()
            # keep at least 200ms after last progress to catch trailing bytes
            deadline = max(deadline, last_progress + 0.2)
        else:
            now = time.time()
            if now > deadline:
                raise RuntimeError(f"GET stream timeout with {remaining} bytes remaining")

def get_header_and_drain(ser, bank, key, fname):
    """Return (size, crc or None)."""
    wline(ser, f"GET {bank} {key} {fname}")
    hdr = ""
    for _ in range(80):
        hdr = rline(ser)
        if hdr.startswith("GET:SIZE"): break
    if not hdr.startswith("GET:SIZE"):
        raise RuntimeError(f"GET header missing for {fname}: {hdr}")

    parts = hdr.split()
    size = int(parts[1])
    crc = int(parts[2]) if len(parts) >= 3 else None

    # temporarily relax timeout for raw phase
    prev = ser.timeout
    ser.timeout = max(prev, 1.5)
    try:
        drain_bytes(ser, size)
    finally:
        ser.timeout = prev

    return size, crc

def next_slot(existing_names):
    used = set()
    for n in existing_names:
        u = n.upper()
        if u.endswith(".MP3") and len(u) == 7 and u[:3].isdigit():
            used.add(int(u[:3]))
    for i in range(1, 1000):
        if i not in used: return f"{i:03d}"
    return "999"

def put_file_with_retry(ser, bank, key, fname, local_path):
    size = os.path.getsize(local_path)
    crc  = crc32_file(local_path)
    cmd  = f"PUT {bank} {key} {fname} {size} {crc}"
    for attempt in (1, 2):
        print(f"[PUT] attempt {attempt}: {cmd}")
        wline(ser, cmd)
        # Wait for PUT:READY
        for _ in range(120):  # ~> a few hundred ms
            ln = rline(ser)
            if ln.startswith("PUT:READY"):
                # Parse flow control window size
                parts = ln.split()
                flow = int(parts[1]) if len(parts) > 1 else 512   # default if old firmware
                # stream file with flow control
                stream_with_flow(ser, local_path, flow)
                # wait completion
                for _ in range(400):
                    ln = rline(ser)
                    if ln == "PUT:DONE": return "PUT:DONE"
                    if ln.startswith("ERR:"): return ln
                return "ERR:TIMEOUT"
            if ln.startswith("ERR:"):
                return ln
        # no PUT:READY -> hard resync then retry
        print("[PUT] no READY; hard-resyncing data mode…")
        hard_reset_datamode(ser)
    return "ERR:NOREADY"

def put_file(ser, bank, key, fname, local_path):
    size = os.path.getsize(local_path)
    crc  = crc32_file(local_path)
    wline(ser, f"PUT {bank} {key} {fname} {size} {crc}")
    # Wait PUT:READY
    ready = False
    flow = 512  # default
    for _ in range(80):
        ln = rline(ser)
        if ln.startswith("PUT:READY"):
            ready = True
            parts = ln.split()
            flow = int(parts[1]) if len(parts) > 1 else 512   # default if old firmware
            break
        if ln.startswith("ERR:"): return ln
    if not ready: return "ERR:NOREADY"
    # Stream with flow control
    stream_with_flow(ser, local_path, flow)
    # Completion
    for _ in range(200):
        ln = rline(ser)
        if ln == "PUT:DONE": return "PUT:DONE"
        if ln.startswith("ERR:"): return ln
    return "ERR:TIMEOUT"

def wait_for_ack(ser, timeout=3.0):
    """Wait for flow control ACK (>) from device"""
    t0 = time.time()
    while time.time() - t0 < timeout:
        b = ser.read(1)
        if b == b'>':
            return True
    raise RuntimeError("No ACK (>) from device")

def stream_with_flow(ser, path, flow_bytes):
    """Stream file with flow control"""
    sent_in_window = 0
    with open(path, "rb") as f:
        while True:
            need = min(256, flow_bytes - sent_in_window)  # 256-sized writes inside each window
            chunk = f.read(need)
            if not chunk:
                break
            ser.write(chunk)
            sent_in_window += len(chunk)
            if sent_in_window >= flow_bytes:
                ser.flush()
                wait_for_ack(ser)          # block until device grants next window
                sent_in_window = 0

def put_bytes(ser, bank, key, fname, data: bytes):
    size = len(data); crc = binascii.crc32(data) & 0xFFFFFFFF
    wline(ser, f"PUT {bank} {key} {fname} {size} {crc}")
    for _ in range(80):
        ln = rline(ser)
        if ln.startswith("PUT:READY"):
            # Parse flow control window size
            parts = ln.split()
            flow = int(parts[1]) if len(parts) > 1 else 512   # default if old firmware
            # stream with flow control
            sent_in_window = 0
            off = 0
            while off < size:
                need = min(256, flow - sent_in_window, size - off)
                ser.write(data[off:off+need])
                off += need
                sent_in_window += need
                if sent_in_window >= flow:
                    ser.flush()
                    wait_for_ack(ser)
                    sent_in_window = 0
            ser.flush()
            break
        if ln.startswith("ERR:"): return ln
    for _ in range(200):
        ln = rline(ser)
        if ln == "PUT:DONE": return "PUT:DONE"
        if ln.startswith("ERR:"): return ln
    return "ERR:TIMEOUT"

def resync_line_mode(ser):
    # Drain any stragglers quickly
    t0 = time.time()
    while time.time() - t0 < 0.5:
        if not ser.read(4096):
            break
    # Ask for STATUS to realign parser to line mode
    wline(ser, "STATUS")
    for _ in range(50):
        s = rline(ser)
        if s.startswith("STATUS"):
            return

def hard_reset_datamode(ser):
    # Drain anything pending
    t0 = time.time()
    while time.time() - t0 < 0.5:
        if not ser.read(4096):
            break
    # Leave data mode
    wline(ser, "EXIT")
    # Read a few lines (DATA:BYE / [DATA] mode=EXIT)
    t1 = time.time()
    while time.time() - t1 < 1.0:
        if not rline(ser):
            break
    # Re-enter
    handshake(ser)
    # Preflight: send an unknown command; expect ERR:UNKNOWN
    wline(ser, "NOOP")
    for _ in range(30):
        ln = rline(ser)
        if ln == "ERR:UNKNOWN":
            return

def build_m3u(filenames):
    lines = ["#EXTM3U"] + sorted((n.upper() for n in filenames if n.upper().endswith(".MP3")))
    return ("\r\n".join(lines) + "\r\n").encode("utf-8")

def main():
    assert os.path.exists(SOURCE_FILE), f"Source file missing: {SOURCE_FILE}"
    local_crc = crc32_file(SOURCE_FILE)
    print(f"[LOCAL] {SOURCE_FILE}  size={os.path.getsize(SOURCE_FILE)}  CRC32={local_crc:08X}")

    ser = open_serial(SERIAL_PORT, BAUD, READ_TIMEOUT)
    try:
        handshake(ser)
        print(status(ser))

        # 1) List existing files in /AUDIO/HUMAN/G
        listing = ls_dir(ser, TARGET_BANK, TARGET_KEY)
        if listing is None:
            print(f"[INFO] Directory {TARGET_BANK}/{TARGET_KEY} does not exist yet (will be created on PUT).")
            listing = []

        names   = [it["name"] for it in listing if it["name"].upper().endswith(".MP3")]
        print(f"[REMOTE] {len(names)} mp3(s) in {TARGET_BANK}/{TARGET_KEY}")

        # Duplicate check - TEMPORARILY DISABLED to avoid GET/PUT mixing
        print("[CHECK] Skipping duplicate check (avoiding GET/PUT serial issues)")
        # TODO: Re-enable after firmware Serial.flush() is confirmed working
        # for n in names:
        #     try:
        #         _, rcrc = get_header_and_drain(ser, TARGET_BANK, TARGET_KEY, n)
        #     except Exception as e:
        #         print(f"  - {n}: GET failed ({e}) — HARD resync")
        #         hard_reset_datamode(ser)
        #         continue
        #     if rcrc is not None and rcrc == local_crc:
        #         print(f"[SKIP] Duplicate (CRC match) with {n}")
        #         # still ensure playlist exists
        #         data = build_m3u(names)
        #         print("[PLAYLIST]", put_bytes(ser, TARGET_BANK, TARGET_KEY, "PLAYLIST.M3U", data))
        #         return

        # Choose name
        base = os.path.splitext(os.path.basename(SOURCE_FILE))[0]
        target_name = None
        if PREFER_SAME_NUMBER and base.isdigit() and len(base) == 3:
            candidate = f"{base}.MP3".upper()
            if candidate.upper() not in (x.upper() for x in names):
                target_name = candidate
        if not target_name:
            target_name = f"{next_slot(names)}.MP3"
        print(f"[NAME] {target_name}")

        # Preflight before PUT
        wline(ser, "STATUS")
        for _ in range(40):
            ln = rline(ser)
            if ln.startswith("STATUS"):
                break
        # throwaway bad command to be sure we're in line mode
        wline(ser, "NOOP")
        for _ in range(40):
            ln = rline(ser)
            if ln == "ERR:UNKNOWN":
                break

        # Upload
        resp = put_file_with_retry(ser, TARGET_BANK, TARGET_KEY, target_name, SOURCE_FILE)
        print(f"[PUT] {resp}")
        if resp != "PUT:DONE":
            raise RuntimeError(resp)

        # Rebuild playlist
        listing2 = ls_dir(ser, TARGET_BANK, TARGET_KEY) or []
        names2   = [it["name"] for it in listing2 if it["name"].upper().endswith(".MP3")]
        if target_name.upper() not in (x.upper() for x in names2):
            names2.append(target_name)
        data = build_m3u(names2)
        print("[PLAYLIST]", put_bytes(ser, TARGET_BANK, TARGET_KEY, "PLAYLIST.M3U", data))

        print(f"[DONE] Uploaded {target_name} to {TARGET_BANK}/{TARGET_KEY}")

    finally:
        try: wline(ser, "EXIT")
        except Exception: pass
        ser.close()

if __name__ == "__main__":
    main()
