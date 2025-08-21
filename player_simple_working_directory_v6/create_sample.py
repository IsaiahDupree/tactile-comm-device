#!/usr/bin/env python3
# Create a simple sample MP3 file for testing
import os

def create_sample_mp3():
    # Create a minimal MP3-like file
    data = b'ID3\x03\x00\x00\x00\x00\x00\x00'  # ID3v2.3 header (11 bytes)
    data += b'\xff\xfb\x90\x00' * 100  # MP3 frame headers (400 bytes)
    
    with open('sample.mp3', 'wb') as f:
        f.write(data)
    
    size = len(data)
    print(f"Created sample.mp3: {size} bytes")
    return size

if __name__ == "__main__":
    create_sample_mp3()
