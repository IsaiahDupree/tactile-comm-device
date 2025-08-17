# Tactile Device Manager

A beautiful, cross-platform desktop application for managing your Future-Proof Tactile Communication Device. Features a UI that perfectly matches your physical device layout with comprehensive device management capabilities.

![Tactile Device Manager](screenshot.png)

## Features

### 🎯 **Device-Matching UI**
- **Exact physical layout replication** - UI buttons match your device's button arrangement
- **Visual button status** - See human/generated audio counts at a glance
- **Interactive button selection** - Click any button to configure it
- **Real-time status indicators** - SD card and device connection status

### 🔧 **Complete Device Management**
- **Auto-detect devices** - Automatically finds Arduino-based tactile devices
- **SD card integration** - Direct access to device configuration and audio files
- **Hardware mapping** - Configure which physical pins map to which buttons
- **Component status monitoring** - Real-time device health and connectivity

### 🎵 **Advanced Audio Management**
- **Drag & drop audio files** - Easy audio file management
- **Strict human/generated separation** - Never mix recording types
- **Playlist management** - Precise control over playback order
- **Audio preview** - Listen to files before deployment
- **Batch operations** - Add/remove multiple files at once

### ⚙️ **Configuration Management**
- **Visual button mapping** - See exactly which GPIO pins control which buttons
- **Priority mode control** - Switch between Human First and Generated First
- **Real-time device communication** - Send commands and see responses
- **Configuration backup/restore** - Save and restore complete device setups

## Installation

### Prerequisites
- **Node.js 16+** - Download from [nodejs.org](https://nodejs.org/)
- **Windows 10/11, macOS 10.14+, or Linux** - Cross-platform support

### Quick Install
1. **Download** the latest release or clone this repository
2. **Run the installer**:
   ```bash
   # Windows
   install.bat
   
   # macOS/Linux
   chmod +x install.sh
   ./install.sh
   ```
3. **Launch the application**:
   ```bash
   npm start
   ```

### Manual Installation
```bash
# Install dependencies
npm install

# Run in development mode
npm run dev

# Build for distribution
npm run build-win    # Windows
npm run build-mac    # macOS
npm run build-linux  # Linux
```

## Usage Guide

### 1. **Connect Your Device**
- Connect your tactile communication device via USB
- Click **"Connect Device"** - the app will auto-detect Arduino devices
- Status indicator will turn green when connected

### 2. **Select SD Card**
- Insert your device's SD card into your computer
- Click **"Select SD Card"** and choose the SD card root directory
- The app will load your existing configuration automatically

### 3. **Configure Buttons**
- **Click any button** in the device layout to select it
- **Set hardware mapping**: Enter physical input (e.g., `pcf0:15`, `gpio:8`)
- **Assign button key**: Enter logical name (e.g., `Water`, `Emergency`)
- **Add audio files**: Use the "Add Human Recording" or "Add Generated Audio" buttons

### 4. **Manage Audio**
- **Preview audio**: Click the play button next to any audio file
- **Reorder tracks**: Drag and drop files in the playlist
- **Remove files**: Click the trash icon to delete audio files
- **Batch import**: Select multiple files at once

### 5. **Test and Deploy**
- **Test individual buttons**: Click "Test Button" to verify functionality
- **Change priority mode**: Use the dropdown to switch between Human/Generated first
- **Monitor console**: Watch real-time device communication
- **Save configuration**: All changes are automatically saved to SD card

## Interface Overview

### Main Layout
```
┌─────────────────────────────────────────────────────────────┐
│ Header: Status indicators, Connect buttons                  │
├─────────────────────┬───────────────────────────────────────┤
│ Device Layout       │ Button Configuration                  │
│                     │                                       │
│ ┌─ Are You? Yes ──┐ │ ┌─ Hardware Mapping ──────────────┐   │
│ │  No    Water    │ │ │ Input: pcf0:15                  │   │
│ └─────────────────┘ │ │ Key:   Water                    │   │
│                     │ └─────────────────────────────────┘   │
│ ┌─ A B C D E F G ─┐ │                                       │
│ │ H I J K L M N   │ │ ┌─ Human Recordings ──────────────┐   │
│ │ O P Q R S T U   │ │ │ 001.mp3 ▶ 🗑                   │   │
│ │ V W X Y Z - .   │ │ │ 002.mp3 ▶ 🗑                   │   │
│ └─────────────────┘ │ └─────────────────────────────────┘   │
│                     │                                       │
│                     │ ┌─ Generated Audio ───────────────┐   │
│                     │ │ 001.mp3 ▶ 🗑                   │   │
│                     │ └─────────────────────────────────┘   │
├─────────────────────┴───────────────────────────────────────┤
│ Console: Real-time device communication                     │
└─────────────────────────────────────────────────────────────┘
```

### Button Status Indicators
- **Green border**: Has human recordings
- **Blue border**: Has generated audio
- **Numbers**: Show count of human/generated files (e.g., "3/5" = 3 human, 5 generated)
- **Highlighted**: Currently selected for configuration

## File Structure

The app works with the Future-Proof SD card structure:
```
SD_CARD/
├── config/
│   ├── mode.cfg                 # Priority settings
│   └── buttons.csv              # Hardware mappings
├── mappings/playlists/
│   ├── A_human.m3u             # Human recordings for A
│   ├── A_generated.m3u         # Generated audio for A
│   └── ...
├── audio/
│   ├── human/A/001.mp3...      # Human recordings
│   ├── generated/A/001.mp3...  # Generated audio
│   └── generated/SYSTEM/       # System announcements
└── manifest.json               # App metadata
```

## Device Communication

### Supported Commands
- **`T`** - Test all buttons
- **`M`** - Toggle priority mode
- **`P`** - Print current mappings
- **`U`** - Verify audio files
- **`L`** - Load configuration
- **`S`** - Save configuration
- **`X`** - Stop audio playback
- **`+/-`** - Volume control
- **`1-9`** - Volume levels

### Serial Protocol
- **Baud rate**: 115200
- **Auto-detection**: Finds Arduino devices automatically
- **Real-time feedback**: See device responses in console
- **Command history**: Track all sent commands

## Hardware Support

### Supported Devices
- **Arduino Uno/Nano** with VS1053 codec
- **Up to 3x PCF8575** I2C expanders (52 buttons total)
- **Direct GPIO pins** for special functions

### Hardware Mapping Format
```csv
#INPUT,KEY
pcf0:00,A        # PCF8575 #0, pin 0 → letter A
pcf1:15,Water    # PCF8575 #1, pin 15 → Water button
pcf2:10,Emergency # PCF8575 #2, pin 10 → Emergency button
gpio:8,Home      # Direct GPIO pin 8 → Home button
```

## Troubleshooting

### Device Not Detected
- Check USB cable connection
- Ensure device drivers are installed
- Try different USB ports
- Restart the application

### SD Card Issues
- Ensure SD card is properly formatted (FAT32)
- Check file permissions
- Verify SD card is not write-protected
- Try ejecting and reinserting

### Audio Problems
- Verify audio files are in MP3 format
- Check file paths in playlist files
- Ensure SD card has sufficient space
- Test audio files in other players

### Configuration Issues
- Verify buttons.csv format is correct
- Check for duplicate hardware mappings
- Ensure all required directories exist
- Validate manifest.json syntax

## Development

### Building from Source
```bash
# Clone repository
git clone <repository-url>
cd TactileDeviceManager

# Install dependencies
npm install

# Run in development
npm run dev

# Build for production
npm run build
```

### Architecture
- **Electron** - Cross-platform desktop framework
- **Node.js** - Backend device communication
- **SerialPort** - Arduino communication
- **Modern CSS** - Beautiful, responsive UI
- **Vanilla JavaScript** - No heavy frameworks, fast performance

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

MIT License - see LICENSE file for details.

## Support

- **Issues**: Report bugs on GitHub
- **Documentation**: See project wiki
- **Community**: Join our Discord server
- **Email**: support@tactiledevice.com

---

**Transform your tactile communication device management with this powerful, beautiful desktop application!**
