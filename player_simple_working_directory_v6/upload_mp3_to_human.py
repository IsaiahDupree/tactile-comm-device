#!/usr/bin/env python3
"""
Upload MP3 file to HUMAN directory on tactile device
Checks existing directories and uploads to available location
"""
import serial
import time
import os
import binascii

# Configuration
SERIAL_PORT = "COM5"
BAUD = 115200
TIMEOUT = 3
WRITE_CHUNK = 256
PAUSE_SEC = 0.004
SOURCE_FILE = r"C:\Users\Cypress\Music\005.mp3"
TARGET_BANK = "HUMAN"
TARGET_FILENAME = "005.MP3"

def crc32_file(filepath):
    """Calculate CRC32 of file"""
    crc = 0
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            crc = binascii.crc32(chunk, crc)
    return crc & 0xFFFFFFFF

def upload_mp3_to_human():
    """Upload MP3 file to HUMAN directory"""
    print("=" * 60)
    print("UPLOADING MP3 TO HUMAN DIRECTORY")
    print("=" * 60)
    
    # Check source file
    if not os.path.exists(SOURCE_FILE):
        print(f"✗ Source file not found: {SOURCE_FILE}")
        return False
    
    file_size = os.path.getsize(SOURCE_FILE)
    file_crc = crc32_file(SOURCE_FILE)
    
    print(f"Source: {SOURCE_FILE}")
    print(f"Size: {file_size:,} bytes ({file_size/1024/1024:.1f} MB)")
    print(f"CRC32: {file_crc:08X}")
    print(f"Target: /{TARGET_BANK}/[KEY]/{TARGET_FILENAME}")
    print()
    
    try:
        # Connect using reliable handshake protocol
        print("1. Connecting to device...")
        ser = serial.Serial(SERIAL_PORT, BAUD, timeout=TIMEOUT)
        time.sleep(2.5)  # Boot delay for UNO R4
        ser.reset_input_buffer()
        print("   ✓ Serial port opened")
        
        # Handshake - single write operation
        print("\n2. Entering data mode...")
        ser.write(b'^DATA? v1\n')
        ser.flush()
        time.sleep(1)
        
        response = ser.read_all().decode('utf-8', errors='replace')
        print(f"   Response: {repr(response)}")
        
        if 'DATA:OK' not in response:
            print("   ✗ Handshake failed")
            return False
        
        print("   ✓ Data mode active")
        
        # Check available directories in HUMAN bank
        print(f"\n3. Checking {TARGET_BANK} directories...")
        ser.write(f'LS {TARGET_BANK}\n'.encode())
        ser.flush()
        time.sleep(1)
        
        ls_response = ser.read_all().decode('utf-8', errors='replace')
        print(f"   LS response: {repr(ls_response)}")
        
        # Parse directory listing
        available_keys = []
        lines = ls_response.split('\n')
        for line in lines:
            line = line.strip()
            if line.startswith('LS:'):
                key_info = line[3:].strip()
                if key_info:
                    key_name = key_info.split()[0]
                    available_keys.append(key_name)
                    print(f"   Found key: {key_name}")
        
        if not available_keys:
            print("   No directories found in HUMAN bank")
            print("   Will try creating SHIFT directory...")
            target_key = "SHIFT"
        else:
            target_key = available_keys[0]
            print(f"   Using existing key: {target_key}")
        
        # Attempt PUT command
        print(f"\n4. Uploading to {TARGET_BANK}/{target_key}...")
        put_cmd = f'PUT {TARGET_BANK} {target_key} {TARGET_FILENAME} {file_size} {file_crc}\n'
        print(f"   Command: {put_cmd.strip()}")
        
        ser.write(put_cmd.encode())
        ser.flush()
        time.sleep(2)
        
        put_response = ser.read_all().decode('utf-8', errors='replace')
        print(f"   PUT response: {repr(put_response)}")
        
        if 'PUT:READY' in put_response:
            print("   ✓ Device ready for upload")
            
            # Upload file data
            print("\n5. Uploading file data...")
            bytes_sent = 0
            start_time = time.time()
            
            with open(SOURCE_FILE, 'rb') as f:
                while True:
                    chunk = f.read(WRITE_CHUNK)
                    if not chunk:
                        break
                    
                    ser.write(chunk)
                    ser.flush()
                    time.sleep(PAUSE_SEC)
                    bytes_sent += len(chunk)
                    
                    # Progress every 1MB
                    if bytes_sent % (1024 * 1024) == 0:
                        elapsed = time.time() - start_time
                        rate = bytes_sent / elapsed / 1024
                        progress = (bytes_sent / file_size) * 100
                        print(f"   Progress: {bytes_sent:,}/{file_size:,} bytes ({progress:.1f}%) - {rate:.1f} KB/s")
            
            ser.flush()
            print(f"   ✓ Sent {bytes_sent:,} bytes")
            
            # Wait for completion
            print("\n6. Waiting for upload completion...")
            completion_timeout = 30  # 30 seconds for large file
            for i in range(completion_timeout):
                time.sleep(1)
                completion_response = ser.read_all().decode('utf-8', errors='replace')
                if completion_response:
                    print(f"   Response: {repr(completion_response)}")
                    if 'PUT:DONE' in completion_response:
                        print("   ✓ Upload completed successfully!")
                        break
                    elif 'ERR:' in completion_response:
                        print(f"   ✗ Upload failed: {completion_response}")
                        break
                else:
                    if i % 5 == 0:  # Progress indicator every 5 seconds
                        print(f"   Waiting... ({i+1}/{completion_timeout}s)")
            
            # Verify upload
            print(f"\n7. Verifying upload...")
            ser.write(f'LS {TARGET_BANK} {target_key}\n'.encode())
            ser.flush()
            time.sleep(1)
            
            verify_response = ser.read_all().decode('utf-8', errors='replace')
            print(f"   Verification: {repr(verify_response)}")
            
            if TARGET_FILENAME in verify_response:
                print("   ✓ File found in directory listing")
            else:
                print("   ⚠ File not found in listing")
        
        elif 'ERR:MKDIR' in put_response:
            print(f"   ⚠ Directory creation needed for {target_key}")
            print("   The file upload failed because the directory doesn't exist")
            print("   You may need to create the directory structure on the SD card")
        elif 'ERR:' in put_response:
            print(f"   ✗ PUT command failed: {put_response}")
        else:
            print("   ✗ Unexpected PUT response")
        
        # Exit data mode
        print("\n8. Exiting data mode...")
        ser.write(b'EXIT\n')
        ser.flush()
        time.sleep(0.5)
        
        exit_response = ser.read_all().decode('utf-8', errors='replace')
        if exit_response:
            print(f"   Exit: {repr(exit_response)}")
        
        ser.close()
        print("   ✓ Connection closed")
        
        return 'PUT:DONE' in locals().get('completion_response', '')
        
    except Exception as e:
        print(f"\n✗ Upload failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("This will upload 005.mp3 to the HUMAN directory on your tactile device.")
    print("The script will check for existing directories and upload to an available location.")
    print()
    
    success = upload_mp3_to_human()
    
    if success:
        print("\n" + "=" * 60)
        print("🎉 MP3 UPLOAD SUCCESSFUL!")
        print("Your audio file is now available on the tactile device")
        print("=" * 60)
    else:
        print("\n" + "=" * 60)
        print("❌ UPLOAD INCOMPLETE")
        print("Check the output above for details")
        print("You may need to create the directory structure on the SD card")
        print("=" * 60)
