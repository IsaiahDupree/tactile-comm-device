import serial
import time

def simple_test():
    try:
        ser = serial.Serial('COM5', 115200, timeout=1)
        time.sleep(2)  # Boot delay
        ser.reset_input_buffer()
        
        # Send handshake
        ser.write(b'^DATA? v1\n')
        ser.flush()
        time.sleep(0.5)
        
        # Read response
        response = ser.read_all().decode('utf-8', errors='ignore')
        print(f"Response: {repr(response)}")
        
        if 'DATA:OK' in response:
            print("✓ Handshake works")
            
            # Test STATUS command
            ser.write(b'STATUS\n')
            ser.flush()
            time.sleep(0.2)
            status = ser.read_all().decode('utf-8', errors='ignore')
            print(f"Status: {repr(status)}")
            
            # Exit data mode
            ser.write(b'EXIT\n')
            ser.flush()
        else:
            print("✗ Handshake failed")
            
        ser.close()
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    simple_test()
