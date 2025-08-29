#!/usr/bin/env python3
"""
Upload real MP3 file to HUMAN directory on tactile device
"""
import serial
import time
import os
import binascii

# Configuration
SERIAL_PORT = "COM5"
BAUD = 115200
TIMEOUT = 5.0
SOURCE_FILE = r"C:\Users\Cypress\Music\005.mp3"
TARGET_BANK = "HUMAN"
TARGET_KEY = "SHIFT"  # or another key if SHIFT directory doesn't exist
TARGET_FILENAME = "005.MP3"

def crc32_file(filepath):
    """Calculate CRC32 of file"""
    crc = 0
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            crc = binascii.crc32(chunk, crc)
    return crc & 0xFFFFFFFF

def upload_mp3_file():
    """Upload the real MP3 file to device"""
    print("=" * 60)
    print("UPLOADING REAL MP3 FILE TO TACTILE DEVICE")
    print("=" * 60)
    
    # Check source file exists
    if not os.path.exists(SOURCE_FILE):
        print(f"✗ Source file not found: {SOURCE_FILE}")
        return False
    
    file_size = os.path.getsize(SOURCE_FILE)
    file_crc = crc32_file(SOURCE_FILE)
    
    print(f"Source file: {SOURCE_FILE}")
    print(f"File size: {file_size:,} bytes")
    print(f"File CRC32: {file_crc:08X}")
    print(f"Target: /{TARGET_BANK}/{TARGET_KEY}/{TARGET_FILENAME}")
    print()
    
    try:
        # Connect to device
        print("1. Connecting to device...")
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
        
        # Check available directories first
        print(f"\n3. Checking {TARGET_BANK} directory structure...")
        ser.write(f'LS {TARGET_BANK}\n'.encode())
        ser.flush()
        
        available_keys = []
        for _ in range(20):
            line = ser.readline().decode('utf-8', errors='replace').strip()
            if line == 'LS:DONE':
                break
            elif line.startswith('LS:'):
                key_info = line[3:].strip()
                key_name = key_info.split()[0]
                available_keys.append(key_name)
                print(f"   Found key: {key_name}")
            elif line == 'LS:NODIR':
                print(f"   No {TARGET_BANK} directory found")
                break
            elif line:
                print(f"   Response: {line}")
        
        # Use first available key if TARGET_KEY doesn't exist
        if available_keys:
            if TARGET_KEY not in available_keys:
                TARGET_KEY = available_keys[0]
                print(f"   Using available key: {TARGET_KEY}")
        else:
            print(f"   No keys found in {TARGET_BANK}, will try {TARGET_KEY}")
        
        # Attempt PUT command
        print(f"\n4. Uploading file to {TARGET_BANK}/{TARGET_KEY}...")
        put_cmd = f'PUT {TARGET_BANK} {TARGET_KEY} {TARGET_FILENAME} {file_size} {file_crc}\n'
        print(f"   Command: {put_cmd.strip()}")
        
        ser.write(put_cmd.encode())
        ser.flush()
        
        put_ready = False
        for _ in range(15):
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
        
        if not put_ready:
            print("   ✗ PUT command failed")
            return False
        
        # Upload file data
        print("   Uploading file data...")
        bytes_sent = 0
        chunk_size = 512
        
        with open(SOURCE_FILE, 'rb') as f:
            while True:
                chunk = f.read(chunk_size)
                if not chunk:
                    break
                
                ser.write(chunk)
                bytes_sent += len(chunk)
                
                # Progress indicator
                progress = (bytes_sent / file_size) * 100
                print(f"   Progress: {bytes_sent:,}/{file_size:,} bytes ({progress:.1f}%)", end='\r')
        
        ser.flush()
        print(f"\n   ✓ Sent {bytes_sent:,} bytes")
        
        # Wait for completion
        print("   Waiting for upload completion...")
        for _ in range(20):
            line = ser.readline().decode('utf-8', errors='replace').strip()
            if line == 'PUT:DONE':
                print("   ✓ Upload completed successfully!")
                break
            elif line.startswith('ERR:'):
                print(f"   ✗ Upload failed: {line}")
                break
            elif line:
                print(f"   Response: {line}")
        
        # Verify file was uploaded
        print(f"\n5. Verifying upload...")
        ser.write(f'LS {TARGET_BANK} {TARGET_KEY}\n'.encode())
        ser.flush()
        
        file_found = False
        for _ in range(10):
            line = ser.readline().decode('utf-8', errors='replace').strip()
            if line == 'LS:DONE':
                break
            elif line.startswith('LS:'):
                file_info = line[3:].strip()
                if TARGET_FILENAME in file_info:
                    print(f"   ✓ File found: {file_info}")
                    file_found = True
                else:
                    print(f"   File: {file_info}")
            elif line:
                print(f"   Response: {line}")
        
        if not file_found:
            print(f"   ⚠ File {TARGET_FILENAME} not found in directory listing")
        
        # Exit data mode
        print("\n6. Exiting data mode...")
        ser.write(b'EXIT\n')
        ser.flush()
        
        for _ in range(5):
            line = ser.readline().decode('utf-8', errors='replace').strip()
            if line:
                print(f"   {line}")
        
        ser.close()
        print("\n✓ Upload process completed")
        return True
        
    except Exception as e:
        print(f"\n✗ Upload failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("This will upload your MP3 file to the tactile device.")
    print(f"Source: {SOURCE_FILE}")
    print(f"Target: /{TARGET_BANK}/{TARGET_KEY}/{TARGET_FILENAME}")
    print()
    
    if input("Continue? (y/N): ").lower().startswith('y'):
        success = upload_mp3_file()
        
        if success:
            print("\n" + "=" * 60)
            print("🎉 MP3 UPLOAD SUCCESSFUL!")
            print("Your audio file is now on the tactile device")
            print("=" * 60)
        else:
            print("\n" + "=" * 60)
            print("❌ UPLOAD FAILED")
            print("Check the error messages above")
            print("=" * 60)
    else:
        print("Upload cancelled.")
