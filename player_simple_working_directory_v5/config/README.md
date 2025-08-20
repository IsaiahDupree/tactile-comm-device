# Configuration Files

This directory contains the configuration files for the tactile communication device.

## Files Overview

### `config.csv`
**Purpose**: Maps hardware button indices to labels  
**Format**: `index,label`  
**Example**:
```csv
index,label
0,YES
1,SHIFT
2,K
3,A
```
**Usage**: Generated during calibration mode when you press buttons and assign labels

### `mode.cfg`
**Purpose**: Global system configuration  
**Format**: Key-value pairs with comments  
**Settings**:
- `PRIORITY`: `HUMAN_FIRST` or `GENERATED_FIRST` - determines which audio bank plays first
- `STRICT_PLAYLISTS`: `1` or `0` - enables/disables strict playlist enforcement (future feature)

### `audio_map.csv`
**Purpose**: Maps button labels to audio folder structure  
**Format**: `label,recFolder,recBase,recCount,ttsFolder,ttsBase,ttsCount,fallbackLabel`  
**Example**:
```csv
label,recFolder,recBase,recCount,ttsFolder,ttsBase,ttsCount,fallbackLabel
A,5,1,1,105,1,9,A
WATER,20,1,5,120,1,3,WATER
```
**Fields**:
- `label`: Button label (matches config.csv)
- `recFolder`: Folder number for recorded audio (human voice)
- `recBase`: Starting track number for recorded audio
- `recCount`: Number of recorded audio tracks
- `ttsFolder`: Folder number for TTS audio (computer voice)
- `ttsBase`: Starting track number for TTS audio
- `ttsCount`: Number of TTS audio tracks
- `fallbackLabel`: Fallback label for display

### `audio_index.csv`
**Purpose**: Text content mapping for console logging  
**Format**: `folder,track,text,bank`  
**Example**:
```csv
folder,track,text,bank
5,1,Alari [REC],REC
105,1,A,TTS
20,1,Water [REC],REC
```
**Fields**:
- `folder`: Audio folder number
- `track`: Track number within folder
- `text`: Human-readable text content
- `bank`: Audio bank type (`REC` for recorded, `TTS` for text-to-speech)

## Audio Folder Structure

The system expects audio files organized as:
```
/01/001.mp3, /01/002.mp3, ...    # Folder 1 audio files
/02/001.mp3, /02/002.mp3, ...    # Folder 2 audio files
...
/101/001.mp3, /101/002.mp3, ...  # TTS folders (100+ series)
/102/001.mp3, /102/002.mp3, ...
```

## Priority Mode System

- **HUMAN_FIRST**: Plays recorded audio first, falls back to TTS
- **GENERATED_FIRST**: Plays TTS audio first, falls back to recorded
- Toggle by triple-pressing the PERIOD button
- Mode is saved to EEPROM and persists across power cycles

## Configuration Workflow

1. **Initial Setup**: Place device in calibration mode
2. **Button Mapping**: Press each button and assign a label
3. **Save Configuration**: Use 'S' command to save `config.csv`
4. **Audio Mapping**: Ensure `audio_map.csv` matches your SD card structure
5. **Testing**: Use 'T' command to test all buttons

## File Locations on SD Card

All config files should be placed in the `/config/` directory on the SD card:
```
SD_CARD/
├── config/
│   ├── config.csv
│   ├── mode.cfg
│   ├── audio_map.csv
│   └── audio_index.csv
├── 01/
│   ├── 001.mp3
│   └── 002.mp3
├── 02/
│   └── 001.mp3
└── ...
```
