# tests/test_02_put_get_ls_del.py
import os
import tempfile
import pytest
from .config import SERIAL_PORT, BAUD, READ_TIMEOUT, BANK, KEY, FILENAME, LOCAL_MP3
from .proto_utils import open_serial, enter_data_mode
from .data_ops import cmd_put, cmd_get, cmd_ls, cmd_del, cmd_status, crc32_file

@pytest.mark.skipif(not os.path.exists(LOCAL_MP3), reason="LOCAL_MP3 not found")
def test_put_get_ls_del_roundtrip(tmp_path):
    ser = open_serial(SERIAL_PORT, BAUD, READ_TIMEOUT)
    try:
        enter_data_mode(ser)

        # 1) STATUS sanity
        status = cmd_status(ser)
        assert "WRITES=ON" in status

        # 2) PUT (with CRC)
        put_resp = cmd_put(ser, BANK, KEY, FILENAME, LOCAL_MP3, use_crc=True)
        assert put_resp == "PUT:DONE"

        # 3) LS contains file
        listing = cmd_ls(ser, BANK, KEY)
        names = [row.split()[0] for row in listing]  # "name size"
        assert FILENAME in names

        # 4) GET and verify size & crc
        out_file = tmp_path / ("got_" + FILENAME)
        got_bytes, remote_crc = cmd_get(ser, BANK, KEY, FILENAME, str(out_file))
        assert got_bytes == os.path.getsize(LOCAL_MP3)

        local_crc = crc32_file(str(out_file))
        if remote_crc != -1:
            assert local_crc == remote_crc

        # 5) DEL
        del_resp = cmd_del(ser, BANK, KEY, FILENAME)
        assert del_resp in ("DEL:OK", "DEL:NOK")  # OK expected; NOK if already gone
        # sanity: it should no longer be in LS
        listing2 = cmd_ls(ser, BANK, KEY)
        names2 = [row.split()[0] for row in listing2]
        assert FILENAME not in names2
    finally:
        ser.close()
