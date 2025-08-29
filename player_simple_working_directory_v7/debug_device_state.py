import serial
import time

def debug_device():
    print("Debugging device state on COM5...")
    
    try:
        ser = serial.Serial('COM5', 115200, timeout=1)
        time.sleep(2.5)  # Boot delay
        ser.reset_input_buffer()
        
        print("1. Testing basic connectivity...")
        ser.write(b'H')  # Help command
        time.sleep(0.5)
        response = ser.read_all().decode(errors='ignore')
        print(f"Help response length: {len(response)} bytes")
        
        print("\n2. Testing handshake...")
        ser.reset_input_buffer()
        ser.write(b'^DATA? v1\n')
        
        # Read with timeout
        start_time = time.time()
        response_lines = []
        while time.time() - start_time < 5:
            line = ser.readline().decode(errors='ignore').strip()
            if line:
                response_lines.append(line)
                print(f"Line: {line}")
                if 'DATA:OK' in line:
                    print("✓ Handshake successful")
                    # Try to exit data mode
                    ser.write(b'EXIT\n')
                    exit_line = ser.readline().decode(errors='ignore').strip()
                    print(f"Exit: {exit_line}")
                    break
        else:
            print("✗ Handshake timeout")
            
        ser.close()
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    debug_device()
