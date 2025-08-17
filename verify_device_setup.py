#!/usr/bin/env python3
"""
Verify Tactile Communication Device Setup
Comprehensive verification of SD card structure, Arduino mappings, and file integrity
"""

import csv
import os
from pathlib import Path

# Configuration
SD_CARD_PATH = r"E:"
ARDUINO_FILE_PATH = r"C:\Users\Isaia\Documents\3D Printing\Projects\Button\Audio\tactile_communicator_vs1053\tactile_communicator_vs1053.ino"

def verify_sd_structure():
    """Verify SD card folder structure"""
    print("📁 VERIFYING SD CARD STRUCTURE")
    print("-" * 40)
    
    sd_path = Path(SD_CARD_PATH)
    if not sd_path.exists():
        print(f"❌ SD card not found at {SD_CARD_PATH}")
        return False
    
    # Check for required folders (01-26 for A-Z, plus specials)
    required_folders = list(range(1, 27)) + [32, 33, 34, 35]
    missing_folders = []
    
    for folder_num in required_folders:
        folder_path = sd_path / f"{folder_num:02d}"
        if not folder_path.exists():
            missing_folders.append(f"{folder_num:02d}")
    
    if missing_folders:
        print(f"❌ Missing folders: {', '.join(missing_folders)}")
        return False
    else:
        print(f"✅ All {len(required_folders)} required folders present")
    
    # Check for required files
    required_files = ["audio_index.csv", "DEVICE_REFERENCE.txt"]
    missing_files = []
    
    for file_name in required_files:
        file_path = sd_path / file_name
        if not file_path.exists():
            missing_files.append(file_name)
    
    if missing_files:
        print(f"❌ Missing files: {', '.join(missing_files)}")
        return False
    else:
        print(f"✅ All required files present")
    
    return True

def verify_audio_files():
    """Verify audio files match the index"""
    print("\n🎵 VERIFYING AUDIO FILES")
    print("-" * 40)
    
    csv_path = Path(SD_CARD_PATH) / "audio_index.csv"
    if not csv_path.exists():
        print("❌ audio_index.csv not found")
        return False
    
    total_files = 0
    present_files = 0
    missing_files = []
    
    with open(csv_path, 'r', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            folder = int(row['folder'])
            track = int(row['track'])
            text = row['text']
            bank = row['bank']
            
            file_path = Path(SD_CARD_PATH) / f"{folder:02d}" / f"{track:03d}.mp3"
            total_files += 1
            
            if file_path.exists():
                present_files += 1
            else:
                missing_files.append(f"/{folder:02d}/{track:03d}.mp3 - '{text}' ({bank})")
    
    print(f"📊 Audio File Status: {present_files}/{total_files} present")
    
    if missing_files:
        print(f"❌ {len(missing_files)} missing files:")
        for missing in missing_files[:10]:  # Show first 10
            print(f"   {missing}")
        if len(missing_files) > 10:
            print(f"   ... and {len(missing_files) - 10} more")
        return False
    else:
        print("✅ All audio files present")
        return True

def verify_arduino_mappings():
    """Verify Arduino mappings are correctly updated"""
    print("\n⚙️ VERIFYING ARDUINO MAPPINGS")
    print("-" * 40)
    
    arduino_path = Path(ARDUINO_FILE_PATH)
    if not arduino_path.exists():
        print(f"❌ Arduino file not found at {ARDUINO_FILE_PATH}")
        return False
    
    with open(arduino_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Check for key indicators of updated mappings
    indicators = [
        'AudioMapping audioMappings[] = {',
        '{"A", /*recFolder*/1,/*recBase*/1,/*recCount*/3',  # A button with 3 recorded files
        '{"D", /*recFolder*/4,/*recBase*/1,/*recCount*/1',  # D button with 1 recorded file
        '{"Z", /*recFolder*/26,/*recBase*/1,/*recCount*/0', # Z button with no recorded files
        'const uint8_t AUDIO_MAPPINGS_COUNT'
    ]
    
    missing_indicators = []
    for indicator in indicators:
        if indicator not in content:
            missing_indicators.append(indicator)
    
    if missing_indicators:
        print("❌ Arduino mappings not properly updated")
        for missing in missing_indicators:
            print(f"   Missing: {missing}")
        return False
    else:
        print("✅ Arduino mappings correctly updated")
        return True

def analyze_priority_system():
    """Analyze the priority system setup"""
    print("\n🎯 ANALYZING PRIORITY SYSTEM")
    print("-" * 40)
    
    csv_path = Path(SD_CARD_PATH) / "audio_index.csv"
    if not csv_path.exists():
        print("❌ audio_index.csv not found")
        return False
    
    rec_count = 0
    tts_count = 0
    buttons_with_rec = set()
    
    with open(csv_path, 'r', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            folder = int(row['folder'])
            bank = row['bank']
            
            if bank == 'REC':
                rec_count += 1
                # Convert folder number to letter (1=A, 2=B, etc.)
                if 1 <= folder <= 26:
                    letter = chr(ord('A') + folder - 1)
                    buttons_with_rec.add(letter)
            elif bank == 'TTS':
                tts_count += 1
    
    print(f"📊 Priority System Analysis:")
    print(f"   🎤 Recorded files: {rec_count}")
    print(f"   🤖 TTS files: {tts_count}")
    print(f"   📝 Total files: {rec_count + tts_count}")
    print(f"   🔤 Buttons with recordings: {len(buttons_with_rec)} ({', '.join(sorted(buttons_with_rec))})")
    
    # Show which buttons have recordings
    if buttons_with_rec:
        print(f"\n🎤 Buttons with personal recordings:")
        for letter in sorted(buttons_with_rec):
            print(f"   {letter} - Personal audio available")
    
    return True

def generate_final_report():
    """Generate final setup report"""
    print("\n📋 GENERATING FINAL REPORT")
    print("-" * 40)
    
    report_path = Path(SD_CARD_PATH) / "DEVICE_SETUP_VERIFICATION.txt"
    
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write("TACTILE COMMUNICATION DEVICE - SETUP VERIFICATION REPORT\n")
        f.write("=" * 70 + "\n\n")
        f.write(f"Verification Date: {Path(__file__).stat().st_mtime}\n")
        f.write(f"SD Card Path: {SD_CARD_PATH}\n")
        f.write(f"Arduino File: {ARDUINO_FILE_PATH}\n\n")
        
        # SD Structure
        f.write("SD CARD STRUCTURE:\n")
        f.write("-" * 20 + "\n")
        sd_ok = verify_sd_structure_silent()
        f.write(f"Status: {'✅ PASS' if sd_ok else '❌ FAIL'}\n\n")
        
        # Audio Files
        f.write("AUDIO FILES:\n")
        f.write("-" * 20 + "\n")
        audio_ok = verify_audio_files_silent()
        f.write(f"Status: {'✅ PASS' if audio_ok else '❌ FAIL'}\n\n")
        
        # Arduino Mappings
        f.write("ARDUINO MAPPINGS:\n")
        f.write("-" * 20 + "\n")
        arduino_ok = verify_arduino_mappings_silent()
        f.write(f"Status: {'✅ PASS' if arduino_ok else '❌ FAIL'}\n\n")
        
        # Overall Status
        overall_ok = sd_ok and audio_ok and arduino_ok
        f.write("OVERALL STATUS:\n")
        f.write("-" * 20 + "\n")
        f.write(f"Device Ready: {'✅ YES' if overall_ok else '❌ NO'}\n\n")
        
        if overall_ok:
            f.write("🎉 Your tactile communication device is fully configured and ready to use!\n")
        else:
            f.write("⚠️ Some issues need to be resolved before the device is ready.\n")
        
        f.write("\n" + "=" * 70 + "\n")
        f.write("End of Report\n")
    
    print(f"📝 Report saved to: {report_path}")

def verify_sd_structure_silent():
    """Silent version of SD structure verification"""
    sd_path = Path(SD_CARD_PATH)
    if not sd_path.exists():
        return False
    
    required_folders = list(range(1, 27)) + [32, 33, 34, 35]
    for folder_num in required_folders:
        if not (sd_path / f"{folder_num:02d}").exists():
            return False
    
    required_files = ["audio_index.csv", "DEVICE_REFERENCE.txt"]
    for file_name in required_files:
        if not (sd_path / file_name).exists():
            return False
    
    return True

def verify_audio_files_silent():
    """Silent version of audio files verification"""
    csv_path = Path(SD_CARD_PATH) / "audio_index.csv"
    if not csv_path.exists():
        return False
    
    with open(csv_path, 'r', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            folder = int(row['folder'])
            track = int(row['track'])
            file_path = Path(SD_CARD_PATH) / f"{folder:02d}" / f"{track:03d}.mp3"
            if not file_path.exists():
                return False
    
    return True

def verify_arduino_mappings_silent():
    """Silent version of Arduino mappings verification"""
    arduino_path = Path(ARDUINO_FILE_PATH)
    if not arduino_path.exists():
        return False
    
    with open(arduino_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    indicators = [
        'AudioMapping audioMappings[] = {',
        '{"A", /*recFolder*/1,/*recBase*/1,/*recCount*/3',
        'const uint8_t AUDIO_MAPPINGS_COUNT'
    ]
    
    return all(indicator in content for indicator in indicators)

def main():
    """Main verification function"""
    print("🔍 TACTILE COMMUNICATION DEVICE - SETUP VERIFICATION")
    print("=" * 70)
    
    try:
        # Run all verifications
        sd_ok = verify_sd_structure()
        audio_ok = verify_audio_files()
        arduino_ok = verify_arduino_mappings()
        analyze_priority_system()
        
        # Generate final report
        generate_final_report()
        
        # Final status
        print("\n" + "=" * 70)
        if sd_ok and audio_ok and arduino_ok:
            print("🎉 VERIFICATION COMPLETE - DEVICE READY!")
            print("Your tactile communication device is fully configured.")
            print("\nNext steps:")
            print("1. Upload the Arduino code to your device")
            print("2. Test all button mappings")
            print("3. Use triple-press on Period button to switch priority modes")
        else:
            print("⚠️ VERIFICATION INCOMPLETE - ISSUES FOUND")
            print("Please resolve the issues above before using the device.")
        
        print("=" * 70)
        
    except Exception as e:
        print(f"❌ Verification failed with error: {e}")
        raise

if __name__ == "__main__":
    main()
