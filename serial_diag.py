#!/usr/bin/env python3
"""
Serial port diagnostic utility.

Features:
- Lists all serial ports (COMx) and metadata (description, VID/PID, location).
- Attempts a safe open/close on each port (no writes) to detect if it's locked/busy.
- Optional: target a specific port via --port COM3.
- Exit code 0 on success, 2 if any tested port is busy/unopenable, 3 if pyserial missing.

Usage:
  python serial_diag.py           # list and test all ports
  python serial_diag.py --port COM3
  python serial_diag.py --json    # machine-readable

If pyserial is not installed, you'll get a clear message and exit code 3.
Install with:
  pip install pyserial
"""
from __future__ import annotations
import argparse
import json
import sys
from typing import Any, Dict, List, Optional

try:
    from serial.tools import list_ports
    import serial  # type: ignore
except Exception as e:
    print("pyserial not available. Install with: pip install pyserial", file=sys.stderr)
    print(str(e), file=sys.stderr)
    sys.exit(3)


def port_dict(info: list_ports.ListPortInfo) -> Dict[str, Any]:
    hwid = getattr(info, 'hwid', '') or ''
    vid = getattr(info, 'vid', None)
    pid = getattr(info, 'pid', None)
    serial_number = getattr(info, 'serial_number', None)
    location = getattr(info, 'location', None)
    manufacturer = getattr(info, 'manufacturer', None)
    product = getattr(info, 'product', None)
    iface = getattr(info, 'interface', None)
    return {
        "device": info.device,
        "name": getattr(info, 'name', info.device),
        "description": getattr(info, 'description', ''),
        "hwid": hwid,
        "vid": vid,
        "pid": pid,
        "serial_number": serial_number,
        "location": location,
        "manufacturer": manufacturer,
        "product": product,
        "interface": iface,
    }


def try_open(port: str, baud: int = 9600, timeout: float = 0.5) -> Dict[str, Any]:
    result: Dict[str, Any] = {"port": port, "opened": False, "error": None}
    sp: Optional[serial.Serial] = None
    try:
        sp = serial.Serial(port=port, baudrate=baud, timeout=timeout)
        result["opened"] = True
    except Exception as e:
        result["error"] = str(e)
    finally:
        if sp and sp.is_open:
            try:
                sp.close()
            except Exception:
                pass
    return result


essential_fields = [
    "device", "description", "manufacturer", "product", "vid", "pid", "hwid"
]


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Serial port diagnostics")
    parser.add_argument("--port", help="Specific port to test, e.g., COM3")
    parser.add_argument("--json", action="store_true", help="Output JSON")
    args = parser.parse_args(argv)

    ports = list(list_ports.comports())

    if args.port:
        # If a specific port is requested, ensure it's present (but still allow test if not listed)
        target = args.port
        target_info = next((p for p in ports if p.device.lower() == target.lower()), None)
        tested = [try_open(target)]
        data = {
            "requested_port": target,
            "listed": port_dict(target_info) if target_info else None,
            "tested": tested,
        }
        if args.json:
            print(json.dumps(data, indent=2))
        else:
            print(f"Requested port: {target}")
            if target_info:
                info = port_dict(target_info)
                print("Detected in system port list:")
                for k in essential_fields:
                    print(f"  {k}: {info.get(k)}")
            else:
                print("Not detected in current port list (may be hidden or in-use).")
            tr = tested[0]
            if tr["opened"]:
                print(f"Open test: SUCCESS (opened and closed {target})")
            else:
                print(f"Open test: FAILED -> {tr['error']}")
        return 0 if tested[0]["opened"] else 2

    # No specific port: list all and test each
    results: List[Dict[str, Any]] = []
    for p in ports:
        info = port_dict(p)
        test = try_open(p.device)
        info["open_test"] = test
        results.append(info)

    if args.json:
        print(json.dumps({"ports": results}, indent=2))
    else:
        if not results:
            print("No serial ports found.")
        for info in results:
            print("-" * 60)
            print(f"Port: {info['device']}")
            print(f"Desc: {info.get('description')}")
            print(f"Mfr : {info.get('manufacturer')}  Prod: {info.get('product')}")
            print(f"VID:PID: {info.get('vid')}:{info.get('pid')}  HWID: {info.get('hwid')}")
            ot = info.get("open_test", {})
            if ot.get("opened"):
                print("Open test: SUCCESS (port is free)")
            else:
                print(f"Open test: FAILED -> {ot.get('error')}")
    # Exit code 2 if any tested port failed to open
    any_fail = any(not i.get("open_test", {}).get("opened") for i in results)
    return 2 if any_fail else 0


if __name__ == "__main__":
    sys.exit(main())
