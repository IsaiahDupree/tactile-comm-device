# tests/data_ops.py
import os
import time
import binascii
from .proto_utils import read_line, write_line, expect_prefix, crc32_file

def cmd_status(ser):
    write_line(ser, "STATUS")
    line = expect_prefix(ser, "STATUS ")
    return line

def cmd_ls(ser, bank: str, key: str) -> list[str]:
    write_line(ser, f"LS {bank} {key}")
    files = []
    while True:
        line = read_line(ser)
        if line == "LS:DONE":
            break
        if line.startswith("LS:"):
            # format: LS:<name> <size>
            files.append(line[3:].strip())
        elif line in ("LS:NODIR", "ERR:ARGS"):
            raise AssertionError(f"LS failed: {line}")
        # allow chatter (logs) to pass
    return files

def cmd_del(ser, bank: str, key: str, fname: str):
    write_line(ser, f"DEL {bank} {key} {fname}")
    line = read_line(ser)
    if line not in ("DEL:OK", "DEL:NOK"):
        raise AssertionError(f"Unexpected DEL response: {line}")
    return line

def cmd_put(ser, bank: str, key: str, fname: str, local_path: str, use_crc=True):
    size = os.path.getsize(local_path)
    crc = crc32_file(local_path) if use_crc else 0
    if use_crc:
        write_line(ser, f"PUT {bank} {key} {fname} {size} {crc}")
    else:
        write_line(ser, f"PUT {bank} {key} {fname} {size}")
    # Expect PUT:READY
    line = expect_prefix(ser, "PUT:READY", tries=10)

    # Stream file bytes raw (no framing)
    with open(local_path, "rb") as f:
        while True:
            chunk = f.read(512)
            if not chunk:
                break
            ser.write(chunk)
    ser.flush()

    # Expect PUT:DONE (or ERR:CRC / ERR:WRITE / ERR:RENAME etc.)
    line = ""
    # allow a couple of lines of chatter
    for _ in range(10):
        line = read_line(ser)
        if line:
            if line in ("PUT:DONE", "ERR:CRC", "ERR:WRITE", "ERR:RENAME", "ERR:OPEN", "ERR:MKDIR"):
                return line
    raise AssertionError("No PUT completion response received")

def cmd_get(ser, bank: str, key: str, fname: str, out_path: str) -> tuple[int, int]:
    """
    Returns (bytes_written, crc_from_header). Verifies exact byte count based on GET:SIZE header.
    """
    import re
    write_line(ser, f"GET {bank} {key} {fname}")
    # Expect "GET:SIZE <size> <crc32>" (crc optional depending on firmware build)
    hdr = expect_prefix(ser, "GET:SIZE")
    parts = hdr.split()
    if len(parts) == 3:
        expected_size = int(parts[1])
        expected_crc = int(parts[2])
    else:
        expected_size = int(parts[1])
        expected_crc = None

    remaining = expected_size
    written = 0
    with open(out_path, "wb") as out:
        while remaining > 0:
            # Use in_waiting to avoid blocking forever
            buf = ser.read(min(remaining, 1024))
            if not buf:
                # short read → device stopped early
                break
            out.write(buf)
            written += len(buf)
            remaining -= len(buf)

    if written != expected_size:
        raise AssertionError(f"GET short read: got {written}, expected {expected_size}")

    return written, (expected_crc if expected_crc is not None else -1)
