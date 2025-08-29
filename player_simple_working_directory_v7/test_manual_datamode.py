#!/usr/bin/env python3
"""
Test script for manual data mode entry.
Use this after pressing PERIOD button 4 times on the device.
"""

import serial
import time

def test_manual_datamode():
    """Test data mode commands assuming device is already in data mode"""
    try:
        print("Connecting to device (assuming manual data mode entry)...")
        ser = serial.Serial('COM5', 9600, timeout=2)
        time.sleep(1)
        
        # Clear any startup messages
        ser.reset_input_buffer()
        time.sleep(0.5)
        
        print("Testing STATUS command...")
        ser.write(b'STATUS\n')
        time.sleep(0.5)
        
        response = ser.read(200)
        if response:
            decoded = response.decode(errors='ignore')
            print(f"STATUS response: {decoded}")
        else:
            print("No STATUS response")
        
        print("\nTesting STAT command...")
        ser.write(b'STAT\n')
        time.sleep(0.5)
        
        response = ser.read(200)
        if response:
            decoded = response.decode(errors='ignore')
            print(f"STAT response: {decoded}")
        else:
            print("No STAT response")
        
        print("\nTesting LS command...")
        ser.write(b'LS GENERA~1\n')
        time.sleep(1)
        
        response = ser.read(500)
        if response:
            decoded = response.decode(errors='ignore')
            print(f"LS response: {decoded}")
        else:
            print("No LS response")
        
        ser.close()
        print("\nTest complete. If you see responses, data mode is working!")
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    print("Manual Data Mode Test")
    print("====================")
    print("1. Press PERIOD button 4 times on your device")
    print("2. Device should print 'DATA:OK v1'")
    print("3. Run this script to test data mode commands")
    print()
    
    input("Press Enter after entering data mode manually...")
    test_manual_datamode()
