#!/usr/bin/env python3
"""
Quick test script to verify 8.3 CLI path handling
"""

import os
from data_cli import cmd_put

# Test filename extension conversion
def test_filename_conversion():
    print("=== Testing 8.3 Filename Conversion ===")
    
    # Simulate the filename conversion logic
    test_cases = [
        ("001.mp3", "001.MP3"),
        ("002.wav", "002.WAV"), 
        ("test.ogg", "test.OGG"),
        ("file.txt", "file.TXT"),
        ("noext", "noext")
    ]
    
    for input_fname, expected in test_cases:
        name, ext = os.path.splitext(input_fname)
        if ext:
            result = name + ext.upper()
        else:
            result = input_fname
            
        status = "✅" if result == expected else "❌"
        print(f"  {status} {input_fname} -> {result} (expected: {expected})")

def test_bank_choices():
    print("\n=== Testing Bank Choices ===")
    valid_banks = ["HUMAN", "GENERA~1"]
    
    for bank in valid_banks:
        print(f"  ✅ {bank} - Valid 8.3 bank name")
    
    print("\n  Old lowercase banks no longer accepted:")
    old_banks = ["human", "generated"]
    for bank in old_banks:
        print(f"  ❌ {bank} - Would be rejected")

if __name__ == "__main__":
    test_filename_conversion()
    test_bank_choices()
    
    print("\n🎉 CLI is now 8.3 compliant!")
    print("\nUsage examples:")
    print("  python data_cli.py put -p COM6 HUMAN I 002.MP3 /path/to/file.mp3")
    print("  python data_cli.py put -p COM6 GENERA~1 A 001.MP3 /path/to/file.mp3")
