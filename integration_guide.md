# Integration Guide for Tactile Communicator Extensions

This guide explains how to integrate the new button simulation and SD file transfer features into your main Arduino sketch.

## Step 1: Add Required Functions to Your Main Sketch

Add these function calls at the appropriate locations in your main `player_simple_working_directory_v2.ino` file:

### Add to your `setup()` function:
```cpp
// Initialize simulation queue
simHead = 0;
simTail = 0;
```

### Add to your `loop()` function:
```cpp
// Process simulation queue
pumpSimQueue();
```

### Add to your serial command handling function:
```cpp
// In your function that processes serial commands, add this:
// Either insert this as a new command check, or call from your existing command handler
handleExtendedSerialCommand(line);
```

## Step 2: Add CRC32 Calculation Function

Add this function to your sketch if it doesn't exist already:

```cpp
// CRC32 calculation for file integrity verification
uint32_t calculate_crc32(const uint8_t* data, size_t length, uint32_t crc = 0) {
  crc = ~crc;
  for (size_t i = 0; i < length; i++) {
    crc ^= data[i];
    for (uint8_t j = 0; j < 8; j++) {
      crc = (crc >> 1) ^ (0xEDB88320 & -(crc & 1));
    }
  }
  return ~crc;
}
```

## Step 3: Implement FS_DATA Command with Buffer

Since the FS_DATA command needs to process binary data, you'll need to add this to your serial reading code:

```cpp
// Process binary data after FS_DATA command
void processDataChunk(uint16_t length) {
  uint8_t buffer[64]; // Adjust size based on your Arduino's memory constraints
  uint16_t remaining = length;
  uint16_t position = 0;
  
  // Read requested bytes in chunks
  while (remaining > 0) {
    uint16_t chunkSize = min(sizeof(buffer), remaining);
    uint16_t bytesRead = 0;
    
    // Read chunk with timeout
    unsigned long startTime = millis();
    while (bytesRead < chunkSize && (millis() - startTime) < 5000) {
      if (Serial.available()) {
        buffer[bytesRead++] = Serial.read();
      }
    }
    
    // Process chunk
    if (bytesRead > 0) {
      cmd_FS_DATA(bytesRead, buffer);
      remaining -= bytesRead;
      position += bytesRead;
    } else {
      // Timeout occurred
      Serial.println(F("ERR TIMEOUT"));
      return;
    }
  }
}
```

## Step 4: Update Serial Processing

Update your serial processing code to handle the binary data:

```cpp
// In your main loop or serial processing function
void processSerial() {
  if (Serial.available()) {
    String line = Serial.readStringUntil('\n');
    line.trim();
    
    // Handle regular commands
    if (line.startsWith("FS_DATA ")) {
      // Special handling for binary data
      uint16_t length = parseIntOr(line, 1, 0);
      if (length > 0) {
        Serial.println(F("READY")); // Signal ready to receive data
        processDataChunk(length);
      } else {
        Serial.println(F("ERR SIZE"));
      }
    } else {
      // Handle all other commands
      handleExtendedSerialCommand(line);
    }
  }
}
```

## Step 5: Copy the Extensions Code

Copy the entire contents of the `device_extensions.ino` file into your project. It's designed to work alongside your existing code.

## Testing the Integration

After integrating these changes, test with the following commands over serial:

1. Button simulation:
   ```
   SIM_KEY A 1 250
   ```

2. File transfer test (using a simple file):
   ```
   FS_BEGIN 1 100 0
   FS_PUT /config/test.txt 11 7AF4D0C
   FS_DATA 11
   Hello World
   FS_DONE
   FS_COMMIT
   ```

## Python Client for Testing

Create a Python client script for testing file transfers:

```python
import serial
import time
import os
import binascii

def crc32(data):
    return binascii.crc32(data) & 0xFFFFFFFF

def send_file(ser, src_path, dest_path):
    with open(src_path, 'rb') as f:
        data = f.read()
    
    # Calculate CRC32
    file_crc = crc32(data)
    file_size = len(data)
    
    print(f"Sending {src_path} -> {dest_path} ({file_size} bytes, CRC: {file_crc:08X})")
    
    # Start file transfer
    ser.write(f"FS_PUT {dest_path} {file_size} {file_crc:X}\n".encode())
    resp = ser.readline().decode().strip()
    print(f"Response: {resp}")
    
    if resp != "OK":
        print("Error starting file transfer")
        return False
    
    # Send data in chunks
    chunk_size = 64
    for i in range(0, file_size, chunk_size):
        chunk = data[i:i+chunk_size]
        ser.write(f"FS_DATA {len(chunk)}\n".encode())
        resp = ser.readline().decode().strip()
        if resp != "READY":
            print(f"Error: Device not ready for data chunk - {resp}")
            return False
        
        ser.write(chunk)
        resp = ser.readline().decode().strip()
        if resp != "OK":
            print(f"Error sending chunk: {resp}")
            return False
        
        print(f"Sent {min(i+chunk_size, file_size)}/{file_size} bytes")
    
    # Finalize file transfer
    ser.write(f"FS_DONE\n".encode())
    resp = ser.readline().decode().strip()
    print(f"File complete: {resp}")
    
    return resp == "OK"

# Usage example
if __name__ == "__main__":
    ser = serial.Serial('COM6', 115200, timeout=5)
    time.sleep(2)  # Wait for Arduino to reset
    
    # Begin transfer session
    ser.write(b"FS_BEGIN 1 0 0\n")
    print(f"Begin: {ser.readline().decode().strip()}")
    
    # Send a test file
    send_file(ser, "test.txt", "/config/test.txt")
    
    # Commit changes
    ser.write(b"FS_COMMIT\n")
    print(f"Commit: {ser.readline().decode().strip()}")
    
    # Reload config
    ser.write(b"CFG_RELOAD\n")
    print(f"Reload: {ser.readline().decode().strip()}")
    
    ser.close()
```
