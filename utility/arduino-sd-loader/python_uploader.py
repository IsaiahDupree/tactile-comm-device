#!/usr/bin/env python3
import argparse
import os
import sys
import time
from pathlib import Path

import serial

BAUD_DEFAULT = 115200

class SDUploader:
    def __init__(self, port: str, baud: int, root: Path, dry_run: bool = False):
        self.port = port
        self.baud = baud
        self.root = root
        self.dry_run = dry_run
        self.ser = None

    def open(self):
        if self.dry_run:
            print(f"[DRY RUN] Would open {self.port} @ {self.baud}")
            return
        self.ser = serial.Serial(self.port, self.baud, timeout=3)
        # Read initial banner if any
        time.sleep(0.3)
        self._drain()
        # Ping
        resp = self._send_line("PING")
        if not resp.startswith("OK"):
            print(f"Error: No OK from device on PING, got: {resp}")
            sys.exit(1)

    def close(self):
        if self.ser:
            self.ser.close()

    def _drain(self):
        if not self.ser:
            return
        time.sleep(0.05)
        while self.ser.in_waiting:
            _ = self.ser.read(self.ser.in_waiting)
            time.sleep(0.02)

    def _readline(self) -> str:
        if self.dry_run:
            return "OK"
        line = self.ser.readline().decode(errors='ignore').strip()
        return line

    def _send_line(self, line: str) -> str:
        if self.dry_run:
            print(f"[DRY RUN] -> {line}")
            return "OK"
        self.ser.write((line + "\n").encode())
        return self._readline()

    def _ensure_dirs(self, sd_path: str):
        # Create intermediate directories on SD
        parts = [p for p in sd_path.split('/') if p]
        if not parts:
            return
        cur = ""
        for part in parts[:-1]:  # exclude filename
            cur += "/" + part
            resp = self._send_line(f"EXISTS {cur}")
            if not resp.startswith("OK"):
                mk = self._send_line(f"MKDIR {cur}")
                if not mk.startswith("OK"):
                    raise RuntimeError(f"MKDIR failed for {cur}: {mk}")

    def put_file(self, rel_file: Path):
        # Convert to SD path (forward slashes, root-based)
        sd_path = "/" + str(rel_file).replace('\\\\', '/').replace('\\', '/')
        # Ensure directories
        self._ensure_dirs(sd_path)
        # Send PUT with size
        size = (self.root / rel_file).stat().st_size
        print(f"PUT {sd_path} ({size} bytes)")
        if self.dry_run:
            return
        resp = self._send_line(f"PUT {sd_path} {size}")
        if not resp.startswith("OK") and not resp.startswith("ERR SIZE"):
            # Device expects raw bytes right after command, no response yet. So if not OK, proceed to stream.
            pass
        # Stream file bytes
        with open(self.root / rel_file, 'rb') as f:
            while True:
                chunk = f.read(64)
                if not chunk:
                    break
                self.ser.write(chunk)
        # Read final OK/ERR
        fin = self._readline()
        if not fin.startswith("OK"):
            raise RuntimeError(f"PUT failed for {sd_path}: {fin}")

    def sync(self):
        if not self.root.exists():
            raise FileNotFoundError(f"Root not found: {self.root}")
        # Walk and send files
        all_files = []
        for p in self.root.rglob('*'):
            if p.is_file():
                rel = p.relative_to(self.root)
                all_files.append(rel)
        # Sort for deterministic order
        all_files.sort()
        for rel in all_files:
            self.put_file(rel)


def main():
    parser = argparse.ArgumentParser(description="Upload SD_FUTURE_PROOF tree to Arduino SD over serial")
    parser.add_argument('--port', required=True, help='Serial port (e.g., COM3 or /dev/ttyUSB0)')
    parser.add_argument('--baud', type=int, default=BAUD_DEFAULT, help='Baud rate (default: 115200)')
    parser.add_argument('--root', type=str, default=str(Path(__file__).resolve().parents[2] / 'tactile-comm-device' / 'sd' / 'SD_FUTURE_PROOF'),
                        help='Root folder to upload (default: sd/SD_FUTURE_PROOF)')
    parser.add_argument('--dry-run', action='store_true', help='Print actions without sending')
    args = parser.parse_args()

    root = Path(args.root).resolve()
    print(f"Using root: {root}")

    up = SDUploader(args.port, args.baud, root, dry_run=args.dry_run)
    try:
        up.open()
        up.sync()
        print("Upload complete")
    finally:
        up.close()

if __name__ == '__main__':
    main()
