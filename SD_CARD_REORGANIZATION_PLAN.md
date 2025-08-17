# 🗂️ SD CARD REORGANIZATION PLAN - TWO-BANK SYSTEM

## 🎯 **OPTION A: NUMERIC RANGES (RECOMMENDED)**

Using **contiguous numeric ranges** within each folder for REC vs TTS banks.

---

## 📋 **REORGANIZATION STRATEGY**

### **🔢 NUMERIC CONVENTION:**
- **Three-digit zero-padded:** `001.mp3`, `002.mp3`, etc.
- **REC Bank:** Lower numbers (typically 001-00X)
- **TTS Bank:** Higher numbers (typically 00Y-00Z)
- **Clear separation** between banks for easy management

### **📁 FOLDER STRUCTURE:**
```
/01/  - Special buttons (YES, NO, WATER, HELP)
/05/  - Button A (Alari + TTS words)
/06/  - Button B (TTS only)
/07/  - Button C (TTS only)
/08/  - Button D (Daddy + TTS words)
...
/33/  - SHIFT help system + Priority announcements
```

---

## 🎵 **DETAILED REORGANIZATION PLAN**

### **✅ BUTTONS WITH PERSONAL RECORDINGS:**

#### **Button A (Folder 05) - Alari:**
```
CURRENT LAYOUT:
/05/001.mp3 - Alari [REC]
/05/002.mp3 - Angry [TTS]
/05/003.mp3 - Apple [TTS]
/05/004.mp3 - Awesome [TTS]
/05/005.mp3 - Azilect [TTS]
/05/006.mp3 - Azra [TTS]

REORGANIZED LAYOUT:
/05/001.mp3 - Alari [REC]          ← REC Bank: 1-1
/05/002.mp3 - Angry [TTS]          ← TTS Bank: 2-6
/05/003.mp3 - Apple [TTS]
/05/004.mp3 - Awesome [TTS]
/05/005.mp3 - Azilect [TTS]
/05/006.mp3 - Azra [TTS]

MAPPING: {"A", 5, /*rec*/1,1, /*tts*/2,5, "Alari"}
```

#### **Button D (Folder 08) - Daddy:**
```
CURRENT LAYOUT:
/08/001.mp3 - Daddy [REC]
/08/002.mp3 - Dance [TTS]
/08/003.mp3 - Doctor [TTS]
/08/004.mp3 - Door [TTS]
/08/005.mp3 - Down [TTS]
/08/006.mp3 - Drink [TTS]

REORGANIZED LAYOUT:
/08/001.mp3 - Daddy [REC]          ← REC Bank: 1-1
/08/002.mp3 - Dance [TTS]          ← TTS Bank: 2-6
/08/003.mp3 - Doctor [TTS]
/08/004.mp3 - Door [TTS]
/08/005.mp3 - Down [TTS]
/08/006.mp3 - Drink [TTS]

MAPPING: {"D", 8, /*rec*/1,1, /*tts*/2,5, "Daddy"}
```

#### **Button L (Folder 16) - I love you:**
```
CURRENT LAYOUT:
/16/001.mp3 - I love you [REC]
/16/002.mp3 - Light [TTS]
/16/003.mp3 - Listen [TTS]
/16/004.mp3 - Look [TTS]
/16/005.mp3 - Loud [TTS]
/16/006.mp3 - Love [TTS]

REORGANIZED LAYOUT:
/16/001.mp3 - I love you [REC]     ← REC Bank: 1-1
/16/002.mp3 - Light [TTS]          ← TTS Bank: 2-6
/16/003.mp3 - Listen [TTS]
/16/004.mp3 - Look [TTS]
/16/005.mp3 - Loud [TTS]
/16/006.mp3 - Love [TTS]

MAPPING: {"L", 16, /*rec*/1,1, /*tts*/2,5, "I love you"}
```

#### **Button N (Folder 18) - Nada/Nadowie/Noah:**
```
CURRENT LAYOUT:
/18/001.mp3 - Nada [REC]
/18/002.mp3 - Nadowie [REC]
/18/003.mp3 - Net [TTS]
/18/004.mp3 - No [TTS]
/18/005.mp3 - Noah [REC]

REORGANIZED LAYOUT:
/18/001.mp3 - Nada [REC]           ← REC Bank: 1-3
/18/002.mp3 - Nadowie [REC]
/18/003.mp3 - Noah [REC]
/18/004.mp3 - Net [TTS]            ← TTS Bank: 4-5
/18/005.mp3 - No [TTS]

MAPPING: {"N", 18, /*rec*/1,3, /*tts*/4,2, "Nada"}
```

#### **Button S (Folder 23) - Susu:**
```
CURRENT LAYOUT:
/23/001.mp3 - Sad [TTS]
/23/002.mp3 - Scarf [TTS]
/23/003.mp3 - Shoes [TTS]
/23/004.mp3 - Sinemet [TTS]
/23/005.mp3 - Sleep [TTS]
/23/006.mp3 - Socks [TTS]
/23/007.mp3 - Space [TTS]
/23/008.mp3 - Stop [TTS]
/23/009.mp3 - Sun [TTS]
/23/010.mp3 - Susu [REC]

REORGANIZED LAYOUT:
/23/001.mp3 - Susu [REC]           ← REC Bank: 1-1
/23/002.mp3 - Sad [TTS]            ← TTS Bank: 2-10
/23/003.mp3 - Scarf [TTS]
/23/004.mp3 - Shoes [TTS]
/23/005.mp3 - Sinemet [TTS]
/23/006.mp3 - Sleep [TTS]
/23/007.mp3 - Socks [TTS]
/23/008.mp3 - Space [TTS]
/23/009.mp3 - Stop [TTS]
/23/010.mp3 - Sun [TTS]

MAPPING: {"S", 23, /*rec*/1,1, /*tts*/2,9, "Sad"}
```

### **✅ TTS-ONLY BUTTONS (No Changes Needed):**

#### **Button B (Folder 06):**
```
CURRENT LAYOUT (Already Correct):
/06/001.mp3 - Bagel [TTS]          ← TTS Bank: 1-7
/06/002.mp3 - Bathroom [TTS]
/06/003.mp3 - Bed [TTS]
/06/004.mp3 - Blue [TTS]
/06/005.mp3 - Book [TTS]
/06/006.mp3 - Bottle [TTS]
/06/007.mp3 - Bread [TTS]

MAPPING: {"B", 6, /*rec*/0,0, /*tts*/1,7, "Bagel"}
```

---

## 🔧 **REORGANIZATION STEPS**

### **📂 STEP 1: BACKUP CURRENT SD CARD**
```bash
# Create backup of current SD card
xcopy E:\ C:\Users\Isaia\Documents\3D_Printing\Projects\Button\SD_BACKUP\ /E /H /C /I
```

### **📁 STEP 2: REORGANIZE FOLDERS WITH PERSONAL RECORDINGS**

#### **Folder 18 (Button N) - NEEDS REORGANIZATION:**
```bash
# Current: REC at 1,2,5 and TTS at 3,4
# Target:  REC at 1,2,3 and TTS at 4,5

# Rename files to temporary names
ren E:\18\003.mp3 003_temp.mp3  # Net [TTS]
ren E:\18\004.mp3 004_temp.mp3  # No [TTS]
ren E:\18\005.mp3 003.mp3       # Noah [REC] -> position 3

# Move TTS files to positions 4-5
ren E:\18\003_temp.mp3 004.mp3  # Net [TTS] -> position 4
ren E:\18\004_temp.mp3 005.mp3  # No [TTS] -> position 5
```

#### **Folder 23 (Button S) - NEEDS REORGANIZATION:**
```bash
# Current: TTS at 1-9, REC at 10
# Target:  REC at 1, TTS at 2-10

# Move Susu to position 1
ren E:\23\010.mp3 001_temp.mp3  # Susu [REC]

# Shift all TTS files up by 1 position (in reverse order)
ren E:\23\009.mp3 010.mp3  # Sun
ren E:\23\008.mp3 009.mp3  # Stop
ren E:\23\007.mp3 008.mp3  # Space
ren E:\23\006.mp3 007.mp3  # Socks
ren E:\23\005.mp3 006.mp3  # Sleep
ren E:\23\004.mp3 005.mp3  # Sinemet
ren E:\23\003.mp3 004.mp3  # Shoes
ren E:\23\002.mp3 003.mp3  # Scarf
ren E:\23\001.mp3 002.mp3  # Sad

# Move Susu to position 1
ren E:\23\001_temp.mp3 001.mp3  # Susu [REC]
```

### **📋 STEP 3: UPDATE ARDUINO MAPPINGS**
- Update the `audioMappings` array with correct bank ranges
- Test each button to ensure proper track selection

### **✅ STEP 4: VERIFY REORGANIZATION**
- Test HUMAN_FIRST mode plays personal recordings first
- Test GENERATED_FIRST mode plays TTS first
- Verify serial output shows correct bank selection

---

## 🎯 **EXPECTED RESULTS**

### **HUMAN_FIRST Mode:**
- **Button N Press 1:** `/18/001.mp3` (Nada - Personal)
- **Button S Press 1:** `/23/001.mp3` (Susu - Personal)
- **Button L Press 1:** `/16/001.mp3` (I love you - Personal)

### **GENERATED_FIRST Mode:**
- **Button N Press 1:** `/18/004.mp3` (Net - TTS)
- **Button S Press 1:** `/23/002.mp3` (Sad - TTS)
- **Button L Press 1:** `/16/002.mp3` (Light - TTS)

---

## 📊 **MANIFEST FILE (OPTIONAL)**

Create `E:\manifest.csv` for validation:
```csv
Label,Folder,RecBase,RecCount,TtsBase,TtsCount,Notes
A,5,1,1,2,5,Alari personal recording
B,6,0,0,1,7,TTS only
D,8,1,1,2,5,Daddy personal recording
L,16,1,1,2,5,I love you personal recording
N,18,1,3,4,2,Nada/Nadowie/Noah personal recordings
S,23,1,1,2,9,Susu personal recording
```

---

## 🚀 **IMPLEMENTATION PRIORITY**

1. **✅ IMMEDIATE:** Update Arduino mappings (already done)
2. **🔄 NEXT:** Reorganize Folder 18 (Button N)
3. **🔄 NEXT:** Reorganize Folder 23 (Button S)
4. **✅ TEST:** Verify priority mode works with real audio differences
5. **📋 OPTIONAL:** Create manifest file for validation

**This reorganization will make the priority mode system bulletproof and audibly functional!** 🎯
