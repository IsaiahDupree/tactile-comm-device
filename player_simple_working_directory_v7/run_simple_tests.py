#!/usr/bin/env python3
import os
import sys
import time
import traceback

# Add tests directory to path
sys.path.insert(0, os.path.join(os.getcwd(), 'tests'))

def create_sample_mp3():
    """Create a minimal sample MP3 file for testing"""
    data = b'ID3\x03\x00\x00\x00\x00\x00\x00' + b'\xff\xfb\x90\x00' * 100
    with open('sample.mp3', 'wb') as f:
        f.write(data)
    print(f"Created sample.mp3: {len(data)} bytes")

def run_individual_tests():
    """Run each test individually to isolate issues"""
    create_sample_mp3()
    
    # Ensure test_results directory exists
    os.makedirs('test_results', exist_ok=True)
    
    results = []
    
    # Import test modules directly
    try:
        from config import SERIAL_PORT, BAUD, READ_TIMEOUT, BANK, KEY, FILENAME, LOCAL_MP3
        from proto_utils import open_serial, enter_data_mode, read_line, write_line
        from data_ops import cmd_put, cmd_get, cmd_ls, cmd_del, cmd_status, crc32_file
        
        print("✓ All imports successful")
        results.append("IMPORT_SUCCESS: All modules imported successfully")
        
        # Test 1: Basic handshake and status
        print("\n=== Test 1: Handshake and Status ===")
        try:
            ser = open_serial(SERIAL_PORT, BAUD, READ_TIMEOUT)
            print(f"✓ Serial port {SERIAL_PORT} opened")
            
            enter_data_mode(ser)
            print("✓ Handshake successful")
            
            # Test STATUS command
            ser.write(b"STATUS\n")
            ser.flush()
            time.sleep(0.5)
            
            seen = []
            for _ in range(8):
                line = ser.readline().decode("utf-8", errors="replace").strip()
                if line:
                    seen.append(line)
                    print(f"  STATUS response: {line}")
                    if line.startswith("STATUS "):
                        if "WRITES=ON" in line and "MODE=OPEN" in line:
                            print("✓ STATUS shows OPEN mode with writes enabled")
                            results.append("TEST1_PASS: Handshake and status successful")
                        else:
                            print(f"✗ Unexpected STATUS: {line}")
                            results.append(f"TEST1_FAIL: Unexpected STATUS: {line}")
                        break
            else:
                print(f"✗ No STATUS response found in: {seen}")
                results.append(f"TEST1_FAIL: No STATUS response: {seen}")
            
            ser.close()
            
        except Exception as e:
            print(f"✗ Test 1 failed: {e}")
            results.append(f"TEST1_ERROR: {e}")
            traceback.print_exc()
        
        # Test 2: Simple PUT operation (if sample MP3 exists)
        if os.path.exists(LOCAL_MP3):
            print(f"\n=== Test 2: PUT Operation with {LOCAL_MP3} ===")
            try:
                ser = open_serial(SERIAL_PORT, BAUD, READ_TIMEOUT)
                enter_data_mode(ser)
                
                put_resp = cmd_put(ser, BANK, KEY, FILENAME, LOCAL_MP3, use_crc=True)
                print(f"PUT response: {put_resp}")
                
                if put_resp == "PUT:DONE":
                    print("✓ PUT operation successful")
                    results.append("TEST2_PASS: PUT operation successful")
                else:
                    print(f"✗ PUT failed: {put_resp}")
                    results.append(f"TEST2_FAIL: PUT failed: {put_resp}")
                
                ser.close()
                
            except Exception as e:
                print(f"✗ Test 2 failed: {e}")
                results.append(f"TEST2_ERROR: {e}")
                traceback.print_exc()
        else:
            print(f"\n=== Test 2: SKIPPED - {LOCAL_MP3} not found ===")
            results.append("TEST2_SKIP: Sample MP3 not found")
        
        # Test 3: LS command
        print(f"\n=== Test 3: LS Command ===")
        try:
            ser = open_serial(SERIAL_PORT, BAUD, READ_TIMEOUT)
            enter_data_mode(ser)
            
            listing = cmd_ls(ser, BANK, KEY)
            print(f"LS response: {listing}")
            
            if isinstance(listing, list):
                print(f"✓ LS successful, found {len(listing)} files")
                results.append(f"TEST3_PASS: LS found {len(listing)} files")
            else:
                print(f"✗ LS failed: {listing}")
                results.append(f"TEST3_FAIL: LS failed: {listing}")
            
            ser.close()
            
        except Exception as e:
            print(f"✗ Test 3 failed: {e}")
            results.append(f"TEST3_ERROR: {e}")
            traceback.print_exc()
        
    except ImportError as e:
        print(f"✗ Import failed: {e}")
        results.append(f"IMPORT_ERROR: {e}")
        traceback.print_exc()
    
    # Write results to file
    with open('test_results/simple_test_results.txt', 'w') as f:
        f.write("SIMPLE TEST RESULTS\n")
        f.write("=" * 50 + "\n")
        f.write(f"Test run at: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Serial port: {SERIAL_PORT if 'SERIAL_PORT' in locals() else 'Unknown'}\n\n")
        
        for result in results:
            f.write(f"{result}\n")
    
    print(f"\n=== Test Summary ===")
    for result in results:
        print(f"  {result}")
    
    print("\nResults written to test_results/simple_test_results.txt")

if __name__ == "__main__":
    run_individual_tests()
