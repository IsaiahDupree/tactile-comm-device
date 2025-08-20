# M4 & M5 Implementation Roadmap

## 🎯 PROJECT STATUS OVERVIEW

### ✅ COMPLETED MILESTONES

**M1 - SD Config + Routing (COMPLETE)**
- Hardware-agnostic button mapping via `/config/buttons.csv`
- Support for PCF8575 I2C expanders and GPIO pins
- Strict CSV parser with PCF and GPIO notation
- Dynamic memory allocation for button mappings
- Backward compatibility with legacy CONFIG.CSV

**M2 - Playlist Engine (COMPLETE)**
- M3U playlist parsing from `/mappings/playlists/{KEY}_{bank}.m3u`
- Playlist caching system (max 32 cached keys)
- Priority mode integration (HUMAN_FIRST vs GENERATED_FIRST)
- Multi-press support with cursor advancement
- Runtime playlist reload via serial command `R/r`

**M4 - Update Path (ARCHITECTURE COMPLETE)**
- Serial FS protocol design and implementation
- Atomic update mechanism with staging directories
- CRC32 verification for file integrity
- Maintenance mode for conflict prevention
- Desktop app integration points prepared

### 🔄 CURRENT MILESTONE

**M5 - Desktop App Integration (READY TO START)**

## 📋 M4 IMPLEMENTATION DETAILS

### Serial FS Protocol Commands
```
FS_BEGIN <files> <totalBytes> <manifestCrc32>  # Initialize update session
FS_PUT <path> <size> <crc32>                   # Prepare file for transfer  
FS_DATA <n> + binary data                      # Transfer file chunks
FS_DONE                                        # Complete current file
FS_COMMIT                                      # Atomically commit staged files
FS_ABORT                                       # Abort and cleanup staging
CFG_RELOAD                                     # Reload config without reboot
GET_INFO                                       # Get device information
```

### Safety Features Implemented
- **CRC32 Verification**: Every file transfer verified with lookup table
- **Chunked Transfer**: 512-byte chunks with timeout protection  
- **Atomic Operations**: All-or-nothing commit mechanism
- **Error Recovery**: Automatic cleanup on failure
- **Power-Loss Safety**: Staging directory approach prevents corruption
- **Maintenance Mode**: Prevents button conflicts during updates

### Integration Points Ready
- FS protocol initialization in `setup()`
- Main loop integration with command priority
- Configuration reload without device reboot
- Compatible with existing M1/M2 systems

## 🚀 M5 DESKTOP APP REQUIREMENTS

### Core Components Needed

#### 1. Arduino CLI Integration
```
Features Required:
├── Auto-detect Arduino boards (Uno R4 WiFi, etc.)
├── Compile firmware with progress tracking
├── Upload firmware with log streaming
└── Handle compilation errors gracefully
```

#### 2. Serial FS Protocol Client
```
Client Implementation:
├── Serial port communication
├── FS protocol command generation
├── File chunking and CRC calculation
├── Progress tracking and resume capability
├── Error handling and retry logic
└── Atomic operation management
```

#### 3. Self-Test Module
```
Test Capabilities:
├── Play known test audio clip
├── Verify device audio response
├── Check button functionality
├── Validate configuration loading
└── Generate pass/fail reports
```

#### 4. One-Click Update Workflow
```
Workflow Steps:
1. Detect and validate device connection
2. Flash latest firmware (with progress)
3. Sync SD card content (with resume)
4. Run comprehensive self-test
5. Report success/failure with details
```

### Technology Stack Recommendations

#### Option A: Tauri (Rust + Web Frontend)
**Pros:**
- Small binary size and fast performance
- Native system integration
- Cross-platform (Windows, Mac, Linux)
- Modern web UI with React/Vue/Svelte

**Cons:**
- Rust learning curve for team
- Smaller ecosystem than Electron

#### Option B: Electron (Node.js + Web Frontend)
**Pros:**
- Large ecosystem and community
- JavaScript/TypeScript familiarity
- Rich serial port libraries (serialport)
- Easy Arduino CLI integration

**Cons:**
- Larger binary size
- Higher memory usage

#### Recommended: **Electron** for rapid development

### Desktop App Architecture
```
Desktop Application Structure:
├── Main Process (Node.js)
│   ├── Arduino CLI wrapper
│   ├── Serial FS protocol client
│   ├── File system operations
│   └── Device management
├── Renderer Process (Web UI)
│   ├── Device selection interface
│   ├── Progress tracking displays
│   ├── Error reporting dialogs
│   └── Settings management
└── Shared Libraries
    ├── Protocol definitions
    ├── CRC32 calculations
    └── Utility functions
```

## 🛠️ M5 DEVELOPMENT PHASES

### Phase 1: Foundation (Week 1-2)
- [ ] Set up Electron project structure
- [ ] Implement Arduino CLI wrapper
- [ ] Create basic device detection
- [ ] Design main UI layout
- [ ] Test firmware compilation and upload

### Phase 2: Serial Communication (Week 3-4)
- [ ] Implement serial port management
- [ ] Create FS protocol client
- [ ] Add file transfer with CRC verification
- [ ] Implement progress tracking
- [ ] Test basic file operations

### Phase 3: Advanced Features (Week 5-6)
- [ ] Add transfer resume capability
- [ ] Implement self-test module
- [ ] Create comprehensive error handling
- [ ] Add logging and debugging features
- [ ] Test error recovery scenarios

### Phase 4: Integration & Polish (Week 7-8)
- [ ] Implement one-click update workflow
- [ ] Add user-friendly progress indicators
- [ ] Create comprehensive error reporting
- [ ] Implement settings and preferences
- [ ] Conduct end-to-end testing

### Phase 5: Testing & Deployment (Week 9-10)
- [ ] Comprehensive integration testing
- [ ] User acceptance testing
- [ ] Performance optimization
- [ ] Create installation packages
- [ ] Documentation and user guides

## 📊 TECHNICAL SPECIFICATIONS

### Device Requirements
- **Arduino Uno R4 WiFi** (primary target)
- **VS1053 Audio Codec** with SD card
- **PCF8575 I2C Expanders** (up to 3 units)
- **SD Card** formatted FAT32
- **Serial Connection** via USB (115200 baud recommended)

### Desktop Requirements
- **Windows 10/11** (primary), macOS, Linux support
- **Arduino CLI** bundled or auto-installed
- **Serial Port Access** (USB drivers)
- **Node.js Runtime** (bundled with Electron)
- **Minimum 4GB RAM**, 1GB storage

### Performance Targets
- **Firmware Flash**: < 30 seconds
- **SD Sync**: < 2 minutes for typical content
- **Self-Test**: < 10 seconds
- **Total Update Time**: < 3 minutes end-to-end

## 🔍 TESTING STRATEGY

### Unit Testing
- [ ] FS protocol command generation
- [ ] CRC32 calculation accuracy
- [ ] File chunking and reassembly
- [ ] Error handling edge cases

### Integration Testing  
- [ ] Arduino CLI integration
- [ ] Serial communication reliability
- [ ] End-to-end update workflow
- [ ] Error recovery scenarios

### User Acceptance Testing
- [ ] One-click operation usability
- [ ] Error message clarity
- [ ] Progress indication accuracy
- [ ] Overall user experience

## 📈 SUCCESS METRICS

### Technical Metrics
- **Update Success Rate**: > 99%
- **Transfer Speed**: > 50KB/s average
- **Error Recovery**: 100% of recoverable errors
- **User Completion Rate**: > 95%

### User Experience Metrics
- **Time to Complete Update**: < 3 minutes
- **User Satisfaction**: > 4.5/5 rating
- **Support Ticket Reduction**: > 80%
- **Adoption Rate**: > 90% of users

## 🎯 IMMEDIATE NEXT STEPS

1. **Choose Technology Stack**: Finalize Electron vs Tauri decision
2. **Set Up Development Environment**: Project structure, dependencies
3. **Create MVP**: Basic device detection and firmware flashing
4. **Implement FS Client**: Core protocol communication
5. **Build One-Click Workflow**: Integrate all components

---

**CONCLUSION**: M4 provides a solid foundation with the serial FS protocol architecture. M5 desktop app development can now proceed with clear requirements, architecture, and implementation phases. The system will provide users with a seamless, one-click device update experience while maintaining the robust, atomic update safety of the M4 protocol.
