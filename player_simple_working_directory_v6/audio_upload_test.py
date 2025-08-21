import argparse, io, struct, time, binascii, serial, os, sys

# ---------- Helpers ----------
def send_line(s, t): s.write((t+"\n").encode("ascii"))
def drain(s): time.sleep(0.05); s.reset_input_buffer()

def read_line(s, timeout=5.0):
    end=time.time()+timeout; buf=bytearray()
    while time.time()<end:
        b=s.read(1)
        if not b: continue
        if b==b"\n": return buf.decode(errors="ignore").rstrip("\r")
        buf+=b
    return None

def expect_prefix(s, prefix, timeout=5.0):
    end=time.time()+timeout
    while time.time()<end:
        ln=read_line(s, timeout)
        if not ln: continue
        if ln.startswith(prefix): return ln
        # ignore any other console noise
    return None

def norm_bank(b):
    b=b.strip().upper()
    if b.startswith("GEN"): return "GENERA~1"   # 8.3 alias for generated
    if b.startswith("HUM"): return "HUMAN"
    return b

# Minimal RIFF/WAV generator (PCM 16-bit mono)
def make_wav_bytes(freq=440, dur_s=1.0, sr=22050, amp=0.3):
    import math
    n = int(sr*dur_s)
    pcm = io.BytesIO()
    for i in range(n):
        sample = int(max(-1.0,min(1.0, amp*math.sin(2*math.pi*freq*i/sr))) * 32767)
        pcm.write(struct.pack("<h", sample))
    pcm_bytes = pcm.getvalue()
    data_sz = len(pcm_bytes)
    riff_sz = 36 + data_sz
    w = io.BytesIO()
    w.write(b"RIFF"); w.write(struct.pack("<I", riff_sz)); w.write(b"WAVE")
    w.write(b"fmt "); w.write(struct.pack("<I", 16))             # PCM chunk size
    w.write(struct.pack("<HHIIHH", 1, 1, sr, sr*2, 2, 16))       # PCM, mono, 16-bit
    w.write(b"data"); w.write(struct.pack("<I", data_sz)); w.write(pcm_bytes)
    return w.getvalue()

# ---------- Protocol commands ----------
def handshake(s):
    drain(s)
    s.write(b"^DATA? v1\n")       # send in one write to avoid interleaving with menu
    ok = expect_prefix(s, "DATA:OK", timeout=3.0)
    if not ok:
        raise RuntimeError("No DATA:OK v1 (baud/port/reset?)")
    # optional informational line:
    expect_prefix(s, "[DATA] mode=ENTER", timeout=1.0)

def cmd_flag(s, on):
    drain(s); send_line(s, "FLAG ON" if on else "FLAG OFF")
    ln = expect_prefix(s, "FLAG:", timeout=4.0)
    if on and ln!="FLAG:ON":  raise RuntimeError(f"FLAG ON failed: {ln}")
    if not on and ln!="FLAG:OFF": raise RuntimeError(f"FLAG OFF failed: {ln}")

def cmd_ls(s, bank, key):
    drain(s); send_line(s, f"LS {norm_bank(bank)} {key}")
    files={}
    while True:
        ln = read_line(s, timeout=5.0)
        if ln is None: raise RuntimeError("LS timeout")
        if ln=="LS:DONE": break
        if ln in ("LS:NODIR","ERR:ARGS"): break
        parts = ln.split()
        if len(parts)==2 and parts[1].isdigit():
            files[parts[0].upper()] = int(parts[1])
    return files

def cmd_put(s, bank, key, name, data: bytes):
    import math, binascii, time
    def expect_any(prefixes, timeout=5.0):
        end = time.time() + timeout
        while time.time() < end:
            ln = read_line(s, timeout=timeout)
            if not ln:
                continue
            for p in prefixes:
                if ln.startswith(p):
                    return ln
        return None

    crc = binascii.crc32(data) & 0xFFFFFFFF
    # 1) Clear any stale input, then send header
    drain(s)
    line = f"PUT {norm_bank(bank)} {key} {name} {len(data)} {crc}"
    send_line(s, line)
    s.flush()                           # <- make sure header is actually sent
    # 2) Wait for device to open path and reply. SD mkdir/open can be slow on first touch.
    #    Give it plenty of time (e.g., 15s) and surface device errors if any.
    ln = expect_any(["PUT:READY", "ERR:"], timeout=15.0)
    if not ln:
        raise RuntimeError("No PUT:READY (timed out). Tip: check FLAG ON, bank/key spelling, and case (8.3).")
    if ln != "PUT:READY":
        raise RuntimeError(f"Device error before PUT: {ln}")

    # 3) Stream payload in chunks
    sent = 0
    # Effective throughput @115200 is ~9–11 KB/s once overhead accounted.
    # Build a dynamic timeout: size/(9 KB/s) + margin
    kbps = 9_000.0
    stream_timeout = max(10.0, (len(data) / kbps) + 10.0)
    t_end = time.time() + stream_timeout
    while sent < len(data):
        if time.time() > t_end:
            raise RuntimeError(f"PUT stream timeout after {sent}/{len(data)} bytes")
        n = s.write(data[sent:sent+512])
        if n <= 0:
            raise RuntimeError("Serial write stalled")
        sent += n

    # 4) Wait for completion acknowledgement
    ln = expect_any(["PUT:DONE", "ERR:"], timeout=20.0)
    if not ln:
        raise RuntimeError("No PUT:DONE after payload (timed out)")
    if ln != "PUT:DONE":
        raise RuntimeError(f"Device error after PUT: {ln}")

def cmd_get(s, bank, key, name):
    drain(s); send_line(s, f"GET {norm_bank(bank)} {key} {name}")
    hdr = expect_prefix(s, "GET:SIZE", timeout=8.0)
    if not hdr: raise RuntimeError("No GET:SIZE header")
    parts = hdr.split()
    size = int(parts[1])
    crc_dev = int(parts[2]) if len(parts)>=3 else None
    out = bytearray()
    while len(out) < size:
        chunk = s.read(size - len(out))
        if not chunk: continue
        out.extend(chunk)
    if crc_dev is not None:
        crc_host = binascii.crc32(out) & 0xFFFFFFFF
        if crc_host != crc_dev:
            raise RuntimeError(f"CRC mismatch: dev={crc_dev:x} host={crc_host:x}")
    return bytes(out)

def cmd_del(s, bank, key, name):
    drain(s); send_line(s, f"DEL {norm_bank(bank)} {key} {name}")
    ln = expect_prefix(s, "DEL:", timeout=5.0)
    return ln == "DEL:OK"

# ---------- Main ----------
def main():
    ap = argparse.ArgumentParser(description="Audio data upload test (WAV PUT/GET/DEL)")
    ap.add_argument("--port", required=True, help="e.g. COM5 or /dev/ttyACM0")
    ap.add_argument("--baud", type=int, default=115200)
    ap.add_argument("--bank", default="HUMAN", help="HUMAN or GENERA~1 (generated)")
    ap.add_argument("--key",  default="A", help="Key folder (e.g. A, J, SHIFT)")
    ap.add_argument("--name", default="001.WAV", help="8.3 filename to upload")
    ap.add_argument("--freq", type=float, default=440.0)
    ap.add_argument("--dur",  type=float, default=1.0)
    ap.add_argument("--cleanup", action="store_true", help="Delete file after test")
    args = ap.parse_args()

    # Make a real WAV (VS1053-compatible)
    wav = make_wav_bytes(freq=args.freq, dur_s=args.dur, sr=22050, amp=0.4)

    print(f"[i] opening {args.port} @ {args.baud}")
    s = serial.Serial(args.port, args.baud, timeout=0.2, write_timeout=5.0)
    try:
        time.sleep(2.5)           # UNO R4 reset on open
        s.reset_input_buffer()

        print("[i] handshaking…")
        handshake(s)
        print("[ok] DATA_MODE")

        print("[i] enabling writes")
        cmd_flag(s, True)

        print(f"[i] PUT {args.bank}/{args.key}/{args.name} ({len(wav)} bytes)")
        cmd_put(s, args.bank, args.key, args.name, wav)

        files = cmd_ls(s, args.bank, args.key)
        if args.name.upper() not in files:
            print("[warn] file not listed by LS (case?)")
        else:
            print(f"[ok] LS shows {args.name} ({files[args.name.upper()]} bytes)")

        print(f"[i] GET {args.name} and verify")
        back = cmd_get(s, args.bank, args.key, args.name)
        assert back == wav, "downloaded bytes differ from uploaded"
        print("[ok] byte-for-byte match")

        if args.cleanup:
            print("[i] DEL file")
            ok = cmd_del(s, args.bank, args.key, args.name)
            print("[ok] DEL" if ok else "[warn] DEL:NOK")

        # Optional: lock writes again
        cmd_flag(s, False)

        send_line(s, "EXIT")
        expect_prefix(s, "DATA:BYE", timeout=3.0)
        print("[ok] exited DATA_MODE")

        print("\n✓ Audio upload test PASSED")
        print("Tip: press the physical key now to confirm playback in NORMAL mode.")
    finally:
        s.close()

if __name__ == "__main__":
    main()
