#!/usr/bin/env python3
import serial
import time
from serial.tools import list_ports

print("=== Testing Data Mode Connection ===")

# List available ports
print("\nAvailable serial ports:")
for port in list_ports.comports():
    print(f"  {port.device} - {port.description}")

# Test connection to COM5
try:
    print(f"\nTrying to connect to COM5...")
    ser = serial.Serial('COM5', 115200, timeout=2)
    time.sleep(0.5)  # Let it settle
    
    # Clear any existing data
    ser.reset_input_buffer()
    
    print("Sending handshake: ^DATA? v1")
    ser.write(b"^DATA? v1\n")
    
    # Wait for response
    response = ser.readline().decode('utf-8', errors='ignore').strip()
    print(f"Device response: '{response}'")
    
    if "DATA:OK v1" in response:
        print("✅ Data mode handshake successful!")
        
        # Try listing files
        print("\nTesting LS command...")
        ser.write(b"LS human A\n")
        
        # Read responses until LS:DONE
        while True:
            line = ser.readline().decode('utf-8', errors='ignore').strip()
            print(f"  {line}")
            if "LS:DONE" in line or "LS:NODIR" in line:
                break
            if not line:  # timeout
                break
        
        # Exit data mode
        print("\nExiting data mode...")
        ser.write(b"EXIT\n")
        response = ser.readline().decode('utf-8', errors='ignore').strip()
        print(f"Exit response: '{response}'")
        
    else:
        print("❌ Handshake failed. Device may not be in normal mode or firmware not uploaded.")
        
    ser.close()
    
except serial.SerialException as e:
    print(f"❌ Serial connection failed: {e}")
except Exception as e:
    print(f"❌ Error: {e}")

print("\nTest complete.")
