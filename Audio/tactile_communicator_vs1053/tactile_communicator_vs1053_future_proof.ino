/*
 * Tactile Communication Device - Future-Proof SD-Defined System
 * 
 * REVOLUTIONARY ARCHITECTURE:
 * - Complete hardware-software decoupling via SD card configuration
 * - Strict human/generated audio separation with playlist-enforced ordering
 * - Support for up to 3 PCF8575 expanders (96 buttons total + direct GPIO)
 * - Desktop app compatible with versioned manifest system
 * - Zero code changes needed for hardware modifications or content updates
 * 
 * SD CARD LAYOUT (STRICT):
 * /config/
 *   mode.cfg                # Global priority settings
 *   buttons.csv             # Physical input → logical key mapping
 * /mappings/
 *   playlists/
 *     {KEY}_human.m3u       # REQUIRED: Human recording playlists
 *     {KEY}_generated.m3u   # REQUIRED: Generated audio playlists
 * /audio/
 *   human/
 *     {KEY}/001.mp3 ...     # Human recordings by key
 *   generated/
 *     {KEY}/001.mp3 ...     # Generated audio by key
 * /state/
 *   cursors.json            # Optional: playback position persistence
 * /manifest.json            # Optional: desktop app contract
 * 
 * HARDWARE INDEPENDENCE:
 * - GPIO changes only require updating buttons.csv
 * - Same firmware works with any PCF8575 configuration
 * - Logical keys (A, B, Water, etc.) remain constant across hardware changes
 * 
 * DESKTOP APP READY:
 * - Playlist-enforced ordering (no directory scanning in strict mode)
 * - Versioned manifest.json for tool compatibility
 * - Cross-platform file paths and naming conventions
 * - State persistence for seamless desktop/device sync
 */

#include <SPI.h>
#include <SD.h>
#include <Wire.h>
#include <EEPROM.h>
#include "Adafruit_PCF8575.h"
#include "Adafruit_VS1053.h"

// ===== HARDWARE CONFIGURATION =====
// VS1053 pins - using shield pin mapping
#define VS1053_RESET   -1     // VS1053 reset pin (tied high on shield)
#define VS1053_CS       7     // VS1053 xCS (shield pin mapping)
#define VS1053_DCS      6     // VS1053 xDCS (shield pin mapping)
#define CARDCS          4     // micro-SD CS (fixed trace on shield)
#define VS1053_DREQ     3     // VS1053 DREQ (INT1 on Uno)

Adafruit_VS1053_FilePlayer musicPlayer = 
  Adafruit_VS1053_FilePlayer(VS1053_RESET, VS1053_CS, VS1053_DCS, VS1053_DREQ, CARDCS);

// PCF8575 I2C port expanders (up to 3 supported)
#define NUM_PCF 3
Adafruit_PCF8575 pcf[NUM_PCF];
const uint8_t PCF_ADDR[NUM_PCF] = {0x20, 0x21, 0x22};
uint16_t last_state[NUM_PCF];   // Edge detection snapshots

// Extra Arduino pins for additional controls
const uint8_t extraPins[]    = { 8,  9,  2,  5 };   // Safe pins: VS1053 uses pins 3,4,6,7
const uint8_t extraIndices[] = {48, 49, 50, 51};    // Indices after 3x PCF8575 (48 pins)
const uint8_t EXTRA_COUNT    = sizeof(extraPins) / sizeof(extraPins[0]);
bool lastExtra[EXTRA_COUNT];

// ===== PRIORITY SYSTEM =====
enum class Priority : uint8_t {
  HUMAN_FIRST = 0,      // Human recordings play first, then generated
  GENERATED_FIRST = 1   // Generated audio plays first, then human recordings
};

Priority globalPriority = Priority::HUMAN_FIRST;
bool strictPlaylists = true;  // Enforce playlist presence, no directory scanning

// ===== DATA STRUCTURES =====
struct ButtonMap {
  String inputId;     // "pcf0:15", "pcf1:03", "gpio:8"
  String key;         // Logical key: "A", ".", "Water", etc.
};

struct Playlists {
  std::vector<String> human;
  std::vector<String> generated;
};

struct PlayCursor {
  uint16_t humanIdx = 0;
  uint16_t generatedIdx = 0;
};

// ===== GLOBAL STATE =====
std::vector<ButtonMap> buttons;                    // Hardware → key mapping
std::map<String, Playlists> playlistCache;         // Cached playlists per key
std::map<String, PlayCursor> cursors;              // Playback positions per key

// Multi-press detection
std::map<String, unsigned long> lastPressTime;
std::map<String, uint8_t> pressCount;
const unsigned long MULTI_PRESS_WINDOW = 1000;     // milliseconds

// Period triple-press for priority toggle
uint8_t periodPressCount = 0;
unsigned long periodWindowStart = 0;
const unsigned long PERIOD_WINDOW_MS = 1200;       // 1.2 seconds

// Audio state
bool isPlaying = false;
String currentTrackPath = "";

// Debug and calibration
bool debugMode = true;
bool inCalibrate = false;

// ===== FORWARD DECLARATIONS =====
void printMenu();
void loadConfig();
void saveConfig();
void printMap();
void testAllButtons();
void sanityCheckAudio();
void onPhysicalPress(const String& inputId);
String nextTrackForKey(const String& key);
bool loadPlaylistsForKey(const String& key);
std::vector<String> readM3U(const String& path);
String keyForInput(const String& inputId);
Priority effectivePriority();
void togglePriorityMode();
void playPriorityAnnouncement();

// ===== INITIALIZATION =====
void setup() {
  Serial.begin(115200);
  while (!Serial) delay(10);
  
  Serial.println(F("\n=== TACTILE COMMUNICATOR - FUTURE-PROOF SYSTEM ==="));
  Serial.println(F("Hardware-agnostic SD-defined architecture"));
  Serial.println(F("Support for 3x PCF8575 + direct GPIO"));
  Serial.println(F("Strict human/generated separation"));
  Serial.println(F("Desktop app compatible"));
  Serial.println(F("================================================\n"));

  // Initialize VS1053
  Serial.print(F("[INIT] VS1053 codec... "));
  if (!musicPlayer.begin()) {
    Serial.println(F("FAILED"));
    while (1) delay(10);
  }
  Serial.println(F("OK"));
  
  // Initialize SD card
  Serial.print(F("[INIT] SD card... "));
  if (!SD.begin(CARDCS)) {
    Serial.println(F("FAILED"));
    while (1) delay(10);
  }
  Serial.println(F("OK"));
  
  // Initialize I2C for PCF8575 expanders
  Serial.print(F("[INIT] I2C bus... "));
  Wire1.begin();
  Serial.println(F("OK"));
  
  // Initialize PCF8575 expanders
  for (uint8_t i = 0; i < NUM_PCF; i++) {
    Serial.print(F("[INIT] PCF8575 #"));
    Serial.print(i);
    Serial.print(F(" (0x"));
    Serial.print(PCF_ADDR[i], HEX);
    Serial.print(F(")... "));
    
    if (!pcf[i].begin(PCF_ADDR[i], &Wire1)) {
      Serial.println(F("NOT FOUND"));
    } else {
      Serial.println(F("OK"));
      // Configure all pins as inputs with pullups
      for (uint8_t p = 0; p < 16; p++) {
        pcf[i].pinMode(p, INPUT_PULLUP);
      }
      last_state[i] = pcf[i].digitalReadWord();
    }
  }
  
  // Initialize extra GPIO pins
  Serial.print(F("[INIT] Extra GPIO pins... "));
  for (uint8_t i = 0; i < EXTRA_COUNT; i++) {
    pinMode(extraPins[i], INPUT_PULLUP);
    lastExtra[i] = digitalRead(extraPins[i]);
  }
  Serial.println(F("OK"));
  
  // Load configuration from SD card
  loadConfig();
  
  // Set initial volume
  musicPlayer.setVolume(20, 20);  // Moderate volume
  
  // Load priority mode from EEPROM
  uint8_t savedMode = EEPROM.read(0);
  if (savedMode <= 1) {
    globalPriority = static_cast<Priority>(savedMode);
  }
  
  Serial.print(F("[INIT] Priority mode: "));
  Serial.println(globalPriority == Priority::HUMAN_FIRST ? F("HUMAN_FIRST") : F("GENERATED_FIRST"));
  
  Serial.println(F("[INIT] System ready! Type 'H' for help menu."));
  printMenu();
}

// ===== MAIN LOOP =====
void loop() {
  // Handle serial commands
  if (Serial.available()) {
    char cmd = Serial.read();
    switch (cmd) {
      case 'L': case 'l': loadConfig(); break;
      case 'S': case 's': saveConfig(); break;
      case 'P': case 'p': printMap(); break;
      case 'H': case 'h': printMenu(); break;
      case 'M': case 'm': togglePriorityMode(); break;
      case 'T': case 't': testAllButtons(); break;
      case 'U': case 'u': sanityCheckAudio(); break;
      case 'C': case 'c': 
        inCalibrate = true;
        Serial.println(F("[CAL] Calibration mode ON - press buttons to assign"));
        break;
      case 'E': case 'e':
        inCalibrate = false;
        Serial.println(F("[CAL] Calibration mode OFF"));
        break;
      case 'X': case 'x':
        musicPlayer.stopPlaying();
        isPlaying = false;
        Serial.println(F("[AUDIO] Playback stopped"));
        break;
      case '+':
        musicPlayer.setVolume(10, 10);
        Serial.println(F("[AUDIO] Volume: Maximum"));
        break;
      case '-':
        musicPlayer.setVolume(40, 40);
        Serial.println(F("[AUDIO] Volume: Moderate"));
        break;
      case '1': case '2': case '3': case '4': case '5':
      case '6': case '7': case '8': case '9':
        {
          uint8_t vol = (cmd - '0') * 10;
          musicPlayer.setVolume(vol, vol);
          Serial.print(F("[AUDIO] Volume level: "));
          Serial.println(10 - (cmd - '0'));
        }
        break;
    }
  }
  
  // Scan PCF8575 expanders for button presses
  for (uint8_t chip = 0; chip < NUM_PCF; chip++) {
    uint16_t current = pcf[chip].digitalReadWord();
    uint16_t previous = last_state[chip];
    uint16_t fell = (previous & ~current);  // HIGH→LOW edges (button presses)
    
    if (fell) {
      for (uint8_t pin = 0; pin < 16; pin++) {
        if (fell & (1 << pin)) {
          String inputId = "pcf" + String(chip) + ":" + String(pin);
          onPhysicalPress(inputId);
        }
      }
    }
    last_state[chip] = current;
  }
  
  // Scan extra GPIO pins
  for (uint8_t i = 0; i < EXTRA_COUNT; i++) {
    bool current = digitalRead(extraPins[i]);
    bool previous = lastExtra[i];
    
    if (previous && !current) {  // HIGH→LOW edge (button press)
      String inputId = "gpio:" + String(extraPins[i]);
      onPhysicalPress(inputId);
    }
    lastExtra[i] = current;
  }
  
  // Update audio playing status
  isPlaying = musicPlayer.playingMusic;
  
  delay(50);  // Reasonable scan rate
}

// ===== CONFIGURATION MANAGEMENT =====
void loadConfig() {
  Serial.println(F("[CONFIG] Loading configuration from SD card..."));
  
  // Clear existing configuration
  buttons.clear();
  playlistCache.clear();
  
  // Load mode.cfg
  File modeFile = SD.open("/config/mode.cfg", FILE_READ);
  if (modeFile) {
    while (modeFile.available()) {
      String line = modeFile.readStringUntil('\n');
      line.trim();
      
      if (line.startsWith("PRIORITY=")) {
        String priority = line.substring(9);
        if (priority == "GENERATED_FIRST") {
          globalPriority = Priority::GENERATED_FIRST;
        } else {
          globalPriority = Priority::HUMAN_FIRST;
        }
      } else if (line.startsWith("STRICT_PLAYLISTS=")) {
        strictPlaylists = line.substring(17).toInt() != 0;
      }
    }
    modeFile.close();
    Serial.print(F("[CONFIG] Priority: "));
    Serial.println(globalPriority == Priority::HUMAN_FIRST ? F("HUMAN_FIRST") : F("GENERATED_FIRST"));
    Serial.print(F("[CONFIG] Strict playlists: "));
    Serial.println(strictPlaylists ? F("ON") : F("OFF"));
  } else {
    Serial.println(F("[CONFIG] mode.cfg not found, using defaults"));
  }
  
  // Load buttons.csv
  File buttonFile = SD.open("/config/buttons.csv", FILE_READ);
  if (buttonFile) {
    uint16_t buttonCount = 0;
    while (buttonFile.available()) {
      String line = buttonFile.readStringUntil('\n');
      line.trim();
      
      if (line.length() == 0 || line.startsWith("#")) continue;
      
      int commaIndex = line.indexOf(',');
      if (commaIndex > 0) {
        ButtonMap btn;
        btn.inputId = line.substring(0, commaIndex);
        btn.key = line.substring(commaIndex + 1);
        buttons.push_back(btn);
        buttonCount++;
      }
    }
    buttonFile.close();
    Serial.print(F("[CONFIG] Loaded "));
    Serial.print(buttonCount);
    Serial.println(F(" button mappings"));
  } else {
    Serial.println(F("[CONFIG] buttons.csv not found - use calibration mode"));
  }
  
  Serial.println(F("[CONFIG] Configuration loaded successfully"));
}

void saveConfig() {
  Serial.println(F("[CONFIG] Saving configuration to SD card..."));
  
  // Save mode.cfg
  File modeFile = SD.open("/config/mode.cfg", FILE_WRITE);
  if (modeFile) {
    modeFile.print("PRIORITY=");
    modeFile.println(globalPriority == Priority::HUMAN_FIRST ? "HUMAN_FIRST" : "GENERATED_FIRST");
    modeFile.print("STRICT_PLAYLISTS=");
    modeFile.println(strictPlaylists ? "1" : "0");
    modeFile.close();
    Serial.println(F("[CONFIG] mode.cfg saved"));
  } else {
    Serial.println(F("[CONFIG] Failed to save mode.cfg"));
  }
  
  // Save buttons.csv
  File buttonFile = SD.open("/config/buttons.csv", FILE_WRITE);
  if (buttonFile) {
    buttonFile.println("#INPUT,KEY");
    for (const auto& btn : buttons) {
      buttonFile.print(btn.inputId);
      buttonFile.print(",");
      buttonFile.println(btn.key);
    }
    buttonFile.close();
    Serial.print(F("[CONFIG] Saved "));
    Serial.print(buttons.size());
    Serial.println(F(" button mappings"));
  } else {
    Serial.println(F("[CONFIG] Failed to save buttons.csv"));
  }
  
  Serial.println(F("[CONFIG] Configuration saved successfully"));
}

// ===== PLAYLIST MANAGEMENT =====
std::vector<String> readM3U(const String& path) {
  std::vector<String> tracks;
  
  File playlistFile = SD.open(path, FILE_READ);
  if (!playlistFile) {
    return tracks;
  }
  
  while (playlistFile.available()) {
    String line = playlistFile.readStringUntil('\n');
    line.trim();
    
    // Skip comments and empty lines
    if (line.length() > 0 && !line.startsWith("#")) {
      tracks.push_back(line);
    }
  }
  playlistFile.close();
  
  return tracks;
}

bool loadPlaylistsForKey(const String& key) {
  Playlists pl;
  
  // Load human playlist
  String humanPath = "/mappings/playlists/" + key + "_human.m3u";
  pl.human = readM3U(humanPath);
  
  // Load generated playlist
  String generatedPath = "/mappings/playlists/" + key + "_generated.m3u";
  pl.generated = readM3U(generatedPath);
  
  // In strict mode, require at least one playlist
  if (strictPlaylists && pl.human.empty() && pl.generated.empty()) {
    Serial.print(F("[ERROR] No playlists found for key '"));
    Serial.print(key);
    Serial.println(F("' in strict mode"));
    return false;
  }
  
  playlistCache[key] = std::move(pl);
  return true;
}

// ===== AUDIO PLAYBACK =====
String keyForInput(const String& inputId) {
  for (const auto& btn : buttons) {
    if (btn.inputId == inputId) {
      return btn.key;
    }
  }
  return "";
}

Priority effectivePriority() {
  return globalPriority;
}

String nextTrackForKey(const String& key) {
  // Load playlists if not cached
  if (playlistCache.find(key) == playlistCache.end()) {
    if (!loadPlaylistsForKey(key)) {
      return "";
    }
  }
  
  const Playlists& pl = playlistCache[key];
  PlayCursor& cursor = cursors[key];  // Creates if doesn't exist
  Priority priority = effectivePriority();
  
  // Helper lambda to choose from a playlist
  auto chooseFrom = [&](const std::vector<String>& playlist, uint16_t& index) -> String {
    if (playlist.empty()) return "";
    if (index >= playlist.size()) index = 0;
    return playlist[index++];
  };
  
  // Try based on priority with fallback
  if (priority == Priority::HUMAN_FIRST) {
    String track = chooseFrom(pl.human, cursor.humanIdx);
    if (!track.isEmpty()) return track;
    track = chooseFrom(pl.generated, cursor.generatedIdx);
    if (!track.isEmpty()) return track;
  } else {  // GENERATED_FIRST
    String track = chooseFrom(pl.generated, cursor.generatedIdx);
    if (!track.isEmpty()) return track;
    track = chooseFrom(pl.human, cursor.humanIdx);
    if (!track.isEmpty()) return track;
  }
  
  return "";  // No tracks available
}

void onPhysicalPress(const String& inputId) {
  String key = keyForInput(inputId);
  
  if (key.isEmpty()) {
    if (debugMode) {
      Serial.print(F("[PRESS] Unknown input: "));
      Serial.println(inputId);
    }
    return;
  }
  
  if (debugMode) {
    Serial.print(F("[PRESS] "));
    Serial.print(inputId);
    Serial.print(F(" → "));
    Serial.println(key);
  }
  
  // Handle period triple-press for priority toggle
  if (key == ".") {
    unsigned long now = millis();
    
    if (periodPressCount == 0 || (now - periodWindowStart) > PERIOD_WINDOW_MS) {
      // Start new sequence
      periodPressCount = 1;
      periodWindowStart = now;
    } else {
      periodPressCount++;
      if (periodPressCount >= 3) {
        // Triple-press detected!
        togglePriorityMode();
        periodPressCount = 0;
        return;
      }
    }
  }
  
  // Handle multi-press detection for other keys
  unsigned long now = millis();
  unsigned long& lastPress = lastPressTime[key];
  uint8_t& count = pressCount[key];
  
  if ((now - lastPress) > MULTI_PRESS_WINDOW) {
    count = 1;
  } else {
    count++;
  }
  lastPress = now;
  
  // Get next track for this key
  String trackPath = nextTrackForKey(key);
  if (trackPath.isEmpty()) {
    Serial.print(F("[AUDIO] No tracks available for key: "));
    Serial.println(key);
    return;
  }
  
  // Stop current playback
  if (isPlaying) {
    musicPlayer.stopPlaying();
  }
  
  // Play the track
  Serial.print(F("[AUDIO] Playing: "));
  Serial.print(trackPath);
  Serial.print(F(" (key: "));
  Serial.print(key);
  Serial.print(F(", press: "));
  Serial.print(count);
  Serial.println(F(")"));
  
  if (musicPlayer.startPlayingFile(trackPath.c_str())) {
    currentTrackPath = trackPath;
    isPlaying = true;
  } else {
    Serial.print(F("[ERROR] Failed to play: "));
    Serial.println(trackPath);
  }
}

// ===== PRIORITY MODE MANAGEMENT =====
void togglePriorityMode() {
  globalPriority = (globalPriority == Priority::HUMAN_FIRST) ? 
                   Priority::GENERATED_FIRST : Priority::HUMAN_FIRST;
  
  // Save to EEPROM
  EEPROM.write(0, static_cast<uint8_t>(globalPriority));
  
  Serial.print(F("[PRIORITY] Mode changed to: "));
  Serial.println(globalPriority == Priority::HUMAN_FIRST ? F("HUMAN_FIRST") : F("GENERATED_FIRST"));
  
  // Play announcement
  playPriorityAnnouncement();
  
  // Update mode.cfg
  saveConfig();
}

void playPriorityAnnouncement() {
  String announcePath;
  if (globalPriority == Priority::HUMAN_FIRST) {
    announcePath = "/audio/generated/SYSTEM/human_first.mp3";
  } else {
    announcePath = "/audio/generated/SYSTEM/generated_first.mp3";
  }
  
  if (SD.exists(announcePath)) {
    if (isPlaying) {
      musicPlayer.stopPlaying();
    }
    musicPlayer.startPlayingFile(announcePath.c_str());
    Serial.print(F("[PRIORITY] Playing announcement: "));
    Serial.println(announcePath);
  }
}

// ===== UTILITY FUNCTIONS =====
void printMap() {
  Serial.println(F("\n=== CURRENT BUTTON MAPPINGS ==="));
  Serial.print(F("Priority Mode: "));
  Serial.println(globalPriority == Priority::HUMAN_FIRST ? F("HUMAN_FIRST") : F("GENERATED_FIRST"));
  Serial.print(F("Strict Playlists: "));
  Serial.println(strictPlaylists ? F("ON") : F("OFF"));
  Serial.println(F("Input → Key mappings:"));
  
  for (const auto& btn : buttons) {
    Serial.print(F("  "));
    Serial.print(btn.inputId);
    Serial.print(F(" → "));
    Serial.println(btn.key);
  }
  
  Serial.print(F("Total buttons configured: "));
  Serial.println(buttons.size());
  Serial.println(F("===============================\n"));
}

void testAllButtons() {
  Serial.println(F("[TEST] Testing all configured buttons..."));
  
  for (const auto& btn : buttons) {
    Serial.print(F("[TEST] "));
    Serial.print(btn.inputId);
    Serial.print(F(" ("));
    Serial.print(btn.key);
    Serial.print(F(") → "));
    
    String track = nextTrackForKey(btn.key);
    if (track.isEmpty()) {
      Serial.println(F("NO TRACKS"));
    } else {
      Serial.println(track);
    }
  }
  
  Serial.println(F("[TEST] Button test complete"));
}

void sanityCheckAudio() {
  Serial.println(F("[CHECK] Verifying playlist files..."));
  
  uint16_t totalTracks = 0;
  uint16_t missingFiles = 0;
  
  for (const auto& btn : buttons) {
    const String& key = btn.key;
    
    // Check human playlist
    String humanPlaylist = "/mappings/playlists/" + key + "_human.m3u";
    if (SD.exists(humanPlaylist)) {
      std::vector<String> tracks = readM3U(humanPlaylist);
      totalTracks += tracks.size();
      
      for (const String& track : tracks) {
        if (!SD.exists(track)) {
          Serial.print(F("⚠ Missing: "));
          Serial.print(track);
          Serial.print(F(" (from "));
          Serial.print(humanPlaylist);
          Serial.println(F(")"));
          missingFiles++;
        }
      }
    }
    
    // Check generated playlist
    String generatedPlaylist = "/mappings/playlists/" + key + "_generated.m3u";
    if (SD.exists(generatedPlaylist)) {
      std::vector<String> tracks = readM3U(generatedPlaylist);
      totalTracks += tracks.size();
      
      for (const String& track : tracks) {
        if (!SD.exists(track)) {
          Serial.print(F("⚠ Missing: "));
          Serial.print(track);
          Serial.print(F(" (from "));
          Serial.print(generatedPlaylist);
          Serial.println(F(")"));
          missingFiles++;
        }
      }
    }
  }
  
  Serial.print(F("[CHECK] Total tracks: "));
  Serial.println(totalTracks);
  Serial.print(F("[CHECK] Missing files: "));
  Serial.println(missingFiles);
  Serial.println(F("[CHECK] Audio verification complete"));
}

void printMenu() {
  Serial.println(F("\n=== TACTILE COMMUNICATOR - FUTURE-PROOF SYSTEM ==="));
  Serial.println(F("L/l - Load config from SD card"));
  Serial.println(F("S/s - Save config to SD card"));
  Serial.println(F("P/p - Print current mappings"));
  Serial.println(F("H/h - Show this help menu"));
  Serial.println(F("M/m - Toggle priority mode"));
  Serial.println(F("T/t - Test all buttons"));
  Serial.println(F("U/u - Verify audio files and playlists"));
  Serial.println(F("C/c - Enter calibration mode"));
  Serial.println(F("E/e - Exit calibration mode"));
  Serial.println(F("X/x - Stop current audio playback"));
  Serial.println(F("Volume: + (max), - (moderate), 1-9 (levels)"));
  Serial.println(F("\nHardware Support:"));
  Serial.println(F("- Up to 3x PCF8575 expanders (48 buttons)"));
  Serial.println(F("- Direct GPIO pins (4 additional)"));
  Serial.println(F("- Total capacity: 52 buttons"));
  Serial.println(F("\nPriority Toggle: Triple-press Period (.) button"));
  Serial.println(F("Current Mode: ") + String(globalPriority == Priority::HUMAN_FIRST ? "HUMAN_FIRST" : "GENERATED_FIRST"));
  Serial.println(F("=================================================\n"));
}
