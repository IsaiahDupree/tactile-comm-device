#!/usr/bin/env python3
"""
Copy YES/NO variants from v3 to v5 and update wordlist
"""

import shutil
import json
from pathlib import Path

def copy_variants():
    # Source and destination paths
    v3_yes = Path("player_simple_working_directory_v3/SD_CARD_STRUCTURE/audio/generated/YES")
    v3_no = Path("player_simple_working_directory_v3/SD_CARD_STRUCTURE/audio/generated/NO")
    
    v5_yes = Path("player_simple_working_directory_v5/SD_CARD_STRUCTURE/audio/GENERA~1/YES")
    v5_no = Path("player_simple_working_directory_v5/SD_CARD_STRUCTURE/audio/GENERA~1/NO")
    
    # Copy YES variants (002.mp3 = Correct, 003.mp3 = Right)
    if (v3_yes / "002.mp3").exists():
        shutil.copy2(v3_yes / "002.mp3", v5_yes / "002.mp3")
        print("✓ Copied YES/002.mp3 (Correct)")
        
    if (v3_yes / "003.mp3").exists():
        shutil.copy2(v3_yes / "003.mp3", v5_yes / "003.mp3")
        print("✓ Copied YES/003.mp3 (Right)")
    
    # Copy NO variants (002.mp3 = Wrong, 003.mp3 = Incorrect)
    if (v3_no / "002.mp3").exists():
        shutil.copy2(v3_no / "002.mp3", v5_no / "002.mp3")
        print("✓ Copied NO/002.mp3 (Wrong)")
        
    if (v3_no / "003.mp3").exists():
        shutil.copy2(v3_no / "003.mp3", v5_no / "003.mp3")
        print("✓ Copied NO/003.mp3 (Incorrect)")
    
    # Create sidecar text files
    (v5_yes / "002.txt").write_text("# 002.mp3 should contain: Correct")
    (v5_yes / "003.txt").write_text("# 003.mp3 should contain: Right")
    (v5_no / "002.txt").write_text("# 002.mp3 should contain: Wrong")
    (v5_no / "003.txt").write_text("# 003.mp3 should contain: Incorrect")
    
    print("✓ Created sidecar text files")

def update_wordlist():
    # Update wordlist to include variants
    try:
        with open("wordlist", "r") as f:
            data = json.load(f)
        
        # Update YES to include variants
        if "phrases" in data and "YES" in data["phrases"]:
            data["phrases"]["YES"]["generated"] = ["Yes", "Correct", "Right"]
            print("✓ Updated YES variants in wordlist")
        
        # Update NO to include variants  
        if "phrases" in data and "NO" in data["phrases"]:
            data["phrases"]["NO"]["generated"] = ["No", "Wrong", "Incorrect"]
            print("✓ Updated NO variants in wordlist")
        
        # Write back to wordlist
        with open("wordlist", "w") as f:
            json.dump(data, f, indent=2)
            
        print("✓ Saved updated wordlist")
        
    except Exception as e:
        print(f"✗ Error updating wordlist: {e}")

if __name__ == "__main__":
    print("Copying YES/NO variants from v3 to v5...")
    copy_variants()
    print("\nUpdating wordlist...")
    update_wordlist()
    print("\n✓ Done! YES/NO now have 3 variants each:")
    print("  YES: Press 1=Yes, 2=Correct, 3=Right")
    print("  NO:  Press 1=No,  2=Wrong,   3=Incorrect")
