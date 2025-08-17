# Tactile Device Manager

A professional desktop application for managing the Tactile Communication Device, providing seamless firmware updates, SD card synchronization, and device configuration management.

## Features

### 🔌 Device Connection
- Auto-detect Arduino devices (Uno R4 WiFi, Uno, Nano)
- Serial communication with real-time console
- Connection status monitoring

### 🔧 Firmware Management  
- Arduino CLI integration for firmware compilation and upload
- Support for multiple board types
- Real-time upload progress tracking
- Automatic board detection

### 💾 SD Card Management
- Browse and manage SD card files directly
- Sync configuration and audio files to device
- Backup device configuration
- File upload and organization tools

### ⚙️ Configuration Management
- Visual button mapping editor (buttons.csv)
- Priority mode configuration (Human First/Generated First)
- Playlist management with M3U support
- Real-time configuration reload

### 🧪 Device Testing
- Comprehensive self-test functionality
- Audio playback testing
- Device status monitoring
- Serial command interface

### 🚀 One-Click Update
- Complete device update workflow
- Automatic firmware flash + SD sync + self-test
- Progress tracking with visual feedback
- Error handling and rollback support

## Installation

### Prerequisites
- Node.js 16+ installed
- Arduino CLI installed and in PATH
- USB drivers for your Arduino device

### Setup
```bash
# Clone or extract the project
cd tactile-device-manager

# Install dependencies
npm install

# Start the application
npm start

# For development with DevTools
npm run dev
```

## Usage

### First Time Setup
1. **Connect Device**: Select your Arduino's serial port and click Connect
2. **Select SD Directory**: Choose your SD card or project directory
3. **Upload Firmware**: Use the Upload Firmware button to flash the latest code
4. **Sync Configuration**: Use Sync to Device to upload your configuration files

### Daily Workflow
1. **One-Click Update**: Use the big green button for complete device updates
2. **Configuration Changes**: Edit button mappings and playlists in the Configuration tab
3. **Testing**: Run self-tests to verify device functionality
4. **File Management**: Use the File Manager tab to organize audio files

### Serial Commands
The console supports all device serial commands:
- `GET_INFO` - Device information
- `L` - Load configuration
- `P` - Print status  
- `M` - Toggle priority mode
- `CFG_RELOAD` - Reload configuration
- `FS_*` - File system protocol commands

## File Structure

```
tactile-device-manager/
├── src/
│   ├── main.js           # Electron main process
│   └── renderer/
│       ├── index.html    # Main UI
│       ├── styles.css    # Application styling
│       └── renderer.js   # Frontend logic
├── package.json          # Dependencies and scripts
└── README.md            # This file
```

## SD Card Structure

The application expects this SD card structure:

```
SD_CARD/
├── config/
│   ├── buttons.csv       # Hardware button mapping
│   └── mode.cfg         # Priority mode settings
├── mappings/
│   └── playlists/
│       ├── A_human.m3u   # Human recordings for key A
│       ├── A_generated.m3u # Generated audio for key A
│       └── ...
├── audio/
│   ├── human/
│   │   ├── A/           # Human recordings for key A
│   │   └── ...
│   └── generated/
│       ├── A/           # Generated audio for key A
│       ├── SYSTEM/      # System announcements
│       └── ...
└── manifest.json        # Version and metadata
```

## Serial FS Protocol

The application implements the M4 Serial File System protocol for atomic SD card updates:

- **FS_BEGIN** - Start file transfer session
- **FS_PUT** - Specify target file
- **FS_DATA** - Send file data chunks with CRC32 verification
- **FS_DONE** - Complete file transfer
- **FS_COMMIT** - Atomically commit all changes
- **FS_ABORT** - Cancel transfer and rollback

## Development

### Building for Distribution
```bash
# Build for current platform
npm run build

# Build for specific platforms
npm run build:win
npm run build:mac
npm run build:linux
```

### Adding Features
1. **Main Process**: Add IPC handlers in `src/main.js`
2. **Renderer**: Add UI elements in `src/renderer/index.html`
3. **Styling**: Update `src/renderer/styles.css`
4. **Logic**: Implement functionality in `src/renderer/renderer.js`

### Testing
- Use `npm run dev` to run with DevTools enabled
- Test with actual Arduino hardware
- Verify file system operations on SD card
- Test error conditions and recovery

## Troubleshooting

### Connection Issues
- Ensure Arduino drivers are installed
- Check that no other applications are using the serial port
- Try different baud rates (115200 is recommended)
- Verify USB cable supports data transfer

### Upload Issues
- Ensure Arduino CLI is installed and in PATH
- Check board selection matches your hardware
- Verify sketch path is correct
- Try manual compilation first

### File System Issues
- Ensure SD card is properly formatted (FAT32)
- Check file permissions
- Verify directory structure matches expected format
- Test with a fresh SD card

## Support

For issues and feature requests, please check the project documentation or create an issue in the repository.

## License

This project is part of the Tactile Communication Device system. See the main project for licensing information.
