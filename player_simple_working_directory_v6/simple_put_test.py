import serial
import time

def simple_put_test():
    print("Testing basic PUT command flow...")
    
    ser = serial.Serial('COM5', 115200, timeout=3, write_timeout=5.0)
    time.sleep(2.5)
    ser.reset_input_buffer()
    
    try:
        # Handshake
        print("1. Handshake...")
        ser.write(b'^DATA? v1\n')
        ser.flush()
        response = ser.readline().decode().strip()
        print(f"   Response: {response}")
        if 'DATA:OK' not in response:
            print("   ✗ Handshake failed")
            return
        
        # Skip info line
        ser.readline()
        
        # Enable writes
        print("2. Enable writes...")
        ser.write(b'FLAG ON\n')
        ser.flush()
        flag_response = ser.readline().decode().strip()
        print(f"   Response: {flag_response}")
        
        # Try PUT command with small payload
        print("3. PUT command...")
        put_cmd = "PUT HUMAN A TEST.WAV 10 1234567890\n"
        print(f"   Sending: {put_cmd.strip()}")
        ser.write(put_cmd.encode())
        ser.flush()
        
        # Wait for response
        start_time = time.time()
        while time.time() - start_time < 15:
            line = ser.readline().decode().strip()
            if line:
                print(f"   Response: {line}")
                if 'PUT:READY' in line:
                    print("   ✓ Got PUT:READY")
                    # Send small payload
                    ser.write(b'1234567890')
                    ser.flush()
                    
                    # Wait for PUT:DONE
                    done_response = ser.readline().decode().strip()
                    print(f"   Final: {done_response}")
                    break
                elif 'ERR:' in line:
                    print(f"   ✗ Error: {line}")
                    break
        else:
            print("   ✗ Timeout waiting for PUT:READY")
        
        # Exit
        ser.write(b'EXIT\n')
        ser.readline()
        
    finally:
        ser.close()

if __name__ == "__main__":
    simple_put_test()
