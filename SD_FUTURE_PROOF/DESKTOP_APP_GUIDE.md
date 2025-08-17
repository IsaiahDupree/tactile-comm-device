# Desktop App Development Guide

## Overview

The future-proof tactile communication system is designed from the ground up to support desktop applications on Windows, Mac, and Linux. This guide shows developers how to create tools that work seamlessly with the device.

## Core Principles

### 1. File-Based API
Everything is controlled through standard files:
- **Configuration**: Simple CSV and INI files
- **Playlists**: Standard M3U format
- **Audio**: Standard MP3 files
- **State**: JSON for complex data

### 2. Cross-Platform Compatibility
- Forward slash paths work on all platforms
- UTF-8 encoding for international support
- FAT32 filesystem constraints respected
- Standard audio formats only

### 3. Versioned Contract
The `manifest.json` provides a stable API that won't break as the system evolves.

## File Format Specifications

### Manifest File (`manifest.json`)
```json
{
  "schema": "tcd-playlists@1",
  "version": "1.0.0",
  "created": "2025-01-15",
  "description": "Future-proof tactile communication device configuration",
  "priority": "HUMAN_FIRST",
  "strict_playlists": true,
  "hardware": {
    "pcf8575_count": 3,
    "gpio_pins": [8, 9, 2, 5],
    "total_capacity": 52
  },
  "keys": [
    {
      "key": "A",
      "human_playlist": "mappings/playlists/A_human.m3u",
      "generated_playlist": "mappings/playlists/A_generated.m3u",
      "human_dir": "audio/human/A",
      "generated_dir": "audio/generated/A"
    }
  ]
}
```

### Button Configuration (`config/buttons.csv`)
```csv
#INPUT,KEY
pcf0:00,A
pcf0:01,B
pcf2:15,Emergency
gpio:8,Home
```

### Mode Configuration (`config/mode.cfg`)
```ini
PRIORITY=HUMAN_FIRST
STRICT_PLAYLISTS=1
```

### Playlist Files (`mappings/playlists/{KEY}_{TYPE}.m3u`)
```
# Human recordings for A
audio/human/A/001.mp3
audio/human/A/002.mp3
audio/human/A/003.mp3
```

### State Persistence (`state/cursors.json`)
```json
{
  "A": {
    "humanIdx": 2,
    "generatedIdx": 0
  },
  "Water": {
    "humanIdx": 0,
    "generatedIdx": 1
  }
}
```

## Desktop App Examples

### 1. Simple Playlist Editor (Python)

```python
#!/usr/bin/env python3
"""
Simple playlist editor for tactile communication device
"""
import json
import os
from pathlib import Path

class TactileDeviceManager:
    def __init__(self, sd_path):
        self.sd_path = Path(sd_path)
        self.manifest = self.load_manifest()
    
    def load_manifest(self):
        manifest_path = self.sd_path / "manifest.json"
        if manifest_path.exists():
            with open(manifest_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        return None
    
    def get_keys(self):
        if self.manifest:
            return [key_info['key'] for key_info in self.manifest['keys']]
        return []
    
    def get_playlist(self, key, playlist_type):
        """Get playlist contents for a key and type (human/generated)"""
        playlist_path = self.sd_path / "mappings" / "playlists" / f"{key}_{playlist_type}.m3u"
        if playlist_path.exists():
            with open(playlist_path, 'r', encoding='utf-8') as f:
                tracks = []
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        tracks.append(line)
                return tracks
        return []
    
    def save_playlist(self, key, playlist_type, tracks):
        """Save playlist contents for a key and type"""
        playlist_path = self.sd_path / "mappings" / "playlists" / f"{key}_{playlist_type}.m3u"
        with open(playlist_path, 'w', encoding='utf-8') as f:
            f.write(f"# {playlist_type.title()} recordings for {key}\n")
            for track in tracks:
                f.write(f"{track}\n")
    
    def add_audio_file(self, key, playlist_type, audio_file_path):
        """Add an audio file to a key's playlist"""
        # Copy file to appropriate directory
        target_dir = self.sd_path / "audio" / playlist_type / key
        target_dir.mkdir(parents=True, exist_ok=True)
        
        # Find next available filename
        existing_files = list(target_dir.glob("*.mp3"))
        next_num = len(existing_files) + 1
        target_file = target_dir / f"{next_num:03d}.mp3"
        
        # Copy the file (in real app, use shutil.copy2)
        import shutil
        shutil.copy2(audio_file_path, target_file)
        
        # Update playlist
        tracks = self.get_playlist(key, playlist_type)
        relative_path = f"audio/{playlist_type}/{key}/{target_file.name}"
        tracks.append(relative_path)
        self.save_playlist(key, playlist_type, tracks)
        
        return target_file

# Example usage
if __name__ == "__main__":
    device = TactileDeviceManager("E:/")  # SD card drive
    
    # List all keys
    print("Available keys:", device.get_keys())
    
    # Get playlist for key 'A'
    human_tracks = device.get_playlist('A', 'human')
    print("Human tracks for A:", human_tracks)
    
    # Add a new audio file
    # device.add_audio_file('A', 'human', 'new_recording.mp3')
```

### 2. Hardware Configuration Tool (JavaScript/Electron)

```javascript
// Electron app for configuring button mappings
const fs = require('fs').promises;
const path = require('path');

class ButtonMapper {
    constructor(sdPath) {
        this.sdPath = sdPath;
        this.configPath = path.join(sdPath, 'config', 'buttons.csv');
    }
    
    async loadButtonMappings() {
        try {
            const content = await fs.readFile(this.configPath, 'utf-8');
            const mappings = [];
            
            for (const line of content.split('\n')) {
                const trimmed = line.trim();
                if (trimmed && !trimmed.startsWith('#')) {
                    const [input, key] = trimmed.split(',');
                    if (input && key) {
                        mappings.push({ input: input.trim(), key: key.trim() });
                    }
                }
            }
            
            return mappings;
        } catch (error) {
            console.error('Failed to load button mappings:', error);
            return [];
        }
    }
    
    async saveButtonMappings(mappings) {
        let content = '#INPUT,KEY\n';
        for (const mapping of mappings) {
            content += `${mapping.input},${mapping.key}\n`;
        }
        
        await fs.writeFile(this.configPath, content, 'utf-8');
    }
    
    async addButtonMapping(input, key) {
        const mappings = await this.loadButtonMappings();
        
        // Remove existing mapping for this input
        const filtered = mappings.filter(m => m.input !== input);
        
        // Add new mapping
        filtered.push({ input, key });
        
        await this.saveButtonMappings(filtered);
    }
}

// Example usage in Electron renderer process
const buttonMapper = new ButtonMapper('E:/');

// Load and display current mappings
buttonMapper.loadButtonMappings().then(mappings => {
    console.log('Current button mappings:', mappings);
    
    // Display in UI
    const mappingsList = document.getElementById('mappings-list');
    mappingsList.innerHTML = '';
    
    for (const mapping of mappings) {
        const item = document.createElement('div');
        item.innerHTML = `
            <span>${mapping.input}</span> → <span>${mapping.key}</span>
            <button onclick="removeMapping('${mapping.input}')">Remove</button>
        `;
        mappingsList.appendChild(item);
    }
});
```

### 3. Audio Content Manager (C#/.NET)

```csharp
using System;
using System.Collections.Generic;
using System.IO;
using System.Text.Json;

public class TactileDeviceAudioManager
{
    private readonly string _sdPath;
    private readonly string _manifestPath;
    
    public TactileDeviceAudioManager(string sdPath)
    {
        _sdPath = sdPath;
        _manifestPath = Path.Combine(sdPath, "manifest.json");
    }
    
    public async Task<DeviceManifest> LoadManifestAsync()
    {
        if (!File.Exists(_manifestPath))
            return null;
            
        var json = await File.ReadAllTextAsync(_manifestPath);
        return JsonSerializer.Deserialize<DeviceManifest>(json);
    }
    
    public async Task<List<string>> GetPlaylistAsync(string key, string type)
    {
        var playlistPath = Path.Combine(_sdPath, "mappings", "playlists", $"{key}_{type}.m3u");
        
        if (!File.Exists(playlistPath))
            return new List<string>();
            
        var lines = await File.ReadAllLinesAsync(playlistPath);
        return lines.Where(line => !string.IsNullOrWhiteSpace(line) && !line.StartsWith("#")).ToList();
    }
    
    public async Task SavePlaylistAsync(string key, string type, List<string> tracks)
    {
        var playlistPath = Path.Combine(_sdPath, "mappings", "playlists", $"{key}_{type}.m3u");
        var directory = Path.GetDirectoryName(playlistPath);
        
        if (!Directory.Exists(directory))
            Directory.CreateDirectory(directory);
            
        var content = new List<string>
        {
            $"# {char.ToUpper(type[0])}{type.Substring(1)} recordings for {key}"
        };
        content.AddRange(tracks);
        
        await File.WriteAllLinesAsync(playlistPath, content);
    }
    
    public async Task<string> AddAudioFileAsync(string key, string type, string sourceFilePath)
    {
        var targetDir = Path.Combine(_sdPath, "audio", type, key);
        Directory.CreateDirectory(targetDir);
        
        // Find next available filename
        var existingFiles = Directory.GetFiles(targetDir, "*.mp3");
        var nextNum = existingFiles.Length + 1;
        var targetFileName = $"{nextNum:D3}.mp3";
        var targetFilePath = Path.Combine(targetDir, targetFileName);
        
        // Copy the file
        File.Copy(sourceFilePath, targetFilePath);
        
        // Update playlist
        var playlist = await GetPlaylistAsync(key, type);
        var relativePath = $"audio/{type}/{key}/{targetFileName}";
        playlist.Add(relativePath);
        await SavePlaylistAsync(key, type, playlist);
        
        return targetFilePath;
    }
}

public class DeviceManifest
{
    public string Schema { get; set; }
    public string Version { get; set; }
    public string Priority { get; set; }
    public bool StrictPlaylists { get; set; }
    public List<KeyInfo> Keys { get; set; }
}

public class KeyInfo
{
    public string Key { get; set; }
    public string HumanPlaylist { get; set; }
    public string GeneratedPlaylist { get; set; }
    public string HumanDir { get; set; }
    public string GeneratedDir { get; set; }
}
```

## Desktop App Features to Implement

### Essential Features
1. **Audio File Management**
   - Drag & drop audio files
   - Automatic playlist updates
   - Audio preview/playback
   - File format conversion

2. **Button Configuration**
   - Visual button layout editor
   - Hardware detection and mapping
   - Conflict detection and resolution
   - Import/export configurations

3. **Playlist Management**
   - Reorder tracks via drag & drop
   - Bulk operations (add/remove multiple)
   - Playlist validation and repair
   - Cross-key audio sharing

### Advanced Features
1. **Content Generation**
   - Text-to-speech integration
   - Voice recording with noise reduction
   - Batch audio processing
   - Multi-language support

2. **Device Management**
   - SD card backup and restore
   - Firmware update management
   - Configuration synchronization
   - Usage analytics and reporting

3. **Collaboration Features**
   - Share configurations between devices
   - Cloud backup and sync
   - Version control for content
   - Multi-user content management

## Best Practices

### File Handling
- Always use UTF-8 encoding for text files
- Use forward slashes in paths for cross-platform compatibility
- Validate file paths before writing
- Handle SD card removal gracefully

### Error Handling
- Validate manifest schema version before processing
- Provide meaningful error messages
- Implement graceful degradation for missing files
- Log all file operations for debugging

### User Experience
- Provide real-time validation feedback
- Show progress for long operations
- Implement undo/redo functionality
- Support keyboard shortcuts for power users

### Performance
- Cache frequently accessed data
- Use background threads for file operations
- Implement lazy loading for large datasets
- Optimize for SD card read/write speeds

## Testing Your Desktop App

### Test Cases
1. **File System Tests**
   - SD card insertion/removal
   - File permission issues
   - Corrupted files
   - Missing directories

2. **Configuration Tests**
   - Invalid button mappings
   - Missing playlist files
   - Malformed manifest
   - Hardware conflicts

3. **Audio Tests**
   - Unsupported file formats
   - Corrupted audio files
   - Very large files
   - Unicode filenames

### Integration Testing
1. Create test configurations on SD card
2. Test with actual hardware device
3. Verify audio playback works correctly
4. Test priority mode switching
5. Validate multi-press behavior

## Conclusion

This file-based API design makes desktop app development straightforward while maintaining complete compatibility with the embedded device. The standard file formats ensure your apps will work across platforms and remain compatible as the system evolves.

The key to success is following the established file formats and respecting the directory structure. This ensures your desktop app will work seamlessly with the device and any other tools in the ecosystem.
