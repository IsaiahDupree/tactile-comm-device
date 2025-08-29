#!/usr/bin/env python3
"""
Upload MP3 file specifically to HUMAN/J directory on tactile device
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
TARGET_BANK = "GENERA~1"
TARGET_KEY = "J"
TARGET_FILENAME = "005.MP3"

def crc32_file(filepath):
    """Calculate CRC32 of file"""
    crc = 0
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            crc = binascii.crc32(chunk, crc)
    return crc & 0xFFFFFFFF

def upload_to_human_j():
    """Upload MP3 file to HUMAN/J directory"""
    print("=" * 60)
    print("UPLOADING 005.MP3 TO GENERA~1/J DIRECTORY")
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
    print(f"Target: /{TARGET_BANK}/{TARGET_KEY}/{TARGET_FILENAME}")
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
        
        # Check if J directory exists in HUMAN bank
        print(f"\n3. Checking {TARGET_BANK}/{TARGET_KEY} directory...")
        ser.write(f'LS {TARGET_BANK} {TARGET_KEY}\n'.encode())
        ser.flush()
        time.sleep(1)
        
        ls_response = ser.read_all().decode('utf-8', errors='replace')
        print(f"   LS response: {repr(ls_response)}")
        
        if 'ERR:' in ls_response:
            print(f"   Directory {TARGET_KEY} may not exist - will attempt to create")
        else:
            print(f"   ✓ Directory {TARGET_KEY} accessible")
        
        # Attempt PUT command to HUMAN/J
        print(f"\n4. Uploading to {TARGET_BANK}/{TARGET_KEY}...")
        put_cmd = f'PUT {TARGET_BANK} {TARGET_KEY} {TARGET_FILENAME} {file_size} {file_crc}\n'
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
                        rate = bytes_sent / elapsed / 1024 if elapsed > 0 else 0
                        progress = (bytes_sent / file_size) * 100
                        print(f"   Progress: {bytes_sent:,}/{file_size:,} bytes ({progress:.1f}%) - {rate:.1f} KB/s")
            
            ser.flush()
            print(f"   ✓ Sent {bytes_sent:,} bytes")
            
            # Wait for completion
            print("\n6. Waiting for upload completion...")
            completion_timeout = 30  # 30 seconds for large file
            upload_complete = False
            
            for i in range(completion_timeout):
                time.sleep(1)
                completion_response = ser.read_all().decode('utf-8', errors='replace')
                if completion_response:
                    print(f"   Response: {repr(completion_response)}")
                    if 'PUT:DONE' in completion_response:
                        print("   ✓ Upload completed successfully!")
                        upload_complete = True
                        break
                    elif 'ERR:' in completion_response:
                        print(f"   ✗ Upload failed: {completion_response}")
                        break
                else:
                    if i % 5 == 0:  # Progress indicator every 5 seconds
                        print(f"   Waiting... ({i+1}/{completion_timeout}s)")
            
            if upload_complete:
                # Verify upload
                print(f"\n7. Verifying upload...")
                ser.write(f'LS {TARGET_BANK} {TARGET_KEY}\n'.encode())
                ser.flush()
                time.sleep(1)
                
                verify_response = ser.read_all().decode('utf-8', errors='replace')
                print(f"   Verification: {repr(verify_response)}")
                
                if TARGET_FILENAME in verify_response:
                    print("   ✓ File found in directory listing")
                    success = True
                else:
                    print("   ⚠ File not found in listing")
                    success = False
            else:
                success = False
        
        elif 'ERR:MKDIR' in put_response:
            print(f"   ⚠ Directory {TARGET_KEY} needs to be created")
            print("   The upload failed because the J directory doesn't exist")
            print("   You may need to create /AUDIO/HUMAN/J/ on the SD card")
            success = False
        elif 'ERR:' in put_response:
            print(f"   ✗ PUT command failed: {put_response}")
            success = False
        else:
            print("   ✗ Unexpected PUT response")
            success = False
        
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
        
        return success
        
    except Exception as e:
        print(f"\n✗ Upload failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("This will upload 005.mp3 to the GENERA~1/J directory on your tactile device.")
    print("If the J directory doesn't exist, the device will attempt to create it.")
    print()
    
    success = upload_to_human_j()
    
    if success:
        print("\n" + "=" * 60)
        print("🎉 MP3 UPLOAD TO GENERA~1/J SUCCESSFUL!")
        print("Your 005.mp3 file is now available in the J directory")
        print("=" * 60)
    else:
        print("\n" + "=" * 60)
        print("❌ UPLOAD TO GENERA~1/J INCOMPLETE")
        print("Check the output above for details")
        print("You may need to create the /AUDIO/GENERA~1/J/ directory on the SD card")
        print("=" * 60)
