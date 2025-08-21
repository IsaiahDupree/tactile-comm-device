# tests/test_device_io.py
import os, time, binascii, tempfile, random
import serial
import pytest

HEADER_TIMEOUT = 10.0
STREAM_TIMEOUT = 30.0

def human(n):
    for u in "B KB MB GB TB".split():
        if n < 1024: return f"{n:.0f}{u}"
        n /= 1024
    return f"{n:.1f}PB"

def send_line(ser, s: str):
    ser.write((s + "\n").encode("ascii"))

def drain_input(ser):
    time.sleep(0.05)
    ser.reset_input_buffer()

def read_line(ser, timeout_s=5.0):
    end = time.time() + timeout_s
    buf = bytearray()
    while time.time() < end:
        b = ser.read(1)
        if not b:
            continue
        if b == b"\n":
            return buf.decode(errors="ignore").rstrip("\r")
        buf += b
    return None

def expect_line(ser, prefix: str, timeout_s=5.0):
    end = time.time() + timeout_s
    while time.time() < end:
        line = read_line(ser, timeout_s=timeout_s)
        if not line:
            continue
        if line.startswith(prefix):
            return line
        # ignore noise
    return None

def norm_bank(b: str) -> str:
    if b.lower().startswith("gen"): return "GENERA~1"
    if b.lower().startswith("hum"): return "HUMAN"
    return b

@pytest.fixture(scope="session")
def ser(port, baud):
    s = serial.Serial(port=port, baudrate=baud, timeout=0.2)
    drain_input(s)

    # enter data mode
    send_line(s, "^DATA? v1")
    ok = expect_line(s, "DATA:OK", timeout_s=3.0)
    # device may also print a status line; ignore anything else
    assert ok, "No DATA:OK v1 handshake"
    # device announces entry
    expect_line(s, "[DATA] mode=ENTER", timeout_s=1.0)  # optional; don't assert

    yield s

    # exit data mode
    try:
        drain_input(s)
        send_line(s, "EXIT")
        expect_line(s, "DATA:BYE", timeout_s=2.0)
        expect_line(s, "[DATA] mode=EXIT", timeout_s=1.0)
    finally:
        s.close()

def cmd_flag(ser, on: bool):
    drain_input(ser)
    send_line(ser, "FLAG ON" if on else "FLAG OFF")
    line = expect_line(ser, "FLAG:", timeout_s=5.0)
    assert line, "No response to FLAG"
    if on:  assert line.startswith("FLAG:ON"),  f"flag on failed: {line}"
    else:   assert line.startswith("FLAG:OFF"), f"flag off failed: {line}"

def cmd_status(ser):
    drain_input(ser); send_line(ser, "STATUS")
    line = expect_line(ser, "STATUS ", timeout_s=5.0)
    assert line, "No response to STATUS"
    return ("WRITES=ON" in line)

def cmd_stat(ser):
    drain_input(ser); send_line(ser, "STAT")
    line = expect_line(ser, "STAT ", timeout_s=5.0)
    assert line, "No response to STAT"
    _, tot, fre = line.split()
    return int(tot), int(fre)

def cmd_ls(ser, bank, key):
    bank = norm_bank(bank)
    drain_input(ser); send_line(ser, f"LS {bank} {key}")
    files = {}
    while True:
        line = read_line(ser, timeout_s=HEADER_TIMEOUT)
        assert line, "LS timed out"
        if line == "LS:DONE":
            break
        if line in ("LS:NODIR","ERR:ARGS"):
            return files
        # expect "LS:NAME SIZE" format
        if line.startswith("LS:"):
            try:
                parts = line[3:].split()
                if len(parts) >= 2:
                    name, sz = parts[0], parts[1]
                    files[name.upper()] = int(sz)
            except Exception:
                # ignore malformed lines
                pass
        # ignore other noise lines
    return files

def cmd_put(ser, bank, key, name, data: bytes):
    bank = norm_bank(bank)
    crc = binascii.crc32(data) & 0xFFFFFFFF
    drain_input(ser)
    send_line(ser, f"PUT {bank} {key} {name} {len(data)} {crc}")
    ready = expect_line(ser, "PUT:READY", timeout_s=5.0)
    assert ready, "No PUT:READY"
    # stream bytes
    sent = 0
    t_end = time.time() + STREAM_TIMEOUT
    while sent < len(data):
        if time.time() > t_end:
            pytest.fail("PUT stream timeout")
        n = ser.write(data[sent:sent+512])
        assert n > 0
        sent += n
    done = expect_line(ser, "PUT:DONE", timeout_s=10.0)
    assert done, "No PUT:DONE"

def cmd_get(ser, bank, key, name) -> bytes:
    bank = norm_bank(bank)
    drain_input(ser)
    send_line(ser, f"GET {bank} {key} {name}")
    hdr = expect_line(ser, "GET:SIZE", timeout_s=HEADER_TIMEOUT)
    assert hdr, "No GET:SIZE header"
    parts = hdr.split()
    size = int(parts[1])
    crc_dev = int(parts[2]) if len(parts) >= 3 else None

    out = bytearray()
    t_end = time.time() + STREAM_TIMEOUT
    while len(out) < size:
        if time.time() > t_end:
            pytest.fail("GET stream timeout")
        chunk = ser.read(size - len(out))
        if not chunk:
            continue
        out.extend(chunk)
    # optional crc check
    if crc_dev is not None:
        crc_host = binascii.crc32(out) & 0xFFFFFFFF
        assert crc_host == crc_dev, f"CRC mismatch: dev={crc_dev:x} host={crc_host:x}"
    return bytes(out)

def cmd_del(ser, bank, key, name):
    bank = norm_bank(bank)
    drain_input(ser)
    send_line(ser, f"DEL {bank} {key} {name}")
    line = expect_line(ser, "DEL:", timeout_s=5.0)
    assert line and line in ("DEL:OK", "DEL:NOK"), "No DEL response"
    return line == "DEL:OK"

# ---------- tests ----------

def test_stat_basic(ser):
    total, free = cmd_stat(ser)
    assert total > 1_000_000, "Total bytes unreasonably small"
    assert 0 <= free <= total, "Free out of range"

def test_flag_toggle(ser):
    # turn on writes
    cmd_flag(ser, True)
    assert cmd_status(ser) is True
    # turn off writes
    cmd_flag(ser, False)
    assert cmd_status(ser) is False
    # leave ON for next test that needs it
    cmd_flag(ser, True)

def test_put_ls_get_del_roundtrip(ser, bank, key, tmp_path):
    # ensure writes ON for this test
    if not cmd_status(ser):
        cmd_flag(ser, True)

    # make a random file with 8.3 compliant name
    name = "TST%03d.MP3" % random.randint(1, 999)
    payload = os.urandom(8192)  # 8 KB

    # PUT
    cmd_put(ser, bank, key, name, payload)

    # LS should show it
    files = cmd_ls(ser, bank, key)
    assert name in files or name.upper() in files, f"uploaded file {name} not found in LS: {list(files.keys())}"

    # GET and verify bytes
    data = cmd_get(ser, bank, key, name)
    assert data == payload, "downloaded bytes differ from uploaded"

    # DEL and ensure gone
    ok = cmd_del(ser, bank, key, name)
    assert ok, "DEL failed"
    files_after = cmd_ls(ser, bank, key)
    assert name not in files_after and name.upper() not in files_after, "file still listed after DEL"

    # optional: turn writes OFF to leave device safe
    cmd_flag(ser, False)

def test_8_3_filename_compliance(ser, bank, key):
    """Test that device properly handles 8.3 filenames"""
    if not cmd_status(ser):
        cmd_flag(ser, True)
    
    # Test various 8.3 compliant names
    test_files = [
        ("001.MP3", b"audio1"),
        ("TEST.WAV", b"audio2"), 
        ("A.TXT", b"text"),
        ("12345678.OGG", b"longname")  # exactly 8 chars
    ]
    
    for name, payload in test_files:
        # PUT
        cmd_put(ser, bank, key, name, payload)
        
        # Verify in LS
        files = cmd_ls(ser, bank, key)
        assert name in files or name.upper() in files, f"8.3 file {name} not found"
        
        # GET and verify
        data = cmd_get(ser, bank, key, name)
        assert data == payload, f"Data mismatch for {name}"
        
        # Clean up
        cmd_del(ser, bank, key, name)
    
    cmd_flag(ser, False)

def test_sd_space_tracking(ser, bank, key):
    """Test that STAT shows decreasing free space as files are added"""
    if not cmd_status(ser):
        cmd_flag(ser, True)
    
    # Get initial space
    total1, free1 = cmd_stat(ser)
    
    # Upload a reasonably sized file
    name = "SPACE.MP3"
    payload = os.urandom(16384)  # 16KB
    cmd_put(ser, bank, key, name, payload)
    
    # Check space decreased
    total2, free2 = cmd_stat(ser)
    assert total2 == total1, "Total space should not change"
    assert free2 < free1, "Free space should decrease after upload"
    
    # Clean up
    cmd_del(ser, bank, key, name)
    
    # Space should increase again (though may not be exact due to filesystem overhead)
    total3, free3 = cmd_stat(ser)
    assert free3 > free2, "Free space should increase after deletion"
    
    cmd_flag(ser, False)
