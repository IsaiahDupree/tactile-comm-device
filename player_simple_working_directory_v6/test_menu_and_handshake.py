#!/usr/bin/env python3
"""
Test script to validate both menu commands and handshake work after serial fix.
"""

import serial
import time

def send(s, t): 
    s.write((t + "\n").encode("ascii"))

def readln(s, to=2.0):
    end = time.time() + to
    buf = bytearray()
    while time.time() < end:
        b = s.read(1)
        if not b: 
            continue
        if b == b'\n': 
            return buf.decode(errors="ignore").rstrip("\r")
        buf += b
    return None

def test_menu_and_handshake():
    print("Testing menu commands and handshake at 115200 baud...")
    
    ser = serial.Serial('COM5', 115200, timeout=2.0)
    time.sleep(2.5)  # allow boot after port open
    ser.reset_input_buffer()

    # 1) Menu should work now
    print("\n=== Testing Menu Command ===")
    send(ser, "H")  # show help/menu
    menu_response = readln(ser, 2.0)
    print("MENU:", menu_response)
    if menu_response:
        print("✅ Menu command working!")
    else:
        print("❌ Menu command failed")

    # 2) Handshake
    print("\n=== Testing Handshake ===")
    send(ser, "^DATA? v1")
    ok = False
    for i in range(10):
        ln = readln(ser, 1.5)
        if not ln: 
            continue
        print(">>", ln)
        if ln.startswith("DATA:OK"): 
            ok = True
            break
    
    print("Handshake OK?", ok)

    if ok:
        print("\n=== Testing Data Mode Commands ===")
        send(ser, "STATUS")
        status_response = readln(ser, 2.0)
        print("STATUS:", status_response)
        
        send(ser, "EXIT")
        exit_response = readln(ser, 2.0)
        print("EXIT:", exit_response)

    ser.close()
    
    if menu_response and ok:
        print("\n✅ SUCCESS: Both menu and handshake working!")
        return True
    else:
        print("\n❌ FAILED: One or both tests failed")
        return False

if __name__ == "__main__":
    test_menu_and_handshake()
