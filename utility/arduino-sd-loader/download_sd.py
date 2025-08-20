#!/usr/bin/env python3
import argparse
import os
import sys
import time
from pathlib import Path

import serial

BAUD_DEFAULT = 115200

class SDDownloader:
    def __init__(self, port: str, baud: int, out_root: Path):
        self.port = port
        self.baud = baud
        self.out_root = out_root
        self.ser = None

    def open(self):
        self.ser = serial.Serial(self.port, self.baud, timeout=4)
        time.sleep(0.3)
        self._drain()
        # Expect banner or OK
        self._send_line("PING")
        _ = self._readline()

    def close(self):
        if self.ser:
            self.ser.close()

    def _drain(self):
        time.sleep(0.05)
        while self.ser.in_waiting:
            self.ser.read(self.ser.in_waiting)
            time.sleep(0.02)

    def _readline(self) -> str:
        return self.ser.readline().decode(errors='ignore').strip()

    def _send_line(self, line: str):
        self.ser.write((line + "\n").encode())

    def list_dir(self, sd_path: str):
        self._send_line(f"LIST {sd_path}")
        first = self._readline()
        if not first.startswith("OK"):
            raise RuntimeError(f"LIST failed for {sd_path}: {first}")
        entries = []
        while True:
            line = self._readline()
            if line == "END":
                break
            if not line:
                continue
            # format: name,type,size
            parts = line.split(',')
            if len(parts) < 3:
                continue
            name, typ, size = parts[0], parts[1], int(parts[2])
            entries.append((name, typ, size))
        return entries

    def get_file(self, sd_path: str, out_path: Path):
        out_path.parent.mkdir(parents=True, exist_ok=True)
        self._send_line(f"GET {sd_path}")
        size_line = self._readline()
        try:
            total = int(size_line)
        except ValueError:
            raise RuntimeError(f"GET failed for {sd_path}: {size_line}")
        remain = total
        with open(out_path, 'wb') as f:
            while remain > 0:
                chunk = self.ser.read(min(256, remain))
                if not chunk:
                    raise RuntimeError(f"GET stream underrun for {sd_path}")
                f.write(chunk)
                remain -= len(chunk)
        # trailing OK/ERR
        fin = self._readline()
        if not fin.startswith("OK"):
            raise RuntimeError(f"GET finalize failed for {sd_path}: {fin}")

    def recurse(self, sd_path: str, local_root: Path):
        for name, typ, size in self.list_dir(sd_path):
            child_sd = (sd_path.rstrip('/') + '/' + name) if sd_path != '/' else ('/' + name)
            child_local = local_root / name
            if typ == 'D':
                child_local.mkdir(parents=True, exist_ok=True)
                self.recurse(child_sd, child_local)
            else:
                self.get_file(child_sd, child_local)


def main():
    parser = argparse.ArgumentParser(description='Download entire SD card tree via Arduino SD loader')
    parser.add_argument('--port', required=True, help='Serial port, e.g., COM3')
    parser.add_argument('--baud', type=int, default=BAUD_DEFAULT)
    parser.add_argument('--out', type=str, default=str(Path('Recordings') / 'SD_DUMPS'))
    args = parser.parse_args()

    ts = time.strftime('%Y%m%d-%H%M%S')
    out_root = Path(args.out).resolve() / f'SD_DUMP_{ts}'
    out_root.mkdir(parents=True, exist_ok=True)
    print(f'Output folder: {out_root}')

    dl = SDDownloader(args.port, args.baud, out_root)
    try:
        dl.open()
        # Start at root
        dl.recurse('/', out_root)
        print('Download complete')
    finally:
        dl.close()

if __name__ == '__main__':
    main()
