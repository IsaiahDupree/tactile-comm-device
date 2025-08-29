#!/usr/bin/env python3
"""
Comprehensive test suite for data mode functionality
Tests all use cases: PUT/GET/DEL/LS/EXIT with various scenarios
"""

import serial
import time
import os
import tempfile
import hashlib
from serial.tools import list_ports

class DataModeTest:
    def __init__(self, port='COM5', baud=115200):
        self.port = port
        self.baud = baud
        self.ser = None
        self.test_files = []
        
    def connect(self):
        """Connect to device and enter data mode"""
        print(f"🔌 Connecting to {self.port}...")
        self.ser = serial.Serial(self.port, self.baud, timeout=5)
        time.sleep(0.5)
        self.ser.reset_input_buffer()
        
        # Handshake
        print("🤝 Sending handshake...")
        self.ser.write(b"^DATA? v1\n")
        response = self.ser.readline().decode('utf-8', errors='ignore').strip()
        
        if "DATA:OK v1" not in response:
            raise Exception(f"Handshake failed: {response}")
        print("✅ Data mode entered successfully")
        
    def disconnect(self):
        """Exit data mode and close connection"""
        if self.ser:
            print("🚪 Exiting data mode...")
            self.ser.write(b"EXIT\n")
            response = self.ser.readline().decode('utf-8', errors='ignore').strip()
            print(f"Exit response: {response}")
            self.ser.close()
            
    def create_test_file(self, content, filename=None):
        """Create a temporary test file"""
        if filename:
            filepath = os.path.join(tempfile.gettempdir(), filename)
            with open(filepath, 'wb') as f:
                f.write(content)
        else:
            fd, filepath = tempfile.mkstemp(suffix='.mp3')
            os.write(fd, content)
            os.close(fd)
        
        self.test_files.append(filepath)
        return filepath
        
    def cleanup_test_files(self):
        """Remove temporary test files"""
        for filepath in self.test_files:
            try:
                os.remove(filepath)
            except:
                pass
        self.test_files = []
        
    def test_ls_command(self):
        """Test LS command with various directories"""
        print("\n📋 Testing LS command...")
        
        test_cases = [
            ("human", "A"),
            ("GENERA~1", "SHIFT"), 
            ("human", "NONEXISTENT"),  # Should return LS:NODIR
        ]
        
        for bank, key in test_cases:
            print(f"  Testing LS {bank} {key}")
            self.ser.write(f"LS {bank} {key}\n".encode())
            
            files = []
            while True:
                line = self.ser.readline().decode('utf-8', errors='ignore').strip()
                if "LS:DONE" in line:
                    print(f"    Found {len(files)} files")
                    break
                elif "LS:NODIR" in line:
                    print(f"    Directory not found (expected)")
                    break
                elif line and not line.startswith('['):
                    files.append(line)
                    print(f"    {line}")
                    
    def test_put_get_cycle(self):
        """Test PUT then GET to verify file integrity"""
        print("\n📤📥 Testing PUT/GET cycle...")
        
        # Create test content
        test_content = b"This is test audio data for PUT/GET verification " * 100
        test_file = self.create_test_file(test_content, "test_put_get.mp3")
        
        # Calculate hash for verification
        original_hash = hashlib.md5(test_content).hexdigest()
        
        # PUT file
        print("  Uploading test file...")
        file_size = len(test_content)
        self.ser.write(f"PUT human A test_cycle.mp3 {file_size}\n".encode())
        
        response = self.ser.readline().decode('utf-8', errors='ignore').strip()
        if "PUT:READY" not in response:
            raise Exception(f"PUT failed: {response}")
            
        # Send file data
        self.ser.write(test_content)
        
        # Wait for completion
        response = self.ser.readline().decode('utf-8', errors='ignore').strip()
        if "PUT:DONE" not in response:
            raise Exception(f"PUT completion failed: {response}")
        print("  ✅ Upload successful")
        
        # GET file back
        print("  Downloading file for verification...")
        self.ser.write(b"GET human A test_cycle.mp3\n")
        
        header = self.ser.readline().decode('utf-8', errors='ignore').strip()
        if not header.startswith("GET:SIZE"):
            raise Exception(f"GET failed: {header}")
            
        # Parse size
        size = int(header.split()[1])
        print(f"  File size: {size} bytes")
        
        # Read file data
        downloaded_data = self.ser.read(size)
        downloaded_hash = hashlib.md5(downloaded_data).hexdigest()
        
        if original_hash == downloaded_hash:
            print("  ✅ File integrity verified")
        else:
            raise Exception("File corruption detected!")
            
    def test_delete_operations(self):
        """Test DEL command"""
        print("\n🗑️ Testing DELETE operations...")
        
        # First create a file to delete
        test_content = b"File to be deleted"
        self.ser.write(f"PUT human A delete_test.mp3 {len(test_content)}\n".encode())
        
        response = self.ser.readline().decode('utf-8', errors='ignore').strip()
        if "PUT:READY" in response:
            self.ser.write(test_content)
            response = self.ser.readline().decode('utf-8', errors='ignore').strip()
            if "PUT:DONE" in response:
                print("  Test file created for deletion")
                
                # Now delete it
                self.ser.write(b"DEL human A delete_test.mp3\n")
                response = self.ser.readline().decode('utf-8', errors='ignore').strip()
                
                if "DEL:OK" in response:
                    print("  ✅ File deleted successfully")
                else:
                    print(f"  ❌ Delete failed: {response}")
                    
    def test_error_conditions(self):
        """Test various error conditions"""
        print("\n⚠️ Testing error conditions...")
        
        # Test invalid commands
        test_cases = [
            ("INVALID", "ERR:UNKNOWN"),
            ("GET nonexistent file", "GET:NOK"),
            ("DEL human A nonexistent.mp3", "DEL:NOK"),
        ]
        
        for command, expected in test_cases:
            print(f"  Testing: {command}")
            self.ser.write(f"{command}\n".encode())
            response = self.ser.readline().decode('utf-8', errors='ignore').strip()
            
            if expected in response:
                print(f"    ✅ Expected error: {response}")
            else:
                print(f"    ❌ Unexpected response: {response}")
                
    def test_large_file_transfer(self):
        """Test transfer of larger files"""
        print("\n📦 Testing large file transfer...")
        
        # Create 50KB test file
        large_content = b"Large file test data " * 2500  # ~50KB
        
        print(f"  Uploading {len(large_content)} byte file...")
        self.ser.write(f"PUT human A large_test.mp3 {len(large_content)}\n".encode())
        
        response = self.ser.readline().decode('utf-8', errors='ignore').strip()
        if "PUT:READY" in response:
            # Send in chunks to avoid buffer overflow
            chunk_size = 512
            for i in range(0, len(large_content), chunk_size):
                chunk = large_content[i:i+chunk_size]
                self.ser.write(chunk)
                time.sleep(0.01)  # Small delay
                
            response = self.ser.readline().decode('utf-8', errors='ignore').strip()
            if "PUT:DONE" in response:
                print("  ✅ Large file upload successful")
            else:
                print(f"  ❌ Large file upload failed: {response}")
                
    def run_all_tests(self):
        """Run complete test suite"""
        print("🧪 Starting Data Mode Test Suite")
        print("=" * 50)
        
        try:
            self.connect()
            
            # Run all tests
            self.test_ls_command()
            self.test_put_get_cycle()
            self.test_delete_operations()
            self.test_error_conditions()
            self.test_large_file_transfer()
            
            print("\n" + "=" * 50)
            print("✅ All tests completed successfully!")
            
        except Exception as e:
            print(f"\n❌ Test failed: {e}")
            
        finally:
            self.disconnect()
            self.cleanup_test_files()

if __name__ == "__main__":
    # List available ports
    print("Available ports:")
    for port in list_ports.comports():
        print(f"  {port.device} - {port.description}")
    
    # Run tests (adjust port as needed)
    tester = DataModeTest('COM5')
    tester.run_all_tests()
