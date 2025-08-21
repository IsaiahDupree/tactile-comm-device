import serial
import time
import sys

def test_connection():
    try:
        print("Testing connection to COM5...")
        ser = serial.Serial('COM5', 115200, timeout=3, write_timeout=2)
        print("Serial port opened successfully")
        
        # Wait for device boot
        print("Waiting for device boot...")
        time.sleep(3)
        ser.reset_input_buffer()
        
        # Try handshake
        print("Sending handshake...")
        ser.write(b'^DATA? v1\n')
        ser.flush()
        
        # Read response with timeout
        response = ser.read_all()
        if response:
            print(f"Raw response: {response}")
            decoded = response.decode('utf-8', errors='ignore')
            print(f"Decoded: {repr(decoded)}")
            
            if 'DATA:OK' in decoded:
                print("✓ Handshake successful!")
                return True
            else:
                print("✗ Unexpected handshake response")
        else:
            print("✗ No response to handshake")
            
    except serial.SerialException as e:
        print(f"Serial error: {e}")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        try:
            ser.close()
        except:
            pass
    
    return False

if __name__ == "__main__":
    success = test_connection()
    sys.exit(0 if success else 1)
