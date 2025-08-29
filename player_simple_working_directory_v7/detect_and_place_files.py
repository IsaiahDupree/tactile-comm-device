#!/usr/bin/env python3
"""
Detect files in GENERA~1 directories and place files in known locations
"""
import serial
import time
import os
import binascii
from pathlib import Path

def print_inventory(title, inv):
    """Show a factual summary (only keys that actually have files)"""
    print(f"\n=== {title} ===")
    any_files = False
    for k, files in inv.items():
        if files:
            any_files = True
            print(f"{k}: {len(files)} file(s)")
            for f in files[:5]:
                print(f"  • {f['name']} ({f['size']} bytes)")
    if not any_files:
        print("(no files found)")

# Configuration
SERIAL_PORT = "COM5"
BAUD = 115200
TIMEOUT = 3

def crc32_file(filepath):
    """Calculate CRC32 of file"""
    crc = 0
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            crc = binascii.crc32(chunk, crc)
    return crc & 0xFFFFFFFF

def connect_device():
    """Connect to device using reliable handshake"""
    print("Connecting to tactile device...")
    ser = serial.Serial(SERIAL_PORT, BAUD, timeout=TIMEOUT)
    time.sleep(3)  # Boot delay
    ser.reset_input_buffer()
    
    # Handshake
    ser.write(b'^DATA? v1\n')
    ser.flush()
    time.sleep(1.5)
    
    response = ser.read_all().decode('utf-8', errors='replace')
    if 'DATA:OK' not in response:
        raise Exception(f"Handshake failed: {response}")
    
    print("✓ Connected and in data mode")
    return ser

def ls_key(ser, bank: str, key: str):
    """Return list of (name, size) or [] if empty; None if directory missing."""
    ser.write(f'LS {bank} {key}\n'.encode('utf-8'))
    ser.flush()

    files = []
    while True:
        line = ser.readline().decode('utf-8', errors='replace').strip()
        if not line:
            continue
        if line == 'LS:DONE':
            return files                # empty ok
        if line == 'LS:NODIR':
            return None                 # key dir not present
        if line.startswith('LS:'):
            parts = line[3:].strip().split()
            if len(parts) >= 2:
                files.append((parts[0], parts[1]))
        # ignore any other chatter

def scan_bank(ser, bank: str):
    """Scan all keys in a bank and return inventory"""
    KEYS = ['SHIFT','PERIOD','SPACE','YES','NO','WATER'] + [chr(c) for c in range(65,91)]
    
    inv = {}
    for k in KEYS:
        result = ls_key(ser, bank, k)
        if result is None:
            continue            # dir doesn't exist
        inv[k] = [{'name': n, 'size': s} for (n, s) in result]  # [] when empty
    return inv

def scan_genera_directories(ser):
    """Scan all directories in GENERA~1 and return file inventory"""
    print("\nScanning /AUDIO/GENERA~1/<KEY> ...")
    return scan_bank(ser, "GENERA~1")

def scan_human_directories(ser):
    """Scan all directories in HUMAN and return file inventory"""
    print("\nScanning /AUDIO/HUMAN/<KEY> ...")
    return scan_bank(ser, "HUMAN")

def find_available_slot(inventory, target_dir):
    """Find next available numbered slot in a directory"""
    if target_dir not in inventory:
        return "001"
    
    existing_numbers = []
    for file in inventory[target_dir]:
        name = file['name']
        if name.endswith('.MP3') and len(name) == 7:  # Format: 001.MP3
            try:
                num = int(name[:3])
                existing_numbers.append(num)
            except ValueError:
                continue
    
    # Find next available number
    for i in range(1, 1000):
        if i not in existing_numbers:
            return f"{i:03d}"
    
    return "999"  # Fallback

def upload_to_directory(ser, source_file, target_bank, target_dir, filename=None):
    """Upload file to specified bank/directory"""
    if not os.path.exists(source_file):
        print(f"✗ Source file not found: {source_file}")
        return False
    
    file_size = os.path.getsize(source_file)
    file_crc = crc32_file(source_file)
    
    if filename is None:
        filename = os.path.basename(source_file)
    
    print(f"\nUploading to {target_bank}/{target_dir}...")
    print(f"  Source: {source_file}")
    print(f"  Target: {filename}")
    print(f"  Size: {file_size:,} bytes")
    print(f"  CRC32: {file_crc:08X}")
    
    # PUT command
    put_cmd = f'PUT {target_bank} {target_dir} {filename} {file_size} {file_crc}\n'
    ser.write(put_cmd.encode())
    ser.flush()
    time.sleep(2)
    
    put_response = ser.read_all().decode('utf-8', errors='replace')
    print(f"  PUT response: {repr(put_response)}")
    
    if 'PUT:READY' not in put_response:
        print(f"  ✗ Upload failed: {put_response}")
        return False
    
    print("  ✓ Device ready - uploading...")
    
    # Upload file data
    bytes_sent = 0
    chunk_size = 1024
    start_time = time.time()
    
    with open(source_file, 'rb') as f:
        while True:
            chunk = f.read(chunk_size)
            if not chunk:
                break
            
            ser.write(chunk)
            bytes_sent += len(chunk)
            
            # Progress every 1MB
            if bytes_sent % (1024 * 1024) == 0:
                elapsed = time.time() - start_time
                rate = bytes_sent / elapsed / 1024 if elapsed > 0 else 0
                progress = (bytes_sent / file_size) * 100
                print(f"    Progress: {bytes_sent:,}/{file_size:,} ({progress:.1f}%) - {rate:.1f} KB/s")
    
    ser.flush()
    print(f"  ✓ Sent {bytes_sent:,} bytes")
    
    # Wait for completion
    print("  Waiting for completion...")
    for i in range(30):
        time.sleep(1)
        completion = ser.read_all().decode('utf-8', errors='replace')
        if completion:
            if 'PUT:DONE' in completion:
                print("  ✓ Upload successful!")
                return True
            elif 'ERR:' in completion:
                print(f"  ✗ Error: {completion}")
                return False
        elif i % 5 == 0:
            print(f"    Waiting... ({i+1}/30s)")
    
    print("  ⚠ Upload timeout")
    return False

def interactive_file_placement():
    """Interactive mode for placing files"""
    print("\n" + "=" * 60)
    print("TACTILE DEVICE FILE DETECTION AND PLACEMENT")
    print("=" * 60)
    
    try:
        ser = connect_device()
        
        # Scan existing files in both banks
        genera_inventory = scan_genera_directories(ser)
        human_inventory = scan_human_directories(ser)
        
        print_inventory("GENERA~1 INVENTORY", genera_inventory)
        print_inventory("HUMAN INVENTORY", human_inventory)
        
        # Combine inventories for selection
        inventory = {'GENERA~1': genera_inventory, 'HUMAN': human_inventory}
        
        # Interactive placement
        while True:
            print("\n" + "=" * 60)
            print("FILE PLACEMENT OPTIONS")
            print("=" * 60)
            print("1. Upload to specific directory")
            print("2. Upload to next available slot")
            print("3. Rescan directories")
            print("4. Exit")
            
            choice = input("\nSelect option (1-4): ").strip()
            
            if choice == "1":
                # Manual directory selection
                print("\nAvailable banks and directories:")
                for bank, dirs in inventory.items():
                    non_empty = [k for k, files in dirs.items() if files]
                    if non_empty:
                        print(f"  {bank}: {non_empty}")
                    else:
                        print(f"  {bank}: (all directories empty)")
                
                target_bank = input("Enter target bank (GENERA~1 or HUMAN): ").strip()
                target_dir = input("Enter target directory: ").strip().upper()
                
                if target_bank not in inventory or target_dir not in ['A','B','C','D','E','F','G','H','I','J','K','L','M','N','O','P','Q','R','S','T','U','V','W','X','Y','Z','SHIFT','PERIOD','SPACE','YES','NO','WATER']:
                    print(f"Invalid bank or directory")
                    continue
                
                source_file = input("Enter source file path: ").strip()
                filename = input("Enter target filename (or press Enter for auto): ").strip()
                
                if not filename:
                    filename = os.path.basename(source_file)
                
                success = upload_to_directory(ser, source_file, target_bank, target_dir, filename)
                if success:
                    # Update inventory
                    genera_inventory = scan_genera_directories(ser)
                    human_inventory = scan_human_directories(ser)
                    inventory = {'GENERA~1': genera_inventory, 'HUMAN': human_inventory}
            
            elif choice == "2":
                # Auto-slot placement
                print("\nAvailable banks and directories:")
                for bank, dirs in inventory.items():
                    non_empty = [k for k, files in dirs.items() if files]
                    if non_empty:
                        print(f"  {bank}: {non_empty}")
                    else:
                        print(f"  {bank}: (all directories empty)")
                
                target_bank = input("Enter target bank (GENERA~1 or HUMAN): ").strip()
                target_dir = input("Enter target directory: ").strip().upper()
                
                if target_bank not in inventory or target_dir not in ['A','B','C','D','E','F','G','H','I','J','K','L','M','N','O','P','Q','R','S','T','U','V','W','X','Y','Z','SHIFT','PERIOD','SPACE','YES','NO','WATER']:
                    print(f"Invalid bank or directory")
                    continue
                
                source_file = input("Enter source file path: ").strip()
                
                # Find next available slot
                slot = find_available_slot(inventory[target_bank], target_dir)
                filename = f"{slot}.MP3"
                
                print(f"Auto-assigned filename: {filename}")
                
                success = upload_to_directory(ser, source_file, target_bank, target_dir, filename)
                if success:
                    # Update inventory
                    genera_inventory = scan_genera_directories(ser)
                    human_inventory = scan_human_directories(ser)
                    inventory = {'GENERA~1': genera_inventory, 'HUMAN': human_inventory}
            
            elif choice == "3":
                # Rescan
                genera_inventory = scan_genera_directories(ser)
                human_inventory = scan_human_directories(ser)
                inventory = {'GENERA~1': genera_inventory, 'HUMAN': human_inventory}
            
            elif choice == "4":
                break
            
            else:
                print("Invalid choice")
        
        # Exit data mode
        print("\nExiting data mode...")
        ser.write(b'EXIT\n')
        ser.flush()
        ser.close()
        print("✓ Disconnected")
        
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()

def quick_upload(source_file, target_dir, filename=None):
    """Quick upload function for scripted use"""
    try:
        ser = connect_device()
        
        if filename is None:
            # Scan to find next available slot
            inventory = scan_genera_directories(ser)
            slot = find_available_slot(inventory, target_dir)
            filename = f"{slot}.MP3"
            print(f"Auto-assigned filename: {filename}")
        
        success = upload_to_directory(ser, source_file, target_dir, filename)
        
        # Exit
        ser.write(b'EXIT\n')
        ser.flush()
        ser.close()
        
        return success
        
    except Exception as e:
        print(f"✗ Error: {e}")
        return False

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) >= 3:
        # Command line mode: python script.py <source_file> <target_dir> [filename]
        source_file = sys.argv[1]
        target_dir = sys.argv[2].upper()
        filename = sys.argv[3] if len(sys.argv) > 3 else None
        
        print(f"Quick upload: {source_file} -> GENERA~1/{target_dir}/{filename or 'auto'}")
        success = quick_upload(source_file, target_dir, filename)
        
        if success:
            print("🎉 Upload successful!")
        else:
            print("❌ Upload failed!")
    else:
        # Interactive mode
        interactive_file_placement()
