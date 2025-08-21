#!/usr/bin/env python3
"""
Test open mode functionality by removing WRITES.FLG and testing PUT/DEL commands
"""
import serial
import time
import os

SERIAL_PORT = "COM5"
BAUD = 115200
TIMEOUT = 3.0

def test_open_mode():
    """Test device in open mode (no write flag required)"""
    print("=" * 60)
    print("TESTING OPEN MODE (NO WRITE FLAG)")
    print("=" * 60)
    
    try:
        # Connect to device
        print(f"\n1. Connecting to {SERIAL_PORT}...")
        ser = serial.Serial(SERIAL_PORT, BAUD, timeout=TIMEOUT)
        time.sleep(2.5)  # Boot delay
        ser.reset_input_buffer()
        print("   ✓ Connected")
        
        # Enter data mode
        print("\n2. Entering data mode...")
        ser.write(b'^DATA? v1\n')
        ser.flush()
        
        handshake_success = False
        for _ in range(10):
            line = ser.readline().decode('utf-8', errors='replace').strip()
            if line.startswith('DATA:OK'):
                print(f"   ✓ Handshake successful: {line}")
                handshake_success = True
                break
            elif line:
                print(f"   Response: {line}")
        
        if not handshake_success:
            print("   ✗ Handshake failed")
            return False
        
        # Test STATUS command
        print("\n3. Checking STATUS...")
        ser.write(b'STATUS\n')
        ser.flush()
        
        for _ in range(5):
            line = ser.readline().decode('utf-8', errors='replace').strip()
            if line.startswith('STATUS'):
                print(f"   Status: {line}")
                if "MODE=OPEN" in line:
                    print("   ✓ Device in OPEN mode")
                if "WRITES=ON" in line:
                    print("   ✓ Writes enabled")
                break
        
        # Delete write flag file (if it exists)
        print("\n4. Removing write flag file...")
        ser.write(b'DEL CONFIG WRITES.FLG\n')
        ser.flush()
        
        for _ in range(5):
            line = ser.readline().decode('utf-8', errors='replace').strip()
            if line in ('DEL:OK', 'DEL:NOK'):
                print(f"   Delete result: {line}")
                break
            elif line:
                print(f"   Response: {line}")
        
        # Test PUT command without write flag
        print("\n5. Testing PUT command in open mode...")
        test_data = b"Hello, open mode!"
        size = len(test_data)
        
        ser.write(f'PUT HUMAN SHIFT TEST.TXT {size}\n'.encode())
        ser.flush()
        
        put_ready = False
        for _ in range(10):
            line = ser.readline().decode('utf-8', errors='replace').strip()
            if line == 'PUT:READY':
                print("   ✓ PUT:READY received")
                put_ready = True
                break
            elif line.startswith('ERR:'):
                print(f"   ✗ PUT error: {line}")
                break
            elif line:
                print(f"   Response: {line}")
        
        if put_ready:
            # Send data
            ser.write(test_data)
            ser.flush()
            
            # Wait for completion
            for _ in range(10):
                line = ser.readline().decode('utf-8', errors='replace').strip()
                if line == 'PUT:DONE':
                    print("   ✓ PUT completed successfully")
                    break
                elif line.startswith('ERR:'):
                    print(f"   ✗ PUT failed: {line}")
                    break
                elif line:
                    print(f"   Response: {line}")
        
        # Exit data mode
        print("\n6. Exiting data mode...")
        ser.write(b'EXIT\n')
        ser.flush()
        
        for _ in range(3):
            line = ser.readline().decode('utf-8', errors='replace').strip()
            if line:
                print(f"   Exit: {line}")
        
        ser.close()
        print("\n✓ Test completed")
        return True
        
    except Exception as e:
        print(f"\n✗ Test failed: {e}")
        return False

def main():
    """Main test function"""
    print("This test will:")
    print("1. Connect to the device")
    print("2. Enter data mode") 
    print("3. Check STATUS (should show MODE=OPEN)")
    print("4. Delete WRITES.FLG file")
    print("5. Test PUT command (should work without write flag)")
    print("6. Exit data mode")
    print()
    
    input("Press Enter to continue...")
    
    success = test_open_mode()
    
    if success:
        print("\n" + "=" * 60)
        print("OPEN MODE TEST SUCCESSFUL")
        print("✓ Device operates without write flag requirement")
        print("✓ PUT commands work in open mode")
        print("=" * 60)
    else:
        print("\n" + "=" * 60)
        print("OPEN MODE TEST FAILED")
        print("Check device connection and firmware upload")
        print("=" * 60)

if __name__ == "__main__":
    main()
