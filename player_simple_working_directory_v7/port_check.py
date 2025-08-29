import serial.tools.list_ports
import serial
import time

def check_ports():
    print("Available serial ports:")
    ports = serial.tools.list_ports.comports()
    for port in ports:
        print(f"  {port.device}: {port.description}")
    
    if not ports:
        print("No serial ports found!")
        return False
    
    # Try COM5 specifically
    try:
        print("\nTesting COM5...")
        ser = serial.Serial('COM5', 115200, timeout=0.5)
        print("COM5 opened successfully")
        
        # Quick test - just try to read any existing data
        time.sleep(1)
        data = ser.read_all()
        if data:
            print(f"Data available: {data[:50]}...")
        else:
            print("No immediate data")
            
        ser.close()
        return True
        
    except serial.SerialException as e:
        print(f"Failed to open COM5: {e}")
        return False
    except Exception as e:
        print(f"Error: {e}")
        return False

if __name__ == "__main__":
    check_ports()
