# WiFi File Management Guide
## Tactile Communication Device

### Table of Contents
1. [Overview](#overview)
2. [WiFi Setup](#wifi-setup)
3. [Connection Methods](#connection-methods)
4. [Web Interface](#web-interface)
5. [Python CLI Tool](#python-cli-tool)
6. [Command Line (curl)](#command-line-curl)
7. [Authentication](#authentication)
8. [Troubleshooting](#troubleshooting)
9. [Technical Details](#technical-details)

---

## Overview

The Tactile Communication Device supports WiFi-based file management, allowing you to upload, download, browse, and delete files on the device's SD card remotely. This guide covers all available methods for managing files over WiFi.

### Key Features
- **Web Browser Interface** - Point-and-click file management
- **Python CLI Tool** - Command-line interface with progress bars
- **HTTP API** - Direct REST API access via curl or custom tools
- **SoftAP Mode** - Device creates its own WiFi network (no router needed)
- **Station Mode** - Connect to existing WiFi networks
- **Secure Authentication** - Token-based security for write operations
- **Progress Monitoring** - Real-time transfer speeds and progress
- **FAT32 Compatible** - Works with 8.3 filenames and long filenames

---

## WiFi Setup

### Option 1: SoftAP Mode (Default)
The device creates its own WiFi network:
- **Network Name:** `TCD-Device`
- **Password:** `tcd12345`
- **Device IP:** `192.168.4.1`
- **No router required** - works anywhere

### Option 2: Station Mode (Connect to Existing WiFi)
Create `/CONFIG/WIFI.CFG` on the SD card:
```
SSID=YourWiFiName
PASS=YourWiFiPassword
TOKEN=MySecret123
```

The device will connect to your existing WiFi network and obtain an IP address via DHCP.

---

## Connection Methods

### 1. Web Interface
**URL:** `http://192.168.4.1/` (SoftAP) or `http://<device-ip>/` (Station)

**With Authentication:** `http://192.168.4.1/?token=MySecret123`

### 2. Python CLI Tool
```bash
python tcd_http.py <device-ip> [--token <auth-token>] <command> [args]
```

### 3. HTTP API (curl)
```bash
curl "http://192.168.4.1/api/<endpoint>?token=MySecret123"
```

---

## Web Interface

### Accessing the Web Interface
1. Connect to the device WiFi network (`TCD-Device`)
2. Open browser to `http://192.168.4.1/`
3. Add token to URL if authentication is enabled: `?token=MySecret123`

### Features
- **Browse Directories** - Click folders to navigate
- **Download Files** - Click "Download" button next to files
- **Upload Files** - Use "Choose File" and "Upload" buttons
- **Delete Files** - Click "Delete" link next to files
- **Real-time Progress** - View transfer progress in browser console (F12)

### Browser Console Logs
Press F12 to open developer tools and view transfer progress:
```
[PUT] 524288/1048576 50.0% @ 1.23 MB/s
[GET] /AUDIO/file.mp3 1048576/1048576 100.0% @ 0.87 MB/s
```

---

## Python CLI Tool

### Installation
```bash
pip install requests tqdm
```

### Basic Commands

#### List Directory Contents
```bash
python tcd_http.py 192.168.4.1 ls /AUDIO
python tcd_http.py 192.168.4.1 --token MySecret123 ls /CONFIG
```

#### Upload Files
```bash
# Upload to specific path
python tcd_http.py 192.168.4.1 put local_file.mp3 /AUDIO/remote_file.mp3

# Upload to directory (uses original filename)
python tcd_http.py 192.168.4.1 put local_file.mp3 /AUDIO/

# With authentication
python tcd_http.py 192.168.4.1 --token MySecret123 put file.mp3 /AUDIO/file.mp3
```

#### Download Files
```bash
# Download to current directory
python tcd_http.py 192.168.4.1 get /AUDIO/file.mp3

# Download with custom local name
python tcd_http.py 192.168.4.1 get /AUDIO/file.mp3 -o local_name.mp3
```

#### Delete Files
```bash
python tcd_http.py 192.168.4.1 --token MySecret123 del /AUDIO/file.mp3
```

### Progress Bars
The Python tool shows real-time progress with transfer speeds:
```
Upload: 75%|████████████████████   | 768KB/1.0MB [00:03<00:01, 245KB/s]
Download: 100%|████████████████████████| 1.0MB/1.0MB [00:04<00:00, 256KB/s]
```

---

## Command Line (curl)

### List Directory
```bash
curl "http://192.168.4.1/api/ls?path=/AUDIO"
```

### Download File
```bash
curl -o local_file.mp3 "http://192.168.4.1/api/get?path=/AUDIO/file.mp3"
```

### Upload File
```bash
# Upload to specific path
curl -X POST --data-binary @local_file.mp3 \
  "http://192.168.4.1/api/put?path=/AUDIO/file.mp3&token=MySecret123"

# Upload to directory with name parameter
curl -X POST --data-binary @local_file.mp3 \
  "http://192.168.4.1/api/put?path=/AUDIO/&name=file.mp3&token=MySecret123"
```

### Delete File
```bash
curl "http://192.168.4.1/api/del?path=/AUDIO/file.mp3&token=MySecret123"
```

---

## Authentication

### Security Modes

#### Mode 1: No Authentication (Testing)
- Set `DATA_WIFI_REQUIRE_AUTH 0` in firmware
- All operations work without tokens
- **Not recommended for production use**

#### Mode 2: Token Authentication (Recommended)
- Set `DATA_WIFI_REQUIRE_AUTH 1` in firmware
- Requires authentication token for upload/delete operations
- Download and browse operations work without authentication

### Setting Up Authentication
1. Create `/CONFIG/WIFI.CFG` with your token:
   ```
   SSID=YourWiFiName
   PASS=YourWiFiPassword
   TOKEN=MySecret123
   ```

2. Use token in requests:
   - **URL Parameter:** `?token=MySecret123`
   - **Bearer Header:** `Authorization: Bearer MySecret123`

### Token Requirements
- Upload operations (PUT) require authentication
- Delete operations (DEL) require authentication
- Download operations (GET) work without authentication
- Directory listing (LS) works without authentication

---

## Troubleshooting

### Connection Issues

#### Cannot Connect to TCD-Device Network
- **Check WiFi:** Ensure device is powered and WiFi is enabled
- **Password:** Use `tcd12345` for default SoftAP
- **Range:** Move closer to device
- **Reset:** Power cycle the device

#### Device Not Responding to HTTP Requests
- **IP Address:** Verify you're using `192.168.4.1` for SoftAP
- **Firewall:** Check Windows firewall settings
- **Browser Cache:** Try incognito/private browsing mode

### Upload/Download Issues

#### Upload Fails with "Connection Reset" Error
- **Filename Length:** Use 8.3 filenames (8 chars + 3 char extension)
- **Authentication:** Ensure token is correct if auth is enabled
- **SD Card Space:** Check available space on SD card
- **File Size:** Large files may timeout - try smaller chunks

#### Delete Operations Fail
- **Case Sensitivity:** Try exact filename from directory listing
- **8.3 Names:** On FAT32, try both long and short names
- **Authentication:** Ensure token is provided for delete operations

#### Slow Transfer Speeds
- **WiFi Signal:** Move closer to device
- **Network Congestion:** Try different WiFi channel
- **SD Card Speed:** Use Class 10 or better SD cards
- **File Size:** Larger files transfer more efficiently

### Authentication Issues

#### "401 Unauthorized" Errors
- **Token Missing:** Add `?token=YourToken` to URL
- **Wrong Token:** Check `/CONFIG/WIFI.CFG` for correct token
- **Case Sensitive:** Tokens are case-sensitive

#### "need_name" Error
- **Directory Upload:** When uploading to `/AUDIO/`, add `&name=filename.mp3`
- **Path Format:** Ensure directory paths end with `/`

---

## Technical Details

### HTTP API Endpoints

#### GET /api/ls
**Purpose:** List directory contents
**Parameters:**
- `path` - Directory path (default: `/`)
**Authentication:** Not required
**Response:** JSON array of files/directories

#### GET /api/get
**Purpose:** Download file
**Parameters:**
- `path` - File path (required)
**Authentication:** Not required
**Response:** File content with appropriate headers

#### POST /api/put
**Purpose:** Upload file
**Parameters:**
- `path` - Target path or directory (required)
- `name` - Filename when uploading to directory (optional)
- `token` - Authentication token (required if auth enabled)
**Authentication:** Required for write operations
**Body:** File content (binary)

#### GET /api/del
**Purpose:** Delete file
**Parameters:**
- `path` - File path (required)
- `token` - Authentication token (required if auth enabled)
**Authentication:** Required for write operations

### File System Compatibility

#### FAT32 Limitations
- **8.3 Filenames:** Traditional DOS naming (8 chars + 3 extension)
- **Long Filename Support:** Depends on SD library configuration
- **Case Sensitivity:** FAT32 is case-insensitive
- **Special Characters:** Avoid spaces and special characters in filenames

#### Recommended Naming
- **Audio Files:** `001.MP3`, `002.MP3`, etc.
- **Config Files:** `WIFI.CFG`, `KEYS.CSV`, etc.
- **Avoid:** Long names, spaces, special characters

### Network Configuration

#### SoftAP Mode Settings
- **SSID:** `TCD-Device` (configurable via WIFI.CFG)
- **Password:** `tcd12345` (configurable via WIFI.CFG)
- **IP Range:** `192.168.4.1/24`
- **DHCP:** Enabled for client devices
- **Encryption:** WPA2

#### Station Mode Settings
- **DHCP Client:** Obtains IP from router
- **Fallback:** Switches to SoftAP if connection fails
- **Reconnection:** Automatic retry on disconnect

### Performance Optimization

#### Transfer Speed Factors
- **Buffer Size:** 1460 bytes (WiFi MTU optimized)
- **Progress Logging:** Every 16KB to avoid overhead
- **SD Card Speed:** Class 10+ recommended
- **WiFi Signal Strength:** Affects throughput significantly

#### Memory Usage
- **RAM:** Minimal impact, streaming design
- **Flash:** HTTP server adds ~15KB to firmware
- **SD Card:** Temporary files use `.TMP` extension

---

## Support

For technical support or feature requests, please visit:
- **GitHub Repository:** [tactile-comm-device](https://github.com/IsaiahDupree/tactile-comm-device)
- **Documentation:** `/docs/` directory
- **Issues:** GitHub Issues tracker

---

*Last Updated: August 2025*
*Firmware Version: v7 with HTTP File Management*
