import serial
import time

print('Testing handshake with uploaded firmware...')
ser = serial.Serial('COM5', 115200, timeout=3)
time.sleep(2)
ser.reset_input_buffer()

# Send handshake
ser.write(b'^DATA? v1\n')
time.sleep(0.5)

# Read response
response = ser.read_all().decode().strip()
print(f'Response: "{response}"')

if 'DATA:OK' in response:
    print('✓ Handshake successful!')
    # Exit data mode
    ser.write(b'EXIT\n')
    time.sleep(0.5)
    exit_response = ser.read_all().decode().strip()
    print(f'Exit response: "{exit_response}"')
else:
    print('✗ Handshake failed')

ser.close()
