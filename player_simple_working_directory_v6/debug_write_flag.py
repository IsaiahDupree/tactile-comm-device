import serial
import time

def debug_write_flag():
    print("Debugging write flag and PUT command...")
    
    ser = serial.Serial('COM5', 115200, timeout=3, write_timeout=5.0)
    time.sleep(2.5)
    ser.reset_input_buffer()
    
    try:
        # Handshake
        print("1. Handshake...")
        ser.write(b'^DATA? v1\n')
        ser.flush()
        response = ser.readline().decode().strip()
        print(f"   {response}")
        ser.readline()  # Skip info line
        
        # Check STATUS first
        print("2. Check STATUS...")
        ser.write(b'STATUS\n')
        ser.flush()
        status_response = ser.readline().decode().strip()
        print(f"   {status_response}")
        
        # Try FLAG ON
        print("3. FLAG ON...")
        ser.write(b'FLAG ON\n')
        ser.flush()
        flag_response = ser.readline().decode().strip()
        print(f"   {flag_response}")
        
        # Check STATUS again
        print("4. Check STATUS after FLAG ON...")
        ser.write(b'STATUS\n')
        ser.flush()
        status2_response = ser.readline().decode().strip()
        print(f"   {status2_response}")
        
        # Now try PUT
        print("5. Try PUT command...")
        ser.write(b'PUT HUMAN A TEST.WAV 5 12345\n')
        ser.flush()
        
        # Read response with timeout
        start_time = time.time()
        while time.time() - start_time < 10:
            line = ser.readline().decode().strip()
            if line:
                print(f"   PUT response: {line}")
                if 'PUT:READY' in line:
                    print("   ✓ Success! Sending payload...")
                    ser.write(b'HELLO')
                    ser.flush()
                    done_line = ser.readline().decode().strip()
                    print(f"   Final: {done_line}")
                    break
                elif 'ERR:' in line:
                    print(f"   ✗ Error: {line}")
                    break
        else:
            print("   ✗ No response to PUT command")
        
        # Exit
        ser.write(b'EXIT\n')
        ser.readline()
        
    finally:
        ser.close()

if __name__ == "__main__":
    debug_write_flag()
