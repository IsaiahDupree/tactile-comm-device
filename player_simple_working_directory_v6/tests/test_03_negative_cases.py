# tests/test_03_negative_cases.py
import os
import io
import tempfile
import pytest
from .config import SERIAL_PORT, BAUD, READ_TIMEOUT, BANK, KEY
from .proto_utils import open_serial, enter_data_mode, read_line, write_line
from .data_ops import cmd_put

def test_put_bad_crc(tmp_path):
    # Create a temp payload
    p = tmp_path / "badcrc.bin"
    p.write_bytes(b"\x00\x01\x02\x03" * 1000)

    ser = open_serial(SERIAL_PORT, BAUD, READ_TIMEOUT)
    try:
        enter_data_mode(ser)
        # Force a wrong CRC by telling helper not to include CRC, then manually appending wrong length header.
        # Easier: call cmd_put with use_crc=True but mutate file after CRC is computed? Simpler: custom PUT:
        size = p.stat().st_size
        write_line(ser, f"PUT {BANK} {KEY} BADCRC.MP3 {size} 12345678")  # bogus crc
        # Expect PUT:READY
        got = ""
        for _ in range(10):
            s = read_line(ser)
            if s == "PUT:READY":
                got = s
                break
        assert got == "PUT:READY", "Did not receive PUT:READY for bad CRC test"

        with open(p, "rb") as f:
            ser.write(f.read())
        ser.flush()

        # Expect ERR:CRC
        seen = []
        for _ in range(10):
            s = read_line(ser)
            if s:
                seen.append(s)
                if s == "ERR:CRC":
                    return
        raise AssertionError(f"Expected ERR:CRC, saw: {seen}")
    finally:
        ser.close()

def test_ls_unknown_key_returns_nodir():
    ser = open_serial(SERIAL_PORT, BAUD, READ_TIMEOUT)
    try:
        enter_data_mode(ser)
        write_line(ser, "LS HUMAN __NOPE__")
        # Expect LS:NODIR then maybe chatter then LS:DONE won't appear
        saw_nodir = False
        for _ in range(5):
            s = read_line(ser)
            if s == "LS:NODIR":
                saw_nodir = True
                break
        assert saw_nodir, "Expected LS:NODIR for unknown key"
    finally:
        ser.close()
