#!/usr/bin/env python3
"""
Transfer Priority Mode Announcement Audio Files to Device
Uses the Serial FS Protocol to upload announcement files to the device SD card

This script transfers the locally generated audio files to the correct location
on the device SD card using the M4 Serial FS Protocol.
"""

import os
import sys
import time
import serial
import serial.tools.list_ports
import binascii
import struct

# CRC32 calculation (matching the firmware implementation)
def calculate_crc32(data):
    crc = 0xFFFFFFFF
    for byte in data:
        crc ^= byte
        for _ in range(8):
            if crc & 1:
                crc = (crc >> 1) ^ 0xEDB88320
            else:
                crc = crc >> 1
    return ~crc & 0xFFFFFFFF

# Serial FS Protocol commands
FS_BEGIN = b'FSBEGIN'  # Start a file transfer session
FS_PUT = b'FSPUT'      # Initialize a file transfer
FS_DATA = b'FSDATA'    # Send file data chunk
FS_DONE = b'FSDONE'    # Finish a file transfer
FS_COMMIT = b'FSCOMIT' # Commit all changes
FS_ABORT = b'FSABORT'  # Abort the transfer session

# Find the Arduino device
def find_arduino():
    print("Searching for Arduino device...")
    ports = list(serial.tools.list_ports.comports())
    
    for port in ports:
        # Look for common Arduino/FTDI/CH340 identifiers
        if any(id in port.description.lower() for id in ["arduino", "ch340", "ftdi"]):
            print(f"Found device: {port.device} ({port.description})")
            return port.device
    
    # If no specific Arduino found, show all ports
    print("No Arduino device found. Available ports:")
    for i, port in enumerate(ports):
        print(f"{i+1}. {port.device} - {port.description}")
    
    if ports:
        selection = input("Enter port number to use (or Enter to quit): ")
        if selection.isdigit() and 1 <= int(selection) <= len(ports):
            return ports[int(selection)-1].device
    
    return None

# Connect to the Arduino
def connect_to_device(port, baud_rate=115200, timeout=5):
    try:
        ser = serial.Serial(port, baud_rate, timeout=timeout)
        time.sleep(2)  # Allow time for Arduino reset
        ser.reset_input_buffer()
        return ser
    except Exception as e:
        print(f"Error connecting to device: {str(e)}")
        return None

# Wait for response
def wait_for_response(ser, expected=None, timeout=5):
    start_time = time.time()
    response = b''
    
    while (time.time() - start_time) < timeout:
        if ser.in_waiting > 0:
            data = ser.read(ser.in_waiting)
            response += data
            if expected and expected in response:
                return True, response.decode('utf-8', errors='ignore')
            if b'ERROR' in response:
                return False, response.decode('utf-8', errors='ignore')
        time.sleep(0.1)
    
    return False, response.decode('utf-8', errors='ignore')

# Send file to device
def transfer_file(ser, source_path, target_path):
    if not os.path.exists(source_path):
        print(f"Error: Source file not found: {source_path}")
        return False
    
    file_size = os.path.getsize(source_path)
    print(f"Transferring {os.path.basename(source_path)} ({file_size} bytes) -> {target_path}")
    
    # Begin FS session
    print("Starting file transfer session...")
    ser.write(FS_BEGIN + b'\n')
    success, response = wait_for_response(ser, b'OK', 5)
    if not success:
        print(f"Session start failed: {response}")
        return False
    print("Session started successfully")
    
    # Prepare file transfer
    print(f"Preparing file: {target_path}")
    command = FS_PUT + b' ' + target_path.encode() + b' ' + str(file_size).encode() + b'\n'
    ser.write(command)
    success, response = wait_for_response(ser, b'READY', 5)
    if not success:
        print(f"File preparation failed: {response}")
        return False
    
    # Send file data in chunks
    with open(source_path, 'rb') as f:
        total_sent = 0
        chunk_size = 512  # Using 512-byte chunks
        
        while total_sent < file_size:
            chunk = f.read(chunk_size)
            if not chunk:
                break
                
            # Calculate CRC32
            crc = calculate_crc32(chunk)
            
            # Send data chunk with CRC
            header = FS_DATA + b' ' + str(len(chunk)).encode() + b' ' + hex(crc).encode()[2:].zfill(8).encode() + b'\n'
            ser.write(header)
            ser.write(chunk)
            
            success, response = wait_for_response(ser, b'OK', 5)
            if not success:
                print(f"Chunk transfer failed: {response}")
                return False
                
            total_sent += len(chunk)
            progress = (total_sent / file_size) * 100
            print(f"Progress: {progress:.1f}% ({total_sent}/{file_size} bytes)")
    
    # Mark file transfer as done
    ser.write(FS_DONE + b'\n')
    success, response = wait_for_response(ser, b'OK', 5)
    if not success:
        print(f"File completion failed: {response}")
        return False
        
    print(f"File transfer completed successfully: {target_path}")
    return True

# Commit changes
def commit_changes(ser):
    print("Committing changes...")
    ser.write(FS_COMMIT + b'\n')
    success, response = wait_for_response(ser, b'OK', 10)  # Longer timeout for commit
    if not success:
        print(f"Commit failed: {response}")
        return False
    print("Changes committed successfully")
    return True

# Abort session
def abort_session(ser):
    print("Aborting session...")
    ser.write(FS_ABORT + b'\n')
    success, response = wait_for_response(ser, b'OK', 5)
    print("Session aborted")

# Main function
def main():
    # Path to the audio files
    audio_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "audio_announcements", "33")
    
    # Files to transfer
    transfer_files = [
        ("001.mp3", "/33/001.mp3", "Human first mode"),
        ("002.mp3", "/33/002.mp3", "Generated first mode")
    ]
    
    # Check if files exist
    for filename, _, _ in transfer_files:
        file_path = os.path.join(audio_dir, filename)
        if not os.path.exists(file_path):
            print(f"Error: File not found: {file_path}")
            return
    
    # Find Arduino device
    port = find_arduino()
    if not port:
        print("No device selected. Exiting.")
        return
    
    # Connect to device
    print(f"Connecting to {port}...")
    ser = connect_to_device(port)
    if not ser:
        print("Failed to connect to device. Exiting.")
        return
    
    try:
        # Transfer each file
        all_successful = True
        for filename, target_path, description in transfer_files:
            source_path = os.path.join(audio_dir, filename)
            print(f"\nTransferring '{description}' announcement...")
            success = transfer_file(ser, source_path, target_path)
            if not success:
                all_successful = False
                break
        
        # Commit or abort
        if all_successful:
            if commit_changes(ser):
                print("\nAll announcement files transferred successfully!")
                print("Now you can use the 'M' serial command or the triple-press")
                print("of the period button to toggle priority modes with announcements.")
            else:
                print("Failed to commit changes. Files may not be available.")
        else:
            abort_session(ser)
            print("Transfer process failed. No changes were made to the device.")
    
    except Exception as e:
        print(f"Error during transfer: {str(e)}")
        # Try to abort if there's an exception
        try:
            abort_session(ser)
        except:
            pass
    finally:
        if ser and ser.is_open:
            ser.close()

if __name__ == "__main__":
    main()
