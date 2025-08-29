import serial
import time

def quick_test():
    print("Quick test of modified firmware...")
    
    ser = serial.Serial('COM5', 115200, timeout=2)
    time.sleep(2.5)
    ser.reset_input_buffer()
    
    try:
        # Handshake
        ser.write(b'^DATA? v1\n')
        ser.flush()
        response = ser.readline().decode().strip()
        print(f"Handshake: {response}")
        ser.readline()  # Skip info line
        
        # Check STATUS to see if we're in OPEN mode
        ser.write(b'STATUS\n')
        ser.flush()
        status = ser.readline().decode().strip()
        print(f"Status: {status}")
        
        # Try PUT without FLAG ON
        ser.write(b'PUT HUMAN A TEST.WAV 5 12345\n')
        ser.flush()
        put_response = ser.readline().decode().strip()
        print(f"PUT response: {put_response}")
        
        if 'PUT:READY' in put_response:
            print("✓ PUT works without flag!")
            ser.write(b'HELLO')
            ser.flush()
            done = ser.readline().decode().strip()
            print(f"Done: {done}")
        
        # Exit
        ser.write(b'EXIT\n')
        ser.readline()
        
    finally:
        ser.close()

if __name__ == "__main__":
    quick_test()
