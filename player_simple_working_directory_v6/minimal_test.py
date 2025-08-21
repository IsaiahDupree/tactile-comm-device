#!/usr/bin/env python3
import serial
import time
import sys

def minimal_test():
    print("Minimal device test starting...")
    
    try:
        # Open port with minimal timeout
        print("Opening COM5...")
        ser = serial.Serial('COM5', 115200, timeout=0.1, write_timeout=0.1)
        print("Port opened")
        
        # Minimal boot delay
        time.sleep(1)
        ser.reset_input_buffer()
        
        # Send handshake quickly
        print("Sending handshake...")
        ser.write(b'^DATA? v1\n')
        ser.flush()
        
        # Quick read
        time.sleep(0.1)
        response = ser.read(100)
        print(f"Got {len(response)} bytes: {response}")
        
        ser.close()
        print("Test complete")
        
    except Exception as e:
        print(f"Error: {type(e).__name__}: {e}")
        return False
    
    return True

if __name__ == "__main__":
    minimal_test()
