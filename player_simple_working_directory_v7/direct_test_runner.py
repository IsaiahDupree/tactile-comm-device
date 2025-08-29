#!/usr/bin/env python3
"""
Direct test runner for tactile communication device data protocol
Bypasses pytest to avoid import issues and provide immediate feedback
"""
import os
import sys
import time
import serial
import binascii
import traceback
from pathlib import Path

# Configuration
SERIAL_PORT = "COM5"
BAUD = 115200
READ_TIMEOUT = 3.5
BANK = "HUMAN"
KEY = "SHIFT"
FILENAME = "999.MP3"
LOCAL_MP3 = "sample.mp3"

def create_sample_mp3():
    """Create test MP3 file"""
    data = b'ID3\x03\x00\x00\x00\x00\x00\x00' + b'\xff\xfb\x90\x00' * 100
    with open(LOCAL_MP3, 'wb') as f:
        f.write(data)
    return len(data)

def crc32_file(path: str) -> int:
    """Calculate CRC32 of file"""
    crc = 0
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            crc = binascii.crc32(chunk, crc)
    return crc & 0xFFFFFFFF

def open_serial_connection():
    """Open and initialize serial connection"""
    ser = serial.Serial(SERIAL_PORT, baudrate=BAUD, timeout=READ_TIMEOUT, write_timeout=READ_TIMEOUT)
    time.sleep(2.5)  # Boot delay for UNO R4
    ser.reset_input_buffer()
    ser.reset_output_buffer()
    return ser

def send_handshake(ser):
    """Send handshake and wait for response"""
    ser.write(b'^DATA? v1\n')
    ser.flush()
    
    # Look for DATA:OK response
    for _ in range(10):
        line = ser.readline().decode('utf-8', errors='replace').strip()
        if line.startswith('DATA:OK'):
            return True, line
        elif line:
            print(f"  Handshake response: {line}")
    return False, "No DATA:OK received"

def test_status_command(ser):
    """Test STATUS command"""
    ser.write(b'STATUS\n')
    ser.flush()
    
    for _ in range(5):
        line = ser.readline().decode('utf-8', errors='replace').strip()
        if line.startswith('STATUS'):
            return line
    return None

def test_put_command(ser, filepath):
    """Test PUT command with file upload"""
    size = os.path.getsize(filepath)
    crc = crc32_file(filepath)
    
    # Send PUT command
    cmd = f'PUT {BANK} {KEY} {FILENAME} {size} {crc}\n'
    ser.write(cmd.encode('utf-8'))
    ser.flush()
    
    # Wait for PUT:READY
    for _ in range(10):
        line = ser.readline().decode('utf-8', errors='replace').strip()
        if line == 'PUT:READY':
            break
        elif line:
            print(f"  PUT response: {line}")
    else:
        return "No PUT:READY received"
    
    # Stream file data
    with open(filepath, 'rb') as f:
        while True:
            chunk = f.read(512)
            if not chunk:
                break
            ser.write(chunk)
    ser.flush()
    
    # Wait for completion
    for _ in range(10):
        line = ser.readline().decode('utf-8', errors='replace').strip()
        if line in ('PUT:DONE', 'ERR:CRC', 'ERR:WRITE', 'ERR:RENAME'):
            return line
        elif line:
            print(f"  PUT completion: {line}")
    
    return "No PUT completion response"

def test_ls_command(ser):
    """Test LS command"""
    cmd = f'LS {BANK} {KEY}\n'
    ser.write(cmd.encode('utf-8'))
    ser.flush()
    
    files = []
    while True:
        line = ser.readline().decode('utf-8', errors='replace').strip()
        if line == 'LS:DONE':
            break
        elif line.startswith('LS:'):
            files.append(line[3:].strip())
        elif line in ('LS:NODIR', 'ERR:ARGS'):
            return line
        elif line:
            print(f"  LS response: {line}")
    
    return files

def run_comprehensive_test():
    """Run complete test suite"""
    print("=" * 60)
    print("TACTILE COMMUNICATION DEVICE - COMPREHENSIVE TEST")
    print("=" * 60)
    
    # Ensure test results directory
    os.makedirs('test_results', exist_ok=True)
    
    results = []
    test_start = time.time()
    
    try:
        # Create sample file
        print("\n1. Creating sample MP3 file...")
        size = create_sample_mp3()
        print(f"   ✓ Created {LOCAL_MP3} ({size} bytes)")
        results.append(f"SETUP_SUCCESS: Created sample file {size} bytes")
        
        # Open serial connection
        print(f"\n2. Opening serial connection to {SERIAL_PORT}...")
        ser = open_serial_connection()
        print(f"   ✓ Serial port opened at {BAUD} baud")
        results.append(f"SERIAL_SUCCESS: Port {SERIAL_PORT} opened")
        
        # Test handshake
        print("\n3. Testing handshake protocol...")
        success, response = send_handshake(ser)
        if success:
            print(f"   ✓ Handshake successful: {response}")
            results.append(f"HANDSHAKE_SUCCESS: {response}")
        else:
            print(f"   ✗ Handshake failed: {response}")
            results.append(f"HANDSHAKE_FAIL: {response}")
            ser.close()
            return results
        
        # Test STATUS command
        print("\n4. Testing STATUS command...")
        status = test_status_command(ser)
        if status:
            print(f"   ✓ STATUS response: {status}")
            if "WRITES=ON" in status and "MODE=OPEN" in status:
                print("   ✓ Device in OPEN mode with writes enabled")
                results.append(f"STATUS_SUCCESS: {status}")
            else:
                print(f"   ⚠ Unexpected status: {status}")
                results.append(f"STATUS_UNEXPECTED: {status}")
        else:
            print("   ✗ No STATUS response")
            results.append("STATUS_FAIL: No response")
        
        # Test PUT command
        print(f"\n5. Testing PUT command with {LOCAL_MP3}...")
        put_result = test_put_command(ser, LOCAL_MP3)
        print(f"   PUT result: {put_result}")
        if put_result == "PUT:DONE":
            print("   ✓ File upload successful")
            results.append("PUT_SUCCESS: File uploaded")
        else:
            print(f"   ✗ File upload failed: {put_result}")
            results.append(f"PUT_FAIL: {put_result}")
        
        # Test LS command
        print(f"\n6. Testing LS command for {BANK}/{KEY}...")
        ls_result = test_ls_command(ser)
        if isinstance(ls_result, list):
            print(f"   ✓ Directory listing: {len(ls_result)} files")
            for file_info in ls_result:
                print(f"     - {file_info}")
            
            # Check if our file is listed
            file_found = any(FILENAME in file_info for file_info in ls_result)
            if file_found:
                print(f"   ✓ Uploaded file {FILENAME} found in listing")
                results.append(f"LS_SUCCESS: File found in {len(ls_result)} files")
            else:
                print(f"   ⚠ Uploaded file {FILENAME} not found in listing")
                results.append(f"LS_PARTIAL: File not found in {len(ls_result)} files")
        else:
            print(f"   ✗ Directory listing failed: {ls_result}")
            results.append(f"LS_FAIL: {ls_result}")
        
        # Exit data mode
        print("\n7. Exiting data mode...")
        ser.write(b'EXIT\n')
        ser.flush()
        time.sleep(0.5)
        exit_response = ser.readline().decode('utf-8', errors='replace').strip()
        if exit_response:
            print(f"   Exit response: {exit_response}")
        
        ser.close()
        print("   ✓ Serial connection closed")
        
    except serial.SerialException as e:
        print(f"   ✗ Serial error: {e}")
        results.append(f"SERIAL_ERROR: {e}")
    except Exception as e:
        print(f"   ✗ Test error: {e}")
        results.append(f"TEST_ERROR: {e}")
        traceback.print_exc()
    
    # Write detailed results
    test_duration = time.time() - test_start
    
    with open('test_results/comprehensive_test_results.txt', 'w') as f:
        f.write("COMPREHENSIVE TEST RESULTS\n")
        f.write("=" * 50 + "\n")
        f.write(f"Test Date: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Duration: {test_duration:.2f} seconds\n")
        f.write(f"Serial Port: {SERIAL_PORT}\n")
        f.write(f"Baud Rate: {BAUD}\n\n")
        
        f.write("RESULTS:\n")
        for result in results:
            f.write(f"  {result}\n")
    
    print(f"\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    success_count = sum(1 for r in results if "SUCCESS" in r)
    fail_count = sum(1 for r in results if "FAIL" in r or "ERROR" in r)
    
    for result in results:
        status = "✓" if "SUCCESS" in result else "✗" if ("FAIL" in result or "ERROR" in result) else "⚠"
        print(f"  {status} {result}")
    
    print(f"\nResults: {success_count} passed, {fail_count} failed")
    print(f"Duration: {test_duration:.2f} seconds")
    print(f"Details: test_results/comprehensive_test_results.txt")
    
    return results

if __name__ == "__main__":
    run_comprehensive_test()
