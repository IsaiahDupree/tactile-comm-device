# Tactile Communication Device - Recorded Words Priority

## 🎵 PRIORITY SYSTEM IMPLEMENTED

Your personal recorded audio files now take priority over generated ones! The system has been organized to ensure recorded words play in their natural positions.

## 📍 Buttons with Recorded Words (PRIORITY)

### Special Buttons
- **AUX Button** → Press 4 times quickly: "Hello How are You" [RECORDED]

### Letters with Recorded Priority

#### Letter A (Press 1-5 times)
1. **Amer** [RECORDED] 🎙️
2. **Alari** [RECORDED] 🎙️
3. Apple [Generated]
4. Arabic Show [Generated]
5. **Amory** [RECORDED] 🎙️

#### Letter B (Press 1-5 times)
1. Bathroom [Generated]
2. **Bye** [RECORDED] 🎙️
3. Bed [Generated]
4. Breathe [Generated]
5. blanket [Generated]

#### Letter D (Press 1-4 times)
1. **Deen** [RECORDED] 🎙️
2. **Daddy** [RECORDED] 🎙️
3. Doctor [Generated]
4. Door [Generated]

#### Letter G (Press 1-2 times)
1. **Good Morning** [RECORDED] 🎙️
2. Go [Generated]

#### Letter K (Press 1-4 times)
1. **Kiyah** [RECORDED] 🎙️
2. **Kyan** [RECORDED] 🎙️
3. Kleenex [Generated]
4. Kaiser [Generated]

#### Letter L (Press 1-4 times)
1. **Lee** [RECORDED] 🎙️
2. **I love you** [RECORDED] 🎙️
3. light down [Generated]
4. light up [Generated]

#### Letter N (Press 1-3 times)
1. Nada [Generated]
2. **Nadowie** [RECORDED] 🎙️
3. **Noah** [RECORDED] 🎙️

#### Letter S (Press 1-3 times)
1. Scarf [Generated]
2. **Susu** [RECORDED] 🎙️
3. Sinemet [Generated]

#### Letter U (Press 1 time)
1. **Urgent Care** [RECORDED] 🎙️

#### Letter W (Press 1-4 times)
1. Water [Generated]
2. **Walker** [RECORDED] 🎙️
3. **wheelchair** [RECORDED] 🎙️
4. walk [Generated]

## 🎯 How It Works

### Button Pressing:
- **Single Press**: Plays first word (track 1)
- **Double Press** (quickly): Plays second word (track 2)
- **Triple Press** (quickly): Plays third word (track 3)
- And so on...

### Priority System:
- 🎙️ **Recorded words** play in their assigned track positions
- Generated words fill remaining positions
- Familiar voices for key family names and important words
- ElevenLabs voices for completeness

## 📁 Files Created

### SD Card Structure (`SD_Structure/` folder):
- **Folders 01-28**: Organized by DFPlayer Mini requirements
- **PRIORITY_MAPPING.txt**: Complete reference of all tracks
- Ready to copy to microSD card for device

### Arduino Code:
- **tactile_communicator_pcf8575.ino**: Updated with recorded word annotations
- Comments show which tracks are recorded vs. generated
- Proper track counts for multi-press functionality

## 🎵 Audio Quality

### Recorded Words (18 total):
- Personal, familiar voices
- Natural family pronunciations
- Priority placement in button sequences

### Generated Words (36 total):
- Slower ElevenLabs speech (improved from earlier)
- Consistent female voice
- Professional quality for medical/technical terms

## 🚀 Next Steps

1. **Copy SD Structure** to microSD card (FAT32 format)
2. **Upload Arduino code** to device
3. **Test recorded words** play correctly in their positions
4. **Verify multi-press** cycling works as expected

The system now prioritizes your personal recordings while maintaining complete communication coverage through generated audio. Recorded words will sound familiar and natural, making communication more personal and comfortable.
