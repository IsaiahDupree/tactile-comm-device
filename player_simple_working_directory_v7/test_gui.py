#!/usr/bin/env python3
# Simple test to verify GUI dependencies and launch

import sys

try:
    import PySimpleGUI as sg
    print("✅ PySimpleGUI imported successfully")
    print(f"   Version: {sg.version}")
except ImportError as e:
    print("❌ PySimpleGUI not found:", e)
    print("   Install with: pip install PySimpleGUI")
    sys.exit(1)

try:
    import serial
    from serial.tools import list_ports
    print("✅ pyserial imported successfully")
    ports = list(list_ports.comports())
    print(f"   Found {len(ports)} serial ports")
    for p in ports[:3]:  # Show first 3
        print(f"   - {p.device}: {p.description}")
except ImportError as e:
    print("❌ pyserial not found:", e)
    print("   Install with: pip install pyserial")
    sys.exit(1)

try:
    import data_cli
    print("✅ data_cli module imported successfully")
except ImportError as e:
    print("❌ data_cli import failed:", e)
    sys.exit(1)

print("\n🚀 All dependencies OK! Launching GUI...")

# Simple GUI test
sg.theme("SystemDefaultForReal")
layout = [
    [sg.Text("Tactile Data Tool - Dependency Test")],
    [sg.Text(f"PySimpleGUI: {sg.version}")],
    [sg.Text(f"Serial ports found: {len(ports)}")],
    [sg.Button("Launch Full GUI"), sg.Button("Exit")]
]

window = sg.Window("Test", layout)
while True:
    event, values = window.read()
    if event in (sg.WINDOW_CLOSED, "Exit"):
        break
    elif event == "Launch Full GUI":
        window.close()
        # Import and run the full GUI
        import data_gui
        break

window.close()
