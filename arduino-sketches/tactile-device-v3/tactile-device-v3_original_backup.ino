/*
 * Tactile Communication Device - VS1053 Version with Detailed Logging
 * 
 * This version uses the high-quality Adafruit VS1053 codec for superior audio
 * playback with PCF8575 I2C port expanders for 32+ button support.
 * 
 * Hardware Components:
 * - Arduino Uno/Nano with adequate I/O
 * - Adafruit VS1053 Codec Breakout or Shield
 * - 2x PCF8575 I2C port expanders (0x20, 0x21)
 * - MicroSD card (formatted as FAT32)
 * - 32+ tactile buttons
 * - Quality speaker/headphones
 * - Rechargeable battery pack
 * 
 * Audio Quality Benefits of VS1053:
 * - Superior DAC quality vs. DFPlayer Mini
 * - Reliable SD card handling
 * - Better volume control
 * - More file format support
 * - Hardware interrupt support for background playback
 * 
 * Console Logging Features:
 * - Detailed hardware initialization status
 * - Button press detection with chip/pin identification
 * - Audio playback status and file path logging
 * - Multi-press detection with timing info
 * - Configuration load/save confirmation
 * - Debug information for troubleshooting
 */

#include <SPI.h>
#include <SD.h>
#include <Wire.h>
#include <EEPROM.h>
#include "Adafruit_PCF8575.h"
#include "Adafruit_VS1053.h"

// VS1053 pins - using shield pin mapping (product 1788)
#define VS1053_RESET   -1     // VS1053 reset pin (tied high on shield)
#define VS1053_CS       7     // VS1053 xCS (shield pin mapping)
#define VS1053_DCS      6     // VS1053 xDCS (shield pin mapping)
#define CARDCS          4     // micro-SD CS (fixed trace on shield)
#define VS1053_DREQ     3     // VS1053 DREQ (INT1 on Uno)

Adafruit_VS1053_FilePlayer musicPlayer = 
  Adafruit_VS1053_FilePlayer(VS1053_RESET, VS1053_CS, VS1053_DCS, VS1053_DREQ, CARDCS);

// ===== Phase 0 Scaffolding: Generalized expander addressing and SD playlist feature flag =====
// Planned expander addresses (use 0x22 for the third expander per spec; update to match hardware)
static const uint8_t PCF_ADDR[] = { 0x20, 0x21, 0x22 };
static const uint8_t NUM_PCF = sizeof(PCF_ADDR) / sizeof(PCF_ADDR[0]);
static const uint16_t EXPANDER_BUTTONS = (uint16_t)NUM_PCF * 16;

// Phase 0.a: Computed total button constants (no more hardcoded 48 or 32)
static const uint8_t EXTRA_COUNT = 4; // Will be computed from extraPins array below
static const uint16_t TOTAL_EXPANDER_PINS = NUM_PCF * 16;
static const uint16_t TOTAL_BUTTONS = TOTAL_EXPANDER_PINS + EXTRA_COUNT;

// File system staging directory for file transfer operations
const String FS_STAGING_DIR = "/_staging";

// Feature switch for SD-defined, hardware-agnostic playlists (M2: enabled for playlist engine)
#ifndef FEATURE_SD_PLAYLISTS
#define FEATURE_SD_PLAYLISTS 1
#endif

#if FEATURE_SD_PLAYLISTS
// Priority mode and strict-playlists configuration (loaded from /config/mode.cfg)
enum class GlobalPriority : uint8_t { HUMAN_FIRST = 0, GENERATED_FIRST = 1 };

struct ModeCfg {
  GlobalPriority priority = GlobalPriority::HUMAN_FIRST;
  bool strictPlaylists = true; // STRICT_PLAYLISTS=1 by default when feature is enabled
};

static ModeCfg modeCfg; // Global configuration (not yet wired into runtime behavior in Phase 0)

// Stubs for Phase 0 (safe to compile; not invoked until a later phase)
static bool loadModeCfg() {
  File f = SD.open("/config/mode.cfg");
  if (!f) {
    // Use defaults
    return false;
  }
  String line;
  while (f.available()) {
    line = f.readStringUntil('\n');
    line.trim();
    if (line.length() == 0 || line[0] == '#') continue;
    int eq = line.indexOf('=');
    if (eq <= 0) continue;
    String key = line.substring(0, eq); key.trim();
    String val = line.substring(eq + 1); val.trim();
    if (key.equalsIgnoreCase("PRIORITY_MODE") || key.equalsIgnoreCase("PRIORITY")) {
      if (val.equalsIgnoreCase("HUMAN_FIRST")) modeCfg.priority = GlobalPriority::HUMAN_FIRST;
      else if (val.equalsIgnoreCase("GENERATED_FIRST")) modeCfg.priority = GlobalPriority::GENERATED_FIRST;
    } else if (key.equalsIgnoreCase("STRICT_PLAYLISTS")) {
      modeCfg.strictPlaylists = (val == "1" || val.equalsIgnoreCase("true"));
    }
  }
  f.close();
  return true;
}

static bool saveModeCfg() {
  // Minimal writer; will be fully integrated in later phases
  SD.remove("/config/mode.cfg");
  File f = SD.open("/config/mode.cfg", FILE_WRITE);
  if (!f) return false;
  f.println(F("# Tactile Communicator mode configuration"));
  f.print(F("PRIORITY_MODE="));
  f.println(modeCfg.priority == GlobalPriority::HUMAN_FIRST ? F("HUMAN_FIRST") : F("GENERATED_FIRST"));
  f.print(F("STRICT_PLAYLISTS="));
  f.println(modeCfg.strictPlaylists ? F("1") : F("0"));
  f.close();
  return true;
}
#endif // FEATURE_SD_PLAYLISTS

// PCF8575 I2C port expanders (now supporting up to 48 buttons)
Adafruit_PCF8575 pcf[NUM_PCF];

// Audio interruption support
volatile bool audioInterrupted = false;
volatile unsigned long lastAudioStart = 0;
const unsigned long MAX_AUDIO_LENGTH = 5000; // 5 second max per audio clip

// Extra Arduino pins for additional controls (avoid pins 0,1 for Serial)
const uint8_t extraPins[] = { 8,  9,  2,  5 };   // Safe pins: VS1053 uses pins 3,4,6,7
// EXTRA_COUNT now computed at compile time and used in TOTAL_BUTTONS above
static_assert(sizeof(extraPins) / sizeof(extraPins[0]) == EXTRA_COUNT, "EXTRA_COUNT mismatch with extraPins array");

// Button mapping structure (now just stores button labels)
struct MapEntry { 
  bool used; 
  char label[12];
};

MapEntry mapTab[TOTAL_BUTTONS];

// State for edge-detection
uint16_t last_s[NUM_PCF];
bool     lastExtra[EXTRA_COUNT];

// Button press timing for multi-press detection
unsigned long lastPressTime[TOTAL_BUTTONS];
uint8_t pressCount[TOTAL_BUTTONS];
const unsigned long MULTI_PRESS_WINDOW = 1000; // milliseconds (increased for better multi-press detection)

// Audio playback state
bool isPlaying = false;
String currentTrackPath = "";

// Calibration mode flag
bool inCalibrate = false;

// Debug logging control
bool debugMode = true;

// ===== PRIORITY MODE SYSTEM =====
// Two modes: HUMAN_FIRST (personal recordings first) or GENERATED_FIRST (TTS first)
// Using GlobalPriority enum defined above

const int EEPROM_ADDR_MODE = 0;  // EEPROM address to store mode (1 byte)
GlobalPriority currentMode = GlobalPriority::HUMAN_FIRST;

// Period triple-press detection for mode switching
static uint8_t periodPressCount = 0;
static unsigned long periodWindowStart = 0;
const unsigned long PERIOD_WINDOW_MS = 1200;  // 1.2 seconds to complete triple-press

// Enhanced two-bank audio mapping system for priority mode
// Each button can have separate folders for recorded and TTS audio
struct AudioMapping {
  char label[16];              // Button label (dynamic for SD loading)
  // Recorded bank (personal recordings)
  uint8_t recFolder; // Folder for recorded tracks
  uint8_t recBase;   // First recorded track number
  uint8_t recCount;  // How many recorded tracks
  // TTS bank (generated audio)
  uint8_t ttsFolder; // Folder for TTS tracks (can be different from recFolder)
  uint8_t ttsBase;   // First TTS track number
  uint8_t ttsCount;  // How many TTS tracks
  char fallbackLabel[16]; // Alternative label for TTS generation (dynamic)
};

// TWO-BANK PRIORITY SYSTEM
// Each button has separate ranges for recorded (REC) and TTS audio
// HUMAN_FIRST mode: recorded tracks first, then TTS
// GENERATED_FIRST mode: TTS tracks first, then recorded
//
// DETAILED BUTTON MAPPINGS:
AudioMapping audioMappings[] = {
  {"", /*recFolder*/1,/*recBase*/0,/*recCount*/0, /*ttsFolder*/1,/*ttsBase*/0,/*ttsCount*/0, ""}, // Index 0 - unused
  {"", /*recFolder*/1,/*recBase*/0,/*recCount*/0, /*ttsFolder*/1,/*ttsBase*/0,/*ttsCount*/0, ""}, // Index 1 - unused
  {"K", /*recFolder*/11,/*recBase*/1,/*recCount*/2, /*ttsFolder*/11,/*ttsBase*/3,/*ttsCount*/3, "Kiyah"}, // Index 2 -> K: REC=1-2(Kiyah,Kyan), TTS=3-5(Kaiser,Key...)
  {"A", /*recFolder*/1,/*recBase*/1,/*recCount*/3, /*ttsFolder*/1,/*ttsBase*/4,/*ttsCount*/3, "Alari"}, // Index 3 -> A: REC=1-3(Alari,Amer...), TTS=4-6(Apple,Arabic...)
  {"", /*recFolder*/1,/*recBase*/0,/*recCount*/0, /*ttsFolder*/1,/*ttsBase*/0,/*ttsCount*/0, ""}, // Index 4 - unused
  {"P", /*recFolder*/16,/*recBase*/1,/*recCount*/0, /*ttsFolder*/16,/*ttsBase*/1,/*ttsCount*/4, "Pain"}, // Index 5 -> P: TTS=1-4(Pain,Period...)
  {"C", /*recFolder*/3,/*recBase*/1,/*recCount*/0, /*ttsFolder*/3,/*ttsBase*/1,/*ttsCount*/7, "Call"}, // Index 6 -> C: TTS=1-7(Call,Car...)
  {"R", /*recFolder*/18,/*recBase*/1,/*recCount*/0, /*ttsFolder*/18,/*ttsBase*/1,/*ttsCount*/3, "Red"}, // Index 7 -> R: TTS=1-3(Red,Rest...)
  {"I", /*recFolder*/9,/*recBase*/1,/*recCount*/0, /*ttsFolder*/9,/*ttsBase*/1,/*ttsCount*/3, "Ice"}, // Index 8 -> I: TTS=1-3(Ice,Inside...)
  {"J", /*recFolder*/10,/*recBase*/1,/*recCount*/0, /*ttsFolder*/10,/*ttsBase*/1,/*ttsCount*/1, "Jump"}, // Index 9 -> J: TTS=1-1(Jump)
  {"Q", /*recFolder*/17,/*recBase*/1,/*recCount*/0, /*ttsFolder*/17,/*ttsBase*/1,/*ttsCount*/1, "Queen"}, // Index 10 -> Q: TTS=1-1(Queen)
  {"W", /*recFolder*/23,/*recBase*/1,/*recCount*/2, /*ttsFolder*/23,/*ttsBase*/3,/*ttsCount*/2, "Walker"}, // Index 11 -> W: REC=1-2(Walker,Wheelchair), TTS=3-4(Walk,Water)
  {"", /*recFolder*/1,/*recBase*/0,/*recCount*/0, /*ttsFolder*/1,/*ttsBase*/0,/*ttsCount*/0, ""}, // Index 12 - unused
  {"V", /*recFolder*/22,/*recBase*/1,/*recCount*/0, /*ttsFolder*/22,/*ttsBase*/1,/*ttsCount*/1, "Van"}, // Index 13 -> V: TTS=1-1(Van)
  {"X", /*recFolder*/24,/*recBase*/1,/*recCount*/0, /*ttsFolder*/24,/*ttsBase*/1,/*ttsCount*/1, "X-ray"}, // Index 14 -> X: TTS=1-1(X-ray)
  {"PERIOD", /*recFolder*/33,/*recBase*/0,/*recCount*/0, /*ttsFolder*/33,/*ttsBase*/1,/*ttsCount*/3, "period"}, // Index 15 -> PERIOD
  {"N", /*recFolder*/14,/*recBase*/1,/*recCount*/2, /*ttsFolder*/14,/*ttsBase*/3,/*ttsCount*/3, "Nadowie"}, // Index 16 -> N: REC=1-2(Nadowie,Noah), TTS=3-5(Nada,Net...)
  {"G", /*recFolder*/7,/*recBase*/1,/*recCount*/1, /*ttsFolder*/7,/*ttsBase*/2,/*ttsCount*/2, "Good Morning"}, // Index 17 -> G: REC=1-1(Good Morning), TTS=2-3(Garage,Go)
  {"F", /*recFolder*/6,/*recBase*/1,/*recCount*/0, /*ttsFolder*/6,/*ttsBase*/1,/*ttsCount*/3, "FaceTime"}, // Index 18 -> F: TTS=1-3(FaceTime,Fish...)
  {"", /*recFolder*/1,/*recBase*/0,/*recCount*/0, /*ttsFolder*/1,/*ttsBase*/0,/*ttsCount*/0, ""}, // Index 19 - unused
  {"", /*recFolder*/1,/*recBase*/0,/*recCount*/0, /*ttsFolder*/1,/*ttsBase*/0,/*ttsCount*/0, ""}, // Index 20 - unused
  {"U", /*recFolder*/21,/*recBase*/1,/*recCount*/1, /*ttsFolder*/21,/*ttsBase*/2,/*ttsCount*/1, "Urgent Care"}, // Index 21 -> U: REC=1-1(Urgent Care), TTS=2-2(Up)
  {"T", /*recFolder*/20,/*recBase*/1,/*recCount*/0, /*ttsFolder*/20,/*ttsBase*/1,/*ttsCount*/4, "Togamet"}, // Index 22 -> T: TTS=1-4(Togamet,Tree...)
  {"M", /*recFolder*/13,/*recBase*/1,/*recCount*/0, /*ttsFolder*/13,/*ttsBase*/1,/*ttsCount*/6, "Mad"}, // Index 23 -> M: TTS=1-6(Mad,Medical...)
  {"E", /*recFolder*/5,/*recBase*/1,/*recCount*/0, /*ttsFolder*/5,/*ttsBase*/1,/*ttsCount*/1, "Elephant"}, // Index 24 -> E: TTS=1-1(Elephant)
  {"", /*recFolder*/1,/*recBase*/0,/*recCount*/0, /*ttsFolder*/1,/*ttsBase*/0,/*ttsCount*/0, ""}, // Index 25 - unused
  {"", /*recFolder*/1,/*recBase*/0,/*recCount*/0, /*ttsFolder*/1,/*ttsBase*/0,/*ttsCount*/0, ""}, // Index 26 - unused
  {"SPACE", /*recFolder*/35,/*recBase*/0,/*recCount*/0, /*ttsFolder*/35,/*ttsBase*/1,/*ttsCount*/1, "space"}, // Index 27 -> SPACE
  {"Z", /*recFolder*/26,/*recBase*/1,/*recCount*/0, /*ttsFolder*/26,/*ttsBase*/1,/*ttsCount*/1, "Zebra"}, // Index 28 -> Z: TTS=1-1(Zebra)
  {"S", /*recFolder*/19,/*recBase*/1,/*recCount*/1, /*ttsFolder*/19,/*ttsBase*/2,/*ttsCount*/9, "Susu"}, // Index 29 -> S: REC=1-1(Susu), TTS=2-10(Sad,Scarf...)
  {"D", /*recFolder*/4,/*recBase*/1,/*recCount*/1, /*ttsFolder*/4,/*ttsBase*/2,/*ttsCount*/5, "Daddy"}, // Index 30 -> D: REC=1-1(Daddy), TTS=2-6(Deen,Doctor...)
  {"Y", /*recFolder*/25,/*recBase*/1,/*recCount*/0, /*ttsFolder*/25,/*ttsBase*/1,/*ttsCount*/2, "Yes"}, // Index 31 -> Y: TTS=1-2(Yes,Yellow)
  {"B", /*recFolder*/2,/*recBase*/1,/*recCount*/0, /*ttsFolder*/2,/*ttsBase*/1,/*ttsCount*/7, "Bagel"}, // Index 32 -> B: TTS=1-7(Bagel,Ball...)
  {"H", /*recFolder*/8,/*recBase*/1,/*recCount*/2, /*ttsFolder*/8,/*ttsBase*/3,/*ttsCount*/5, "Hello"}, // Index 33 -> H: REC=1-2(Hello,How are you), TTS=3-7(Happy,Heartburn...)
  {"", /*recFolder*/1,/*recBase*/0,/*recCount*/0, /*ttsFolder*/1,/*ttsBase*/0,/*ttsCount*/0, ""}, // Index 34 - unused
  {"O", /*recFolder*/15,/*recBase*/1,/*recCount*/0, /*ttsFolder*/15,/*ttsBase*/1,/*ttsCount*/2, "Orange"} // Index 35 -> O: TTS=1-2(Orange,Outside)
};

const uint8_t AUDIO_MAPPINGS_COUNT = sizeof(audioMappings) / sizeof(audioMappings[0]);

// ===== SD CARD CONFIGURATION SYSTEM =====
// Audio index for SD-based text mapping
struct AudioIndex {
  uint8_t folder;
  uint8_t track;
  char text[24];
  char bank[4]; // "REC" or "TTS"
};

// Dynamic arrays for SD-loaded configuration
AudioIndex* audioIndex = nullptr;
uint16_t audioIndexCount = 0;
AudioMapping* dynamicMappings = nullptr;
uint8_t dynamicMappingsCount = 0;
bool sdConfigLoaded = false;

// Forward declarations
void printMenu();
void printCalibrationInstructions();
void loadConfig();
void saveConfig();
void printMap();
void handlePress(uint8_t idx);
void initializeDefaultMappings();
void initializeHardwareMapping();

void playButtonAudioWithCount(const char* label, uint8_t pressCount);
void handleMultiPress();
void checkAudioStatus();
void testAllButtons();
bool hasValidMappings();
AudioMapping* findAudioByLabel(const char* label);

// ===== HARDWARE-DEPENDENT BUTTON MAPPING =====
// Maps physical button indices to their corresponding labels
struct HardwareButtonMapping {
  uint8_t hardwareIndex;
  char label[4];
};

// Dynamic hardware button mapping (loaded from SD card CONFIG.CSV)
HardwareButtonMapping* hardwareButtonMap = nullptr;
uint8_t HARDWARE_BUTTON_COUNT = 0;

// ===== M3U PLAYLIST SYSTEM =====
#ifdef FEATURE_SD_PLAYLISTS
// Playlist entry structure
struct PlaylistEntry {
  char path[64];  // SD card path to audio file
};

// Playlist structure for each key/bank combination
struct Playlist {
  PlaylistEntry* entries;
  uint8_t count;
  uint8_t cursor;  // Current playback position
  bool loaded;
};

// Playlist cache - one for each key and bank
// Keys are indexed by their string hash for efficient lookup
struct PlaylistCache {
  char key[16];           // Key name (A, WATER, PERIOD, etc.)
  Playlist humanPlaylist; // _human.m3u playlist
  Playlist generatedPlaylist; // _generated.m3u playlist
  bool valid;
};

#define MAX_CACHED_PLAYLISTS 32
PlaylistCache playlistCache[MAX_CACHED_PLAYLISTS];
uint8_t cachedPlaylistCount = 0;
#endif // FEATURE_SD_PLAYLISTS

// Function to get label from hardware button index
const char* getButtonLabel(uint8_t hardwareIndex) {
  // First check dynamic hardware mapping from SD card
  if (hardwareButtonMap != nullptr) {
    for (uint8_t i = 0; i < HARDWARE_BUTTON_COUNT; i++) {
      if (hardwareButtonMap[i].hardwareIndex == hardwareIndex) {
        return hardwareButtonMap[i].label;
      }
    }
  }
  
  // Fallback to mapTab for calibrated buttons
  if (hardwareIndex < TOTAL_BUTTONS && mapTab[hardwareIndex].used) {
    return mapTab[hardwareIndex].label;
  }
  
  return ""; // Return empty string for unmapped buttons
}

// Function to get audio mapping index from hardware button index
int8_t getAudioMappingIndex(uint8_t hardwareIndex) {
  const char* label = getButtonLabel(hardwareIndex);
  if (strlen(label) == 0) return -1; // No mapping found
  
  // Search through audioMappings for matching label
  for (uint8_t i = 0; i < AUDIO_MAPPINGS_COUNT; i++) {
    if (strcmp(audioMappings[i].label, label) == 0) {
      return i;
    }
  }
  return -1; // No audio mapping found for this label
}

// Parse PCF input string (pcf0:15) to hardware index
int parsePCFInput(String input) {
  input.trim();
  if (!input.startsWith("pcf")) return -1;
  
  int colonPos = input.indexOf(':');
  if (colonPos < 4) return -1;
  
  int pcfNum = input.substring(3, colonPos).toInt();
  int pinNum = input.substring(colonPos + 1).toInt();
  
  if (pcfNum < 0 || pcfNum >= NUM_PCF || pinNum < 0 || pinNum > 15) {
    return -1;
  }
  
  return (pcfNum * 16) + pinNum;
}

// Parse GPIO input string (gpio:8) to hardware index  
int parseGPIOInput(String input) {
  input.trim();
  if (!input.startsWith("gpio:")) return -1;
  
  int pinNum = input.substring(5).toInt();
  // GPIO pins are mapped after PCF expander pins
  return TOTAL_EXPANDER_PINS + pinNum;
}

// Load hardware button mapping from strict mode buttons.csv
bool loadHardwareMapping() {
  // Try strict mode first
  File cfg = SD.open("/config/buttons.csv");
  if (!cfg) {
    // Fallback to legacy CONFIG.CSV
    cfg = SD.open("CONFIG.CSV");
    if (!cfg) {
      Serial.println(F("[CONFIG] No buttons.csv or CONFIG.CSV found - using calibration mode"));
      return false;
    }
    Serial.println(F("[CONFIG] Using legacy CONFIG.CSV format"));
    return loadLegacyConfig(cfg);
  }
  
  Serial.println(F("[CONFIG] Loading strict mode buttons.csv"));
  
  // Count valid entries (skip comments and header)
  HARDWARE_BUTTON_COUNT = 0;
  String line;
  bool foundHeader = false;
  
  while (cfg.available()) {
    line = cfg.readStringUntil('\n');
    line.trim();
    
    // Skip empty lines and comments
    if (line.length() == 0 || line.startsWith("#")) continue;
    
    // Check for header
    if (!foundHeader && line.startsWith("INPUT,KEY")) {
      foundHeader = true;
      continue;
    }
    
    // Count valid data lines
    if (foundHeader && line.indexOf(',') > 0) {
      HARDWARE_BUTTON_COUNT++;
    }
  }
  cfg.close();
  
  if (HARDWARE_BUTTON_COUNT == 0) {
    Serial.println(F("[CONFIG] No valid entries found in buttons.csv"));
    return false;
  }
  
  // Allocate memory for hardware mappings
  hardwareButtonMap = (HardwareButtonMapping*)malloc(HARDWARE_BUTTON_COUNT * sizeof(HardwareButtonMapping));
  if (!hardwareButtonMap) {
    Serial.println(F("[CONFIG] Failed to allocate memory for hardware mappings"));
    HARDWARE_BUTTON_COUNT = 0;
    return false;
  }
  
  // Load the mappings
  cfg = SD.open("/config/buttons.csv");
  foundHeader = false;
  uint8_t idx = 0;
  
  while (cfg.available() && idx < HARDWARE_BUTTON_COUNT) {
    line = cfg.readStringUntil('\n');
    line.trim();
    
    // Skip empty lines and comments
    if (line.length() == 0 || line.startsWith("#")) continue;
    
    // Skip header
    if (!foundHeader && line.startsWith("INPUT,KEY")) {
      foundHeader = true;
      continue;
    }
    
    if (foundHeader && line.length() > 3) {
      int comma = line.indexOf(',');
      if (comma > 0) {
        String inputStr = line.substring(0, comma);
        String keyStr = line.substring(comma + 1);
        inputStr.trim();
        keyStr.trim();
        
        // Parse input to hardware index
        int hwIndex = -1;
        if (inputStr.startsWith("pcf")) {
          hwIndex = parsePCFInput(inputStr);
        } else if (inputStr.startsWith("gpio:")) {
          hwIndex = parseGPIOInput(inputStr);
        }
        
        if (hwIndex >= 0 && hwIndex < TOTAL_BUTTONS && keyStr.length() > 0) {
          hardwareButtonMap[idx].hardwareIndex = hwIndex;
          strncpy(hardwareButtonMap[idx].label, keyStr.c_str(), sizeof(hardwareButtonMap[idx].label) - 1);
          hardwareButtonMap[idx].label[sizeof(hardwareButtonMap[idx].label) - 1] = '\0';
          
          Serial.print(F("[CONFIG] Mapped "));
          Serial.print(inputStr);
          Serial.print(F(" (hw:"));
          Serial.print(hwIndex);
          Serial.print(F(") -> "));
          Serial.println(keyStr);
          
          idx++;
        } else {
          Serial.print(F("[CONFIG] Invalid mapping: "));
          Serial.print(inputStr);
          Serial.print(F(" -> "));
          Serial.println(keyStr);
        }
      }
    }
  }
  cfg.close();
  
  HARDWARE_BUTTON_COUNT = idx; // Update to actual loaded count
  
  Serial.print(F("[CONFIG] Loaded "));
  Serial.print(HARDWARE_BUTTON_COUNT);
  Serial.println(F(" hardware button mappings from buttons.csv"));
  
  return true;
}

// Legacy CONFIG.CSV loader (index,label format)
bool loadLegacyConfig(File cfg) {
  // Count entries first (skip header)
  HARDWARE_BUTTON_COUNT = 0;
  String line = cfg.readStringUntil('\n'); // Skip header
  while (cfg.available()) {
    line = cfg.readStringUntil('\n');
    line.trim();
    if (line.length() > 3 && line.indexOf(',') > 0) {
      HARDWARE_BUTTON_COUNT++;
    }
  }
  cfg.close();
  
  if (HARDWARE_BUTTON_COUNT == 0) {
    Serial.println(F("[CONFIG] No valid entries found in legacy CONFIG.CSV"));
    return false;
  }
  
  // Allocate memory for hardware mappings
  hardwareButtonMap = (HardwareButtonMapping*)malloc(HARDWARE_BUTTON_COUNT * sizeof(HardwareButtonMapping));
  if (!hardwareButtonMap) {
    Serial.println(F("[CONFIG] Failed to allocate memory for hardware mappings"));
    HARDWARE_BUTTON_COUNT = 0;
    return false;
  }
  
  // Load the mappings
  cfg = SD.open("CONFIG.CSV");
  cfg.readStringUntil('\n'); // Skip header
  uint8_t idx = 0;
  
  while (cfg.available() && idx < HARDWARE_BUTTON_COUNT) {
    line = cfg.readStringUntil('\n');
    line.trim();
    
    if (line.length() > 3) {
      int comma = line.indexOf(',');
      if (comma > 0) {
        uint8_t hwIndex = line.substring(0, comma).toInt();
        String label = line.substring(comma + 1);
        label.trim();
        
        if (hwIndex < TOTAL_BUTTONS && label.length() > 0) {
          hardwareButtonMap[idx].hardwareIndex = hwIndex;
          strncpy(hardwareButtonMap[idx].label, label.c_str(), sizeof(hardwareButtonMap[idx].label) - 1);
          hardwareButtonMap[idx].label[sizeof(hardwareButtonMap[idx].label) - 1] = '\0';
          idx++;
        }
      }
    }
  }
  cfg.close();
  
  HARDWARE_BUTTON_COUNT = idx; // Update to actual loaded count
  
  Serial.print(F("[CONFIG] Loaded "));
  Serial.print(HARDWARE_BUTTON_COUNT);
  Serial.println(F(" hardware button mappings from legacy CONFIG.CSV"));
  
  return true;
}

// ===== M3U PLAYLIST ENGINE =====
#ifdef FEATURE_SD_PLAYLISTS

// Forward declarations for playlist functions
PlaylistCache* getPlaylistCache(const char* key);
bool loadPlaylist(Playlist* playlist, const char* key, bool isHuman);
const char* getNextTrack(const char* key, bool humanFirst);

// Playlist function implementations
PlaylistCache* getPlaylistCache(const char* key) {
  // Check if already in cache
  for (uint8_t i = 0; i < cachedPlaylistCount; i++) {
    if (strcmp(playlistCache[i].key, key) == 0 && playlistCache[i].valid) {
      return &playlistCache[i];
    }
  }
  
  // Not in cache, create new entry if there's room
  if (cachedPlaylistCount < MAX_CACHED_PLAYLISTS) {
    PlaylistCache* cache = &playlistCache[cachedPlaylistCount];
    strncpy(cache->key, key, sizeof(cache->key) - 1);
    cache->key[sizeof(cache->key) - 1] = '\0';
    cache->humanPlaylist.entries = nullptr;
    cache->humanPlaylist.count = 0;
    cache->humanPlaylist.cursor = 0;
    cache->humanPlaylist.loaded = false;
    cache->generatedPlaylist.entries = nullptr;
    cache->generatedPlaylist.count = 0;
    cache->generatedPlaylist.cursor = 0;
    cache->generatedPlaylist.loaded = false;
    cache->valid = true;
    cachedPlaylistCount++;
    return cache;
  }
  
  // Cache full, clear oldest entry and reuse
  if (cachedPlaylistCount > 0) {
    // Free memory for the first entry
    if (playlistCache[0].humanPlaylist.entries) {
      free(playlistCache[0].humanPlaylist.entries);
      playlistCache[0].humanPlaylist.entries = nullptr;
    }
    if (playlistCache[0].generatedPlaylist.entries) {
      free(playlistCache[0].generatedPlaylist.entries);
      playlistCache[0].generatedPlaylist.entries = nullptr;
    }
    
    // Shift all entries down by one
    for (uint8_t i = 0; i < cachedPlaylistCount - 1; i++) {
      memcpy(&playlistCache[i], &playlistCache[i+1], sizeof(PlaylistCache));
    }
    
    // Use the last slot for our new entry
    PlaylistCache* cache = &playlistCache[cachedPlaylistCount - 1];
    strncpy(cache->key, key, sizeof(cache->key) - 1);
    cache->key[sizeof(cache->key) - 1] = '\0';
    cache->humanPlaylist.entries = nullptr;
    cache->humanPlaylist.count = 0;
    cache->humanPlaylist.cursor = 0;
    cache->humanPlaylist.loaded = false;
    cache->generatedPlaylist.entries = nullptr;
    cache->generatedPlaylist.count = 0;
    cache->generatedPlaylist.cursor = 0;
    cache->generatedPlaylist.loaded = false;
    cache->valid = true;
    return cache;
  }
  
  return nullptr; // Should never reach here if MAX_CACHED_PLAYLISTS > 0
}

bool loadPlaylist(Playlist* playlist, const char* key, bool isHuman) {
  // Form the playlist filename: /mappings/playlists/{key}_human.m3u or {key}_generated.m3u
  char playlistPath[80];
  snprintf(playlistPath, sizeof(playlistPath), 
           "/mappings/playlists/%s_%s.m3u", 
           key, 
           isHuman ? "human" : "generated");
  
  // Clear previous entries if any
  if (playlist->entries) {
    free(playlist->entries);
    playlist->entries = nullptr;
  }
  playlist->count = 0;
  playlist->cursor = 0;
  playlist->loaded = false;
  
  // Open playlist file
  File f = SD.open(playlistPath);
  if (!f) {
    Serial.print(F("[PLAYLIST] File not found: "));
    Serial.println(playlistPath);
    return false;
  }
  
  // First pass: count valid entries
  uint8_t entryCount = 0;
  String line;
  while (f.available()) {
    line = f.readStringUntil('\n');
    line.trim();
    if (line.length() > 0 && !line.startsWith("#")) {
      entryCount++;
    }
  }
  f.close();
  
  if (entryCount == 0) {
    Serial.print(F("[PLAYLIST] No valid entries in "));
    Serial.println(playlistPath);
    return false;
  }
  
  // Allocate memory for entries
  playlist->entries = (PlaylistEntry*)malloc(entryCount * sizeof(PlaylistEntry));
  if (!playlist->entries) {
    Serial.println(F("[PLAYLIST] Memory allocation failed"));
    return false;
  }
  
  // Second pass: load entries
  f = SD.open(playlistPath);
  uint8_t idx = 0;
  while (f.available() && idx < entryCount) {
    line = f.readStringUntil('\n');
    line.trim();
    if (line.length() > 0 && !line.startsWith("#")) {
      strncpy(playlist->entries[idx].path, line.c_str(), sizeof(playlist->entries[idx].path) - 1);
      playlist->entries[idx].path[sizeof(playlist->entries[idx].path) - 1] = '\0';
      idx++;
    }
  }
  f.close();
  
  playlist->count = idx;
  playlist->cursor = 0;
  playlist->loaded = true;
  
  Serial.print(F("[PLAYLIST] Loaded "));
  Serial.print(playlist->count);
  Serial.print(F(" entries from "));
  Serial.println(playlistPath);
  
  return true;
}

const char* getNextTrack(const char* key, bool humanFirst) {
  // Get or create playlist cache for this key
  PlaylistCache* cache = getPlaylistCache(key);
  if (!cache) {
    Serial.println(F("[PLAYLIST] Failed to get playlist cache"));
    return nullptr;
  }
  
  // Load playlists if needed
  bool humanLoaded = cache->humanPlaylist.loaded;
  bool genLoaded = cache->generatedPlaylist.loaded;
  
  if (!humanLoaded) {
    humanLoaded = loadPlaylist(&cache->humanPlaylist, key, true);
  }
  
  if (!genLoaded) {
    genLoaded = loadPlaylist(&cache->generatedPlaylist, key, false);
  }
  
  if (!humanLoaded && !genLoaded) {
    Serial.println(F("[PLAYLIST] No playlists available"));
    return nullptr;
  }
  
  // Determine which playlist to use first based on priority mode
  Playlist* firstPlaylist = humanFirst ? 
    (humanLoaded ? &cache->humanPlaylist : &cache->generatedPlaylist) : 
    (genLoaded ? &cache->generatedPlaylist : &cache->humanPlaylist);
  
  Playlist* secondPlaylist = humanFirst ? 
    (genLoaded ? &cache->generatedPlaylist : nullptr) : 
    (humanLoaded ? &cache->humanPlaylist : nullptr);
  
  // Try first playlist
  if (firstPlaylist && firstPlaylist->count > 0) {
    // Get track at current cursor position
    const char* track = firstPlaylist->entries[firstPlaylist->cursor].path;
    
    // Increment cursor for next time, wrapping around if needed
    firstPlaylist->cursor = (firstPlaylist->cursor + 1) % firstPlaylist->count;
    
    return track;
  }
  
  // If first playlist empty or exhausted, try second playlist
  if (secondPlaylist && secondPlaylist->count > 0) {
    const char* track = secondPlaylist->entries[secondPlaylist->cursor].path;
    secondPlaylist->cursor = (secondPlaylist->cursor + 1) % secondPlaylist->count;
    return track;
  }
  
  return nullptr; // No tracks available
}
#endif // FEATURE_SD_PLAYLISTS

void clearPlaylistCache() {
  for (uint8_t i = 0; i < cachedPlaylistCount; i++) {
    if (playlistCache[i].humanPlaylist.entries) {
      free(playlistCache[i].humanPlaylist.entries);
      playlistCache[i].humanPlaylist.entries = nullptr;
    }
    if (playlistCache[i].generatedPlaylist.entries) {
      free(playlistCache[i].generatedPlaylist.entries);
      playlistCache[i].generatedPlaylist.entries = nullptr;
    }
    playlistCache[i].valid = false;
  }
  cachedPlaylistCount = 0;
  Serial.println(F("[PLAYLIST] Cache cleared"));
}

// ===== CRC32 CALCULATION =====

// CRC32 lookup table
static const uint32_t crc32_table[256] PROGMEM = {
  0x00000000, 0x77073096, 0xee0e612c, 0x990951ba, 0x076dc419, 0x706af48f,
  0xe963a535, 0x9e6495a3, 0x0edb8832, 0x79dcb8a4, 0xe0d5e91e, 0x97d2d988,
  0x09b64c2b, 0x7eb17cbd, 0xe7b82d07, 0x90bf1d91, 0x1db71064, 0x6ab020f2,
  0xf3b97148, 0x84be41de, 0x1adad47d, 0x6ddde4eb, 0xf4d4b551, 0x83d385c7,
  0x136c9856, 0x646ba8c0, 0xfd62f97a, 0x8a65c9ec, 0x14015c4f, 0x63066cd9,
  0xfa0f3d63, 0x8d080df5, 0x3b6e20c8, 0x4c69105e, 0xd56041e4, 0xa2677172,
  0x3c03e4d1, 0x4b04d447, 0xd20d85fd, 0xa50ab56b, 0x35b5a8fa, 0x42b2986c,
  0xdbbbc9d6, 0xacbcf940, 0x32d86ce3, 0x45df5c75, 0xdcd60dcf, 0xabd13d59,
  0x26d930ac, 0x51de003a, 0xc8d75180, 0xbfd06116, 0x21b4f4b5, 0x56b3c423,
  0xcfba9599, 0xb8bda50f, 0x2802b89e, 0x5f058808, 0xc60cd9b2, 0xb10be924,
  0x2f6f7c87, 0x58684c11, 0xc1611dab, 0xb6662d3d, 0x76dc4190, 0x01db7106,
  0x98d220bc, 0xefd5102a, 0x71b18589, 0x06b6b51f, 0x9fbfe4a5, 0xe8b8d433,
  0x7807c9a2, 0x0f00f934, 0x9609a88e, 0xe10e9818, 0x7f6a0dbb, 0x086d3d2d,
  0x91646c97, 0xe6635c01, 0x6b6b51f4, 0x1c6c6162, 0x856530d8, 0xf262004e,
  0x6c0695ed, 0x1b01a57b, 0x8208f4c1, 0xf50fc457, 0x65b0d9c6, 0x12b7e950,
  0x8bbeb8ea, 0xfcb9887c, 0x62dd1ddf, 0x15da2d49, 0x8cd37cf3, 0xfbd44c65,
  0x4db26158, 0x3ab551ce, 0xa3bc0074, 0xd4bb30e2, 0x4adfa541, 0x3dd895d7,
  0xa4d1c46d, 0xd3d6f4fb, 0x4369e96a, 0x346ed9fc, 0xad678846, 0xda60b8d0,
  0x44042d73, 0x33031de5, 0xaa0a4c5f, 0xdd0d7cc9, 0x5005713c, 0x270241aa,
  0xbe0b1010, 0xc90c2086, 0x5768b525, 0x206f85b3, 0xb966d409, 0xce61e49f,
  0x5edef90e, 0x29d9c998, 0xb0d09822, 0xc7d7a8b4, 0x59b33d17, 0x2eb40d81,
  0xb7bd5c3b, 0xc0ba6cad, 0xedb88320, 0x9abfb3b6, 0x03b6e20c, 0x74b1d29a,
  0xead54739, 0x9dd277af, 0x04db2615, 0x73dc1683, 0xe3630b12, 0x94643b84,
  0x0d6d6a3e, 0x7a6a5aa8, 0xe40ecf0b, 0x9309ff9d, 0x0a00ae27, 0x7d079eb1,
  0xf00f9344, 0x8708a3d2, 0x1e01f268, 0x6906c2fe, 0xf762575d, 0x806567cb,
  0x196c3671, 0x6e6b06e7, 0xfed41b76, 0x89d32be0, 0x10da7a5a, 0x67dd4acc,
  0xf9b9df6f, 0x8ebeeff9, 0x17b7be43, 0x60b08ed5, 0xd6d6a3e8, 0xa1d1937e,
  0x38d8c2c4, 0x4fdff252, 0xd1bb67f1, 0xa6bc5767, 0x3fb506dd, 0x48b2364b,
  0xd80d2bda, 0xaf0a1b4c, 0x36034af6, 0x41047a60, 0xdf60efc3, 0xa867df55,
  0x316e8eef, 0x4669be79, 0xcb61b38c, 0xbc66831a, 0x256fd2a0, 0x5268e236,
  0xcc0c7795, 0xbb0b4703, 0x220216b9, 0x5505262f, 0xc5ba3bbe, 0xb2bd0b28,
  0x2bb45a92, 0x5cb36a04, 0xc2d7ffa7, 0xb5d0cf31, 0x2cd99e8b, 0x5bdeae1d,
  0x9b64c2b0, 0xec63f226, 0x756aa39c, 0x026d930a, 0x9c0906a9, 0xeb0e363f,
  0x72076785, 0x05005713, 0x95bf4a82, 0xe2b87a14, 0x7bb12bae, 0x0cb61b38,
  0x92d28e9b, 0xe5d5be0d, 0x7cdcefb7, 0x0bdbdf21, 0x86d3d2d4, 0xf1d4e242,
  0x68ddb3f8, 0x1fda836e, 0x81be16cd, 0xf6b9265b, 0x6fb077e1, 0x18b74777,
  0x88085ae6, 0xff0f6a70, 0x66063bca, 0x11010b5c, 0x8f659eff, 0xf862ae69,
  0x616bffd3, 0x166ccf45, 0xa00ae278, 0xd70dd2ee, 0x4e048354, 0x3903b3c2,
  0xa7672661, 0xd06016f7, 0x4969474d, 0x3e6e77db, 0xaed16a4a, 0xd9d65adc,
  0x40df0b66, 0x37d83bf0, 0xa9bcae53, 0xdebb9ec5, 0x47b2cf7f, 0x30b5ffe9,
  0xbdbdf21c, 0xcabac28a, 0x53b39330, 0x24b4a3a6, 0xbad03605, 0xcdd70693,
  0x54de5729, 0x23d967bf, 0xb3667a2e, 0xc4614ab8, 0x5d681b02, 0x2a6f2b94,
  0xb40bbe37, 0xc30c8ea1, 0x5a05df1b, 0x2d02ef8d
};

// Calculate CRC32 for data buffer
uint32_t calculateCRC32(const uint8_t* data, size_t length) {
  uint32_t crc = 0xFFFFFFFF;
  for (size_t i = 0; i < length; i++) {
    uint8_t byte = data[i];
    uint8_t tbl_idx = (crc ^ byte) & 0xFF;
    crc = (crc >> 8) ^ pgm_read_dword(&crc32_table[tbl_idx]);
  }
  return crc ^ 0xFFFFFFFF;
}

// ===== SERIAL FS PROTOCOL (M4) =====
// Atomic SD card update protocol for desktop app integration

#define FS_MAX_CHUNK_SIZE 512
#define FS_MAX_PATH_LENGTH 64
#define FS_MAX_FILES 64

enum FSState {
  FS_IDLE,
  FS_RECEIVING_MANIFEST,
  FS_RECEIVING_FILE,
  FS_COMMITTING,
  FS_MAINTENANCE_MODE
};

struct FSFileInfo {
  char path[FS_MAX_PATH_LENGTH];
  uint32_t size;
  uint32_t crc32;
  uint32_t receivedBytes;
  bool completed;
};

struct FSSession {
  FSState state;
  uint16_t totalFiles;
  uint32_t totalBytes;
  uint32_t manifestCrc32;
  FSFileInfo files[FS_MAX_FILES];
  uint16_t currentFileIndex;
  File currentFile;
  uint32_t sessionCrc32;
  bool maintenanceMode;
};

FSSession fsSession;

// Initialize FS session
void initFSSession() {
  fsSession.state = FS_IDLE;
  fsSession.totalFiles = 0;
  fsSession.totalBytes = 0;
  fsSession.manifestCrc32 = 0;
  fsSession.currentFileIndex = 0;
  fsSession.sessionCrc32 = 0;
  fsSession.maintenanceMode = false;
  
  // Create staging directory if it doesn't exist
  if (!SD.exists(FS_STAGING_DIR)) {
    SD.mkdir(FS_STAGING_DIR);
  }
  
  for (uint16_t i = 0; i < FS_MAX_FILES; i++) {
    memset(fsSession.files[i].path, 0, FS_MAX_PATH_LENGTH);
    fsSession.files[i].size = 0;
    fsSession.files[i].crc32 = 0;
    fsSession.files[i].receivedBytes = 0;
    fsSession.files[i].completed = false;
  }
  
  if (fsSession.currentFile) {
    fsSession.currentFile.close();
  }
}

// Clean staging directory
void cleanStagingDirectory() {
  if (SD.exists("/_staging")) {
    // Remove all files in staging (simplified - would need recursive delete in production)
    Serial.println(F("[FS] Cleaning staging directory"));
    SD.rmdir("/_staging");
  }
  SD.mkdir("/_staging");
}

// Process FS commands
void processFSCommand(String command) {
  command.trim();
  
  if (command.startsWith("FS_BEGIN ")) {
    // FS_BEGIN <files> <totalBytes> <manifestCrc32>
    int space1 = command.indexOf(' ', 9);
    int space2 = command.indexOf(' ', space1 + 1);
    
    if (space1 > 0 && space2 > 0) {
      fsSession.totalFiles = command.substring(9, space1).toInt();
      fsSession.totalBytes = command.substring(space1 + 1, space2).toInt();
      fsSession.manifestCrc32 = strtoul(command.substring(space2 + 1).c_str(), NULL, 16);
      
      if (fsSession.totalFiles <= FS_MAX_FILES) {
        initFSSession();
        cleanStagingDirectory();
        fsSession.state = FS_RECEIVING_MANIFEST;
        fsSession.maintenanceMode = true;
        
        Serial.println(F("[FS] OK"));
        Serial.print(F("[FS] Ready for "));
        Serial.print(fsSession.totalFiles);
        Serial.print(F(" files, "));
        Serial.print(fsSession.totalBytes);
        Serial.println(F(" bytes"));
      } else {
        Serial.println(F("[FS] ERROR: Too many files"));
      }
    } else {
      Serial.println(F("[FS] ERROR: Invalid FS_BEGIN format"));
    }
  }
  else if (command.startsWith("FS_PUT ")) {
    // FS_PUT <path> <size> <crc32>
    if (fsSession.state != FS_RECEIVING_MANIFEST && fsSession.state != FS_RECEIVING_FILE) {
      Serial.println(F("[FS] ERROR: Not in file receiving state"));
      return;
    }
    
    int space1 = command.indexOf(' ', 7);
    int space2 = command.indexOf(' ', space1 + 1);
    
    if (space1 > 0 && space2 > 0 && fsSession.currentFileIndex < fsSession.totalFiles) {
      String path = command.substring(7, space1);
      uint32_t size = command.substring(space1 + 1, space2).toInt();
      uint32_t crc32 = strtoul(command.substring(space2 + 1).c_str(), NULL, 16);
      
      // Store file info
      strncpy(fsSession.files[fsSession.currentFileIndex].path, path.c_str(), FS_MAX_PATH_LENGTH - 1);
      fsSession.files[fsSession.currentFileIndex].size = size;
      fsSession.files[fsSession.currentFileIndex].crc32 = crc32;
      fsSession.files[fsSession.currentFileIndex].receivedBytes = 0;
      fsSession.files[fsSession.currentFileIndex].completed = false;
      
      // Create staging file path
      String stagingPath = "/_staging" + path;
      
      // Ensure directory exists
      int lastSlash = stagingPath.lastIndexOf('/');
      if (lastSlash > 0) {
        String dir = stagingPath.substring(0, lastSlash);
        // Create directory if needed (simplified)
      }
      
      // Open file for writing
      if (fsSession.currentFile) fsSession.currentFile.close();
      fsSession.currentFile = SD.open(stagingPath.c_str(), FILE_WRITE);
      
      if (fsSession.currentFile) {
        fsSession.state = FS_RECEIVING_FILE;
        Serial.println(F("[FS] OK"));
        Serial.print(F("[FS] Ready for file: "));
        Serial.println(path);
      } else {
        Serial.println(F("[FS] ERROR: Cannot create staging file"));
      }
    } else {
      Serial.println(F("[FS] ERROR: Invalid FS_PUT format"));
    }
  }
  else if (command.startsWith("FS_DATA ")) {
    // FS_DATA <n> followed by n bytes of binary data
    if (fsSession.state != FS_RECEIVING_FILE) {
      Serial.println(F("[FS] ERROR: Not in file receiving state"));
      return;
    }
    
    uint16_t dataSize = command.substring(8).toInt();
    if (dataSize > 0 && dataSize <= FS_MAX_CHUNK_SIZE) {
      Serial.println(F("[FS] READY")); // Signal ready for binary data
      
      // Read binary data
      uint8_t buffer[FS_MAX_CHUNK_SIZE];
      uint16_t bytesRead = 0;
      unsigned long timeout = millis() + 5000; // 5 second timeout
      
      while (bytesRead < dataSize && millis() < timeout) {
        if (Serial.available()) {
          buffer[bytesRead++] = Serial.read();
        }
      }
      
      if (bytesRead == dataSize) {
        // Write to file
        size_t written = fsSession.currentFile.write(buffer, bytesRead);
        fsSession.currentFile.flush();
        
        if (written == bytesRead) {
          fsSession.files[fsSession.currentFileIndex].receivedBytes += bytesRead;
          Serial.println(F("[FS] OK"));
        } else {
          Serial.println(F("[FS] ERROR: Write failed"));
        }
      } else {
        Serial.println(F("[FS] ERROR: Data timeout"));
      }
    } else {
      Serial.println(F("[FS] ERROR: Invalid data size"));
    }
  }
  else if (command == "FS_DONE") {
    // Finish current file and verify CRC
    if (fsSession.state != FS_RECEIVING_FILE) {
      Serial.println(F("[FS] ERROR: Not in file receiving state"));
      return;
    }
    
    fsSession.currentFile.close();
    
    // Verify file size and CRC (simplified - would implement full CRC check)
    FSFileInfo& fileInfo = fsSession.files[fsSession.currentFileIndex];
    if (fileInfo.receivedBytes == fileInfo.size) {
      fileInfo.completed = true;
      fsSession.currentFileIndex++;
      
      Serial.println(F("[FS] OK"));
      Serial.print(F("[FS] File completed: "));
      Serial.println(fileInfo.path);
      
      if (fsSession.currentFileIndex >= fsSession.totalFiles) {
        fsSession.state = FS_COMMITTING;
        Serial.println(F("[FS] All files received, ready for commit"));
      } else {
        fsSession.state = FS_RECEIVING_MANIFEST;
      }
    } else {
      Serial.println(F("[FS] ERROR: File size mismatch"));
    }
  }
  else if (command == "FS_COMMIT") {
    // Atomically move files from staging to final locations
    if (fsSession.state != FS_COMMITTING) {
      Serial.println(F("[FS] ERROR: Not ready for commit"));
      return;
    }
    
    Serial.println(F("[FS] Committing files..."));
    
    bool success = true;
    for (uint16_t i = 0; i < fsSession.currentFileIndex; i++) {
      if (fsSession.files[i].completed) {
        String stagingPath = "/_staging" + String(fsSession.files[i].path);
        String finalPath = fsSession.files[i].path;
        
        // Remove existing file
        if (SD.exists(finalPath.c_str())) {
          SD.remove(finalPath.c_str());
        }
        
        // Move from staging (simplified - would use proper atomic move)
        File src = SD.open(stagingPath.c_str());
        File dst = SD.open(finalPath.c_str(), FILE_WRITE);
        
        if (src && dst) {
          while (src.available()) {
            dst.write(src.read());
          }
          src.close();
          dst.close();
          SD.remove(stagingPath.c_str());
        } else {
          success = false;
          break;
        }
      }
    }
    
    if (success) {
      cleanStagingDirectory();
      initFSSession();
      Serial.println(F("[FS] OK"));
      Serial.println(F("[FS] Commit successful"));
    } else {
      Serial.println(F("[FS] ERROR: Commit failed"));
    }
  }
  else if (command == "FS_ABORT") {
    // Abort current session and clean up
    cleanStagingDirectory();
    initFSSession();
    Serial.println(F("[FS] OK"));
    Serial.println(F("[FS] Session aborted"));
  }
  else if (command == "CFG_RELOAD") {
    // Reload configuration without reboot
#ifdef FEATURE_SD_PLAYLISTS
    clearPlaylistCache();
    loadModeCfg();
#endif
    initializeHardwareMapping();
    Serial.println(F("[FS] OK"));
    Serial.println(F("[FS] Configuration reloaded"));
  }
  else if (command == "GET_INFO") {
    // Return device information
    Serial.println(F("[FS] OK"));
    Serial.println(F("[INFO] Device: Tactile Communication Device"));
    Serial.println(F("[INFO] Firmware: v2.0 M1+M2+M4"));
    Serial.print(F("[INFO] Free space: "));
    // Would implement SD card free space check
    Serial.println(F("Unknown"));
    Serial.print(F("[INFO] Priority: "));
#ifdef FEATURE_SD_PLAYLISTS
    Serial.println(modeCfg.priority == GlobalPriority::HUMAN_FIRST ? F("HUMAN_FIRST") : F("GENERATED_FIRST"));
    Serial.print(F("[INFO] Strict playlists: "));
    Serial.println(modeCfg.strictPlaylists ? F("ON") : F("OFF"));
#else
    Serial.println(F("Legacy mode"));
#endif
  }
  else {
    Serial.println(F("[FS] ERROR: Unknown command"));
  }
}

void setup() {
  Serial.begin(115200);
  while (!Serial && millis() < 3000); // Wait up to 3 seconds for Serial

  Serial.println(F("\n=================================================="));
  Serial.println(F("    TACTILE COMMUNICATION DEVICE - VS1053"));
  Serial.println(F("     Enhanced with Priority Mode System"));
  Serial.println(F("=================================================="));
  Serial.println(F("[INIT] Starting hardware initialization..."));
  
  // Initialize priority mode system
  loadPriorityMode();

  // Initialize all timing arrays
  Serial.println(F("[INIT] Initializing button timing arrays..."));
  for (uint16_t i = 0; i < (EXPANDER_BUTTONS + EXTRA_COUNT); i++) {
    lastPressTime[i] = 0;
    pressCount[i] = 0;
  }
  Serial.print(F("[INIT] Configured for "));
  Serial.print(EXPANDER_BUTTONS + EXTRA_COUNT);
  Serial.print(F(" total buttons ("));
  Serial.print(EXPANDER_BUTTONS);
  Serial.println(F(" PCF8575 + Arduino extras)"));

  // ── Initialize SD card pin to avoid MISO conflicts ──
  pinMode(CARDCS, OUTPUT);
  digitalWrite(CARDCS, HIGH);    // SD chip‑select held HIGH initially

  // Initialize VS1053 first
  Serial.println(F("[INIT] Searching for VS1053 codec..."));
  if (!musicPlayer.begin()) {
    Serial.println(F("[ERROR] VS1053 codec not found! Check wiring:"));
    Serial.println(F("  - SHIELD_CS (xCS): pin 7"));
    Serial.println(F("  - SHIELD_DCS (xDCS): pin 6")); 
    Serial.println(F("  - DREQ: pin 3"));
    while (1);
  }
  Serial.println(F("[SUCCESS] VS1053 codec initialized successfully!"));

  // Now safe to initialize SD card
  if (!SD.begin(CARDCS)) {
    Serial.println(F("SD card initialization failed!"));
    while (1);
  }
  Serial.println(F("SD card initialized."));

  // Configure VS1053 for optimal performance  
  musicPlayer.setVolume(1, 1);   // MAXIMUM default volume (0=loudest, 100=quiet)
  Serial.println(F("[AUDIO] Volume increased to maximum (1/100)"));  // Startup volume confirmation
  // DO NOT call useInterrupt() - this enables polling mode to prevent I2C conflicts
  
  // Quick startup sound test
  Serial.println(F("VS1053 audio test..."));
  musicPlayer.sineTest(0x44, 200);  // Brief 1kHz tone
  delay(300);

  // Load any existing mappings, or use defaults
  loadConfig();
  if (!hasValidMappings()) {
    Serial.println(F("Loading default mappings..."));
    initializeDefaultMappings();
  }
  
  // Load SD-based configuration if available
  initSDConfig();

  // Initialize I²C for PCF8575 expanders  
  Serial.println(F("[I2C] Initializing I2C bus for port expanders..."));
  Serial.println(F("[I2C] Using Wire1 bus (STEMMA QT connector)"));
  Wire1.begin();
  Serial.println(F("[I2C] I2C bus initialized on Wire1"));
  
  Serial.println(F("[I2C] Scanning for PCF8575 expanders..."));
  for (uint8_t e = 0; e < NUM_PCF; e++) {
    if (!pcf[e].begin(PCF_ADDR[e], &Wire1)) {
      Serial.print(F("[WARNING] PCF8575 #")); Serial.print(e);
      Serial.print(F(" (0x")); Serial.print(PCF_ADDR[e], HEX); Serial.println(F(") not found on Wire1!"));
      Serial.print(F("[WARNING] Check STEMMA QT connection to 0x")); Serial.println(PCF_ADDR[e], HEX);
      Serial.print(F("[WARNING] GPIO pins "));
      Serial.print(e * 16); Serial.print(F("-")); Serial.print((e * 16) + 15);
      Serial.println(F(" will not be available"));
    } else {
      Serial.print(F("[SUCCESS] PCF8575 #")); Serial.print(e);
      Serial.print(F(" (0x")); Serial.print(PCF_ADDR[e], HEX); Serial.print(F(") online - GPIO "));
      Serial.print(e * 16); Serial.print(F("-")); Serial.print((e * 16) + 15);
      Serial.println(F(" ready"));
    }
  }

  // Configure PCF8575 pins as inputs with pullup
  for (uint8_t e = 0; e < NUM_PCF; e++) {
    for (uint8_t i = 0; i < 16; i++) {
      pcf[e].pinMode(i, INPUT_PULLUP);
    }
  }

  // Initialize extra Arduino pins
  for (uint8_t x = 0; x < EXTRA_COUNT; x++) {
    pinMode(extraPins[x], INPUT_PULLUP);
    lastExtra[x] = digitalRead(extraPins[x]);
  }

  // Prime the expander states
  for (uint8_t e = 0; e < NUM_PCF; e++) {
    last_s[e] = pcf[e].digitalReadWord();
  }

  // Initialize hardware button mappings
  initializeHardwareMapping();

  // Initialize FS session for atomic updates
  initFSSession();
  Serial.println(F("[FS] Serial FS protocol ready"));

#ifdef FEATURE_SD_PLAYLISTS
  // Load mode configuration for playlist engine
  if (loadModeCfg()) {
    Serial.print(F("[CONFIG] Loaded mode: "));
    Serial.print(modeCfg.priority == GlobalPriority::HUMAN_FIRST ? F("HUMAN_FIRST") : F("GENERATED_FIRST"));
    Serial.print(F(", Strict playlists: "));
    Serial.println(modeCfg.strictPlaylists ? F("ON") : F("OFF"));
  } else {
    Serial.println(F("[CONFIG] Using default mode configuration"));
  }
#endif

  // Test audio by playing first available track
  Serial.println(F("Testing audio system..."));
  if (SD.exists("/01/001.mp3")) {
    Serial.println(F("Playing startup audio..."));
    musicPlayer.startPlayingFile("/01/001.mp3");
    delay(2000);  // Let it play briefly
    musicPlayer.stopPlaying();
  }

  Serial.println(F("\n=================================================="));
  Serial.println(F("    TACTILE COMMUNICATION DEVICE READY!"));
  Serial.println(F("=================================================="));
  Serial.print(F("Initialization completed in "));
  Serial.print(millis());
  Serial.println(F(" milliseconds"));
  printMenu();
}

void loop() {
  // Feed VS1053 audio buffer manually (prevents I2C deadlock)
  
  musicPlayer.setVolume(1, 1);   // MAXIMUM default volume (0=loudest, 100=quiet)
  musicPlayer.feedBuffer();
  
  // Handle period triple-press window finalization
  finalizePeriodWindow();
  
  // Handle Serial commands
  if (Serial.available()) {
    char c = Serial.read();
    switch (c) {
      case 'C': case 'c':
        inCalibrate = true;
        printCalibrationInstructions();
        break;
      case 'E': case 'e':
        inCalibrate = false;
        Serial.println(F("\n** Calibration mode OFF **"));
        printMenu();
        break;
      case 'L': case 'l': loadConfig(); break;
      case 'S': case 's': saveConfig(); break;
      case 'P': case 'p': printMap(); break;
      case 'H': case 'h': printMenu(); break;
      case 'M': case 'm':
        // Toggle priority mode manually and persist everywhere
        currentMode = (currentMode == GlobalPriority::HUMAN_FIRST) ? GlobalPriority::GENERATED_FIRST : GlobalPriority::HUMAN_FIRST;
        // Keep SD playlist engine config in sync
        modeCfg.priority = currentMode;
        // Persist to EEPROM
        savePriorityMode();
        // Persist to SD config if available
        #ifdef FEATURE_SD_PLAYLISTS
        (void)saveModeCfg();
        #endif
        // Audible announcement and console feedback
        announcePriorityMode(currentMode);
        break;
      case 'T': case 't': testAllButtons(); break;
      case 'U': case 'u': sanityCheckAudio(); break;
      case 'V': case 'v': 
        Serial.println(F("Volume commands: + (louder), - (quieter)"));
        Serial.println(F("Numbers 1-9: Set specific volume level (1=max, 9=quiet)"));
        break;
      case '+':
        musicPlayer.setVolume(1, 1);  // Maximum volume
        Serial.println(F("[AUDIO] Volume increased to maximum (1/100)"));
        break;
      case '-':
        musicPlayer.setVolume(15, 15); // Moderate volume  
        Serial.println(F("[AUDIO] Volume decreased to moderate (15/100)"));
        break;
      case '1': case '2': case '3': case '4': case '5': 
      case '6': case '7': case '8': case '9': {
        uint8_t level = c - '0';  // Convert char to number
        uint8_t volume = level * 10;  // 1=10, 2=20, ..., 9=90
        if (level == 1) volume = 1;   // Special case: 1 = maximum volume
        musicPlayer.setVolume(volume, volume);
        Serial.print(F("[AUDIO] Volume set to level "));
        Serial.print(level);
        Serial.print(F(" ("));
        Serial.print(volume);
        Serial.println(F("/100)"));
        break;
      }
      case 'X': case 'x':
        if (isPlaying) {
          Serial.print(F("[AUDIO] Manual stop requested: "));
          Serial.println(currentTrackPath);
          musicPlayer.stopPlaying();
          Serial.println(F("[AUDIO] Playback stopped"));
          isPlaying = false;
          currentTrackPath = "";
        } else {
          Serial.println(F("[AUDIO] No audio currently playing"));
        }
        break;
    }
  }

  // Read current expander states
  uint16_t s0 = pcf[0].digitalReadWord();   // GPIO 0–15
  uint16_t s1 = pcf[1].digitalReadWord();   // GPIO 16–31
  uint16_t s2 = pcf[2].digitalReadWord();   // GPIO 32–47

  // Edge-detect PCF8575 #0 → indices 0–15
  for (uint8_t i = 0; i < 16; i++) {
    bool prev = bitRead(last_s[0], i);
    bool cur  = bitRead(s0, i);
    if (prev && !cur) handlePress(i);
  }

  // Edge-detect PCF8575 #1 → indices 16–31
  for (uint8_t i = 0; i < 16; i++) {
    bool prev = bitRead(last_s[1], i);
    bool cur  = bitRead(s1, i);
    if (prev && !cur) handlePress(i + 16);
  }

  // Edge-detect PCF8575 #2 → indices 32–47
  for (uint8_t i = 0; i < 16; i++) {
    bool prev = bitRead(last_s[2], i);
    bool cur  = bitRead(s2, i);
    if (prev && !cur) handlePress(i + 32);
  }

  // Edge-detect Arduino extras
  for (uint8_t x = 0; x < EXTRA_COUNT; x++) {
    bool cur = digitalRead(extraPins[x]);
    if (lastExtra[x] == HIGH && cur == LOW) {
      handlePress(EXPANDER_BUTTONS + x);  // Extra pins start after expander buttons
    }
    lastExtra[x] = cur;
  }

  // Handle multi-press timeout and audio status
  handleMultiPress();
  checkAudioStatus();

  // Save last states
  last_s[0] = s0;
  last_s[1] = s1;
  last_s[2] = s2;

  delay(20);
}

 

void handlePress(uint8_t idx) {
  if (idx >= TOTAL_BUTTONS) return;
  
  unsigned long currentTime = millis();
  
  // Check if this is part of a multi-press sequence
  if (currentTime - lastPressTime[idx] < MULTI_PRESS_WINDOW) {
    pressCount[idx]++;
  } else {
    pressCount[idx] = 1;
  }
  
  lastPressTime[idx] = currentTime;
  
  // Get the button label from hardware mapping
  const char* buttonLabel = getButtonLabel(idx);
  bool hasMapping = (strlen(buttonLabel) > 0);
  
  // Print detailed button info with chip identification
  Serial.print(F("[BUTTON] "));
  if (idx < 16) {
    Serial.print(F("PCF8575 #0 GPIO "));
    Serial.print(idx);
  } else if (idx < 32) {
    Serial.print(F("PCF8575 #1 GPIO "));
    Serial.print(idx - 16);
    Serial.print(F(" (idx "));
    Serial.print(idx);
    Serial.print(F(")"));
  } else if (idx < 48) {
    Serial.print(F("PCF8575 #2 GPIO "));
    Serial.print(idx - 32);
    Serial.print(F(" (idx "));
    Serial.print(idx);
    Serial.print(F(")"));
  } else {
    uint8_t xp = extraPins[idx - 48];
    Serial.print(F("Arduino Pin "));
    Serial.print(xp);
    Serial.print(F(" (idx "));
    Serial.print(idx);
    Serial.print(F(")"));
  }
  
  if (hasMapping) {
    Serial.print(F(" → "));
    Serial.print(buttonLabel);
    
    // Show audio info if available
    AudioMapping* audioMap = findAudioByLabel(buttonLabel);
    if (audioMap && (audioMap->recCount > 0 || audioMap->ttsCount > 0)) {
      Serial.print(F(" [REC:"));
      Serial.print(audioMap->recFolder);
      Serial.print(F("/"));
      Serial.print(audioMap->recBase);
      Serial.print(F("/"));
      Serial.print(audioMap->recCount);
      Serial.print(F("|TTS:"));
      Serial.print(audioMap->ttsFolder);
      Serial.print(F("/"));
      Serial.print(audioMap->ttsBase);
      Serial.print(F("/"));
      Serial.print(audioMap->ttsCount);
      Serial.print(F("]"));
    }
  } else {
    Serial.print(F(" → UNMAPPED"));
  }
  
  Serial.print(F(" | Press #"));
  Serial.print(pressCount[idx]);
  Serial.print(F(" @ "));
  Serial.print(currentTime);
  Serial.println(F("ms"));

  // Handle Period button triple-press for priority mode switching
  if (hasMapping && (strcmp(buttonLabel, "PERIOD") == 0 || strcmp(buttonLabel, ".") == 0)) {
    handlePeriodPress();
    // Clear press count to prevent handleMultiPress from processing this button
    pressCount[idx] = 0;
    return;  // Period handling manages its own audio playback
  }
  
  // Handle calibration mode
  if (inCalibrate) {
    Serial.print(F("Enter new label for index "));
    Serial.print(idx);
    Serial.println(F(":"));
    while (!Serial.available()) delay(10);
    String lbl = Serial.readStringUntil('\n');
    lbl.trim();
    lbl.toUpperCase();
    
    if (lbl.length()) {
      lbl.toCharArray(mapTab[idx].label, sizeof(mapTab[idx].label));
      mapTab[idx].used = true;
      Serial.print(F("Mapped "));
      Serial.print(idx);
      Serial.print(F(" → "));
      Serial.println(lbl);
    }
  }
}

void handleMultiPress() {
  unsigned long currentTime = millis();
  
  for (uint8_t i = 0; i < TOTAL_BUTTONS; i++) {
    if (pressCount[i] > 0 && 
        (currentTime - lastPressTime[i]) > MULTI_PRESS_WINDOW) {
      
      // Get the button label from hardware mapping
      const char* buttonLabel = getButtonLabel(i);
      bool hasMapping = (strlen(buttonLabel) > 0);
      
      // Time to play the audio using the actual press count
      if (!inCalibrate && hasMapping) {
        playButtonAudioWithCount(buttonLabel, pressCount[i]);
      }
      pressCount[i] = 0; // Reset press count
    }
  }
}

void playButtonAudioWithCount(const char* label, uint8_t pressCount) {
  // Find the audio mapping for this label
  AudioMapping* audioMap = findAudioByLabel(label);
  if (!audioMap) {
    Serial.print(F("No audio mapping found for label: "));
    Serial.println(label);
    return;
  }
  
  Serial.print(F("Playing audio for label '"));
  Serial.print(label);
  Serial.print(F("' [REC folder "));
  Serial.print(audioMap->recFolder);
  Serial.print(F(", TTS folder "));
  Serial.print(audioMap->ttsFolder);
  Serial.print(F("]"));
  
  // Two-bank priority mode system
  Serial.print(F(" [REC:"));
  Serial.print(audioMap->recCount);
  Serial.print(F("/TTS:"));
  Serial.print(audioMap->ttsCount);
  Serial.print(F("], press #"));
  Serial.print(pressCount);
  Serial.print(F(", mode: "));
  Serial.println(currentMode == GlobalPriority::HUMAN_FIRST ? F("HUMAN_FIRST") : F("GENERATED_FIRST"));
  
  // Two-bank priority mode track selection
  uint8_t k = (pressCount - 1); // 0-based press index
  bool humanFirst = (currentMode == GlobalPriority::HUMAN_FIRST);
  
  // Choose bank order by mode
  uint8_t bank0Base, bank0Count, bank1Base, bank1Count;
  const char* bank0Type, *bank1Type;
  
  if (humanFirst) {
    // HUMAN_FIRST: Try recorded bank first, then TTS bank
    bank0Base = audioMap->recBase; bank0Count = audioMap->recCount;
    bank1Base = audioMap->ttsBase; bank1Count = audioMap->ttsCount;
    bank0Type = "RECORDED"; bank1Type = "TTS";
  } else {
    // GENERATED_FIRST: Try TTS bank first, then recorded bank
    bank0Base = audioMap->ttsBase; bank0Count = audioMap->ttsCount;
    bank1Base = audioMap->recBase; bank1Count = audioMap->recCount;
    bank0Type = "TTS"; bank1Type = "RECORDED";
  }
  
  // Map k across banks: exhaust bank0, then bank1, then wrap
  uint8_t trackNumber;
  const char* selectedBankType;
  
  if (bank0Count > 0 && k < bank0Count) {
    // Use primary bank (bank0)
    trackNumber = bank0Base + k;
    selectedBankType = bank0Type;
  } else if (bank1Count > 0) {
    // Use secondary bank (bank1)
    uint8_t k2 = (bank0Count == 0) ? k : (k - bank0Count);
    trackNumber = bank1Base + (k2 % bank1Count);
    selectedBankType = bank1Type;
  } else if (bank0Count > 0) {
    // Fallback to primary bank with wrapping
    trackNumber = bank0Base + (k % bank0Count);
    selectedBankType = bank0Type;
  } else {
    // No banks available - fallback to track 1
    trackNumber = 1;
    selectedBankType = "FALLBACK";
  }
  
  Serial.print(F("Priority mode: "));
  Serial.print(humanFirst ? F("HUMAN_FIRST") : F("GENERATED_FIRST"));
  Serial.print(F(" -> Selected "));
  Serial.print(selectedBankType);
  Serial.print(F(" bank, track "));
  Serial.println(trackNumber);
  
  Serial.print(F("Press index: "));
  Serial.print(k);
  Serial.print(F(", Final track: "));
  Serial.println(trackNumber);
  
  // Determine which folder to use based on selected bank
  uint8_t selectedFolder;
  if (bank0Count > 0 && k < bank0Count) {
    // Using bank0 (first priority bank)
    selectedFolder = humanFirst ? audioMap->recFolder : audioMap->ttsFolder;
  } else {
    // Using bank1 (second priority bank)
    selectedFolder = humanFirst ? audioMap->ttsFolder : audioMap->recFolder;
  }
  
  // Build file path
  String filePath = "/";
  if (selectedFolder < 10) filePath += "0";
  filePath += String(selectedFolder);
  filePath += "/";
  if (trackNumber < 10) filePath += "00";
  else if (trackNumber < 100) filePath += "0";
  filePath += String(trackNumber);
  filePath += ".mp3";
  
  // Get and display the text content for this audio file
  const char* audioText = getAudioText(selectedFolder, trackNumber);
  
  Serial.print(F("🎵 Playing: "));
  Serial.print(filePath);
  Serial.print(F(" -> \""));
  Serial.print(audioText);
  Serial.println(F("\""));
  
  // Check if file exists
  if (SD.exists(filePath.c_str())) {
    // SIMPLIFIED ROBUST AUDIO STOPPING - Prevent VS1053 lockups
    Serial.println(F("Stopping current audio..."));
    
    // Simple but effective stop sequence
    musicPlayer.stopPlaying();
    delay(100);
    
    // Quick check and single reset if needed
    if (musicPlayer.playingMusic) {
      Serial.println(F("Audio still playing - doing soft reset..."));
      musicPlayer.softReset();
      delay(150);
      // Restore volume after reset
      musicPlayer.setVolume(1, 1);
      delay(50);
    } else {
      Serial.println(F("Audio stopped successfully"));
    }
    
    Serial.println(F("Starting new audio..."));
    musicPlayer.startPlayingFile(filePath.c_str());
    Serial.println(F("✓ Audio playback started"));
    isPlaying = true;
    currentTrackPath = filePath;
  } else {
    Serial.print(F("⚠ Audio file not found: "));
    Serial.println(filePath);
    
    // Try track 001 as fallback
    String fallbackPath = "/";
    if (selectedFolder < 10) fallbackPath += "0";
    fallbackPath += String(selectedFolder);
    fallbackPath += "/001.mp3";
    
    if (SD.exists(fallbackPath.c_str())) {
      Serial.print(F("↳ Playing fallback track: "));
      Serial.println(fallbackPath);
      
      // SIMPLIFIED AUDIO STOPPING for fallback
      Serial.println(F("Stopping current audio for fallback..."));
      
      // Simple fallback stop sequence
      musicPlayer.stopPlaying();
      delay(100);
      
      // Quick check and single reset if needed
      if (musicPlayer.playingMusic) {
        Serial.println(F("Fallback audio still playing - doing soft reset..."));
        musicPlayer.softReset();
        delay(150);
        // Restore volume after reset
        musicPlayer.setVolume(1, 1);
        delay(50);
      } else {
        Serial.println(F("Fallback audio stopped successfully"));
      }
      
      musicPlayer.startPlayingFile(fallbackPath.c_str());
      isPlaying = true;
      currentTrackPath = fallbackPath;
    } else {
      Serial.println(F("✗ No audio files found for this label"));
    }
  }
}

void checkAudioStatus() {
  // Check if playback has finished
  if (isPlaying && musicPlayer.stopped()) {
    Serial.print(F("[AUDIO] Playback finished: "));
    Serial.println(currentTrackPath);
    isPlaying = false;
    currentTrackPath = "";
  }
}

void handlePeriodPress() {
  const unsigned long now = millis();
  
  // Start or reset the detection window
  if (periodPressCount == 0 || (now - periodWindowStart) > PERIOD_WINDOW_MS) {
    periodWindowStart = now;
    periodPressCount = 0;
  }
  
  periodPressCount++;
  Serial.print(F("Period press "));
  Serial.print(periodPressCount);
  Serial.print(F("/3 within window"));
  
  if (periodPressCount == 3 && (now - periodWindowStart) <= PERIOD_WINDOW_MS) {
    // Triple-press detected: toggle mode
    currentMode = (currentMode == GlobalPriority::HUMAN_FIRST) ? GlobalPriority::GENERATED_FIRST : GlobalPriority::HUMAN_FIRST;
    savePriorityMode();
    announcePriorityMode(currentMode);
    
    Serial.println(F("🔄 Priority mode toggled!"));
    
    // Reset detection state
    periodPressCount = 0;
    periodWindowStart = 0;
    
    return;  // Don't play normal period audio for triple-press
  }
  
  // Single or double press - play normal period audio after window expires
  // This will be handled by finalizePeriodWindow() function
}

void finalizePeriodWindow() {
  if (periodPressCount > 0 && (millis() - periodWindowStart) > PERIOD_WINDOW_MS) {
    // Window expired without triple-press - play normal period audio
    if (periodPressCount < 3) {
      Serial.println(F("Playing normal period audio with proper mapping"));
      
      // Use proper mapping + priority mode for period button
      playButtonAudioWithCount(".", 1);  // Respect two-bank priority system
    }
    
    // Reset detection state
    periodPressCount = 0;
    periodWindowStart = 0;
  }
}

void testAllButtons() {
  Serial.println(F("Testing all configured buttons with VS1053..."));
  Serial.println(F("Press 's' to stop test."));
  
  for (uint8_t i = 0; i < TOTAL_BUTTONS; i++) {
    if (Serial.available() && Serial.read() == 's') break;
    
    if (mapTab[i].used) {
      // Check if this label has audio
      AudioMapping* audioMap = findAudioByLabel(mapTab[i].label);
      if (audioMap && (audioMap->recCount > 0 || audioMap->ttsCount > 0)) {
        Serial.print(F("Testing button "));
        Serial.print(i);
        Serial.print(F(" ("));
        Serial.print(mapTab[i].label);
        Serial.println(F(")..."));
        
        // Use first available folder
        uint8_t folder = (audioMap->recCount > 0) ? audioMap->recFolder : audioMap->ttsFolder;
        String filePath = "/";
        if (folder < 10) filePath += "0";
        filePath += String(folder);
        filePath += "/001.mp3";
      
        if (SD.exists(filePath.c_str())) {
          musicPlayer.startPlayingFile(filePath.c_str());
          delay(2000);  // Play for 2 seconds
          musicPlayer.stopPlaying();
          delay(500);   // Brief pause between tests
        } else {
          Serial.print(F("  File not found: "));
          Serial.println(filePath);
        }
      } else {
        Serial.print(F("  No audio for label '"));
        Serial.print(mapTab[i].label);
        Serial.println(F("'"));
      }
    }
  }
  
  Serial.println(F("Button test complete."));
}

void printCalibrationInstructions() {
  Serial.println(F("\n*** CALIBRATION MODE ON ***"));
  Serial.println(F("• Press any button to assign/update its label"));
  Serial.println(F("• After press, type label and hit Enter"));
  Serial.println(F("• Press 'E' to exit calibration"));
}

void loadPriorityMode() {
  uint8_t mode = EEPROM.read(EEPROM_ADDR_MODE);
  if (mode <= 1) {
    currentMode = (GlobalPriority)mode;
  } else {
    currentMode = GlobalPriority::HUMAN_FIRST; // Default
  }
  
  Serial.print(F("[PRIORITY] Loaded mode: "));
  Serial.println(currentMode == GlobalPriority::HUMAN_FIRST ? F("HUMAN_FIRST") : F("GENERATED_FIRST"));
}

void savePriorityMode() {
  EEPROM.write(EEPROM_ADDR_MODE, (uint8_t)currentMode);
  Serial.print(F("[PRIORITY] Saved mode: "));
  Serial.println(currentMode == GlobalPriority::HUMAN_FIRST ? F("HUMAN_FIRST") : F("GENERATED_FIRST"));
}

void announcePriorityMode(GlobalPriority mode) {
  Serial.print(F("[PRIORITY] Current mode: "));
  Serial.println(mode == GlobalPriority::HUMAN_FIRST ? F("HUMAN_FIRST") : F("GENERATED_FIRST"));
  
  // Play audio announcement
  String announcePath = "/33/";
  announcePath += (mode == GlobalPriority::HUMAN_FIRST) ? "001" : "002";
  announcePath += ".mp3";
  
  if (SD.exists(announcePath.c_str())) {
    Serial.print(F("🔊 Announcing: "));
    Serial.println(announcePath);
    musicPlayer.stopPlaying();
    delay(100);
    musicPlayer.startPlayingFile(announcePath.c_str());
    isPlaying = true;
    currentTrackPath = announcePath;
  } else {
    Serial.print(F("⚠ Announcement file not found: "));
    Serial.println(announcePath);
    
    // Try alternate announcement file locations
    String alternateLocations[] = {
      "/" + announcePath.substring(4),     // Try in root directory
      "/audio/" + announcePath.substring(4), // Try in /audio/ directory
      "/announcements/" + announcePath.substring(4) // Try in /announcements/ directory
    };
    
    bool played = false;
    for (int i = 0; i < 3; i++) {
      if (SD.exists(alternateLocations[i].c_str())) {
        Serial.print(F("🔊 Found alternate announcement: "));
        Serial.println(alternateLocations[i]);
        musicPlayer.stopPlaying();
        delay(100);
        musicPlayer.startPlayingFile(alternateLocations[i].c_str());
        isPlaying = true;
        currentTrackPath = alternateLocations[i];
        played = true;
        break;
      }
    }
    
    // If no announcement file found, provide visual feedback only
    if (!played) {
      // Flash LED or provide other visual feedback
      Serial.println(F("📢 Priority mode changed - announcement files missing"));
      Serial.println(F("    Place 001.mp3 and 002.mp3 in /33/ directory for audio announcements"));
    }
  }
}

void checkButtons() {
  // Check PCF8575 expanders
  for (uint8_t pcfIndex = 0; pcfIndex < NUM_PCF; pcfIndex++) {
    uint16_t s = pcf[pcfIndex].digitalReadWord();
    uint16_t changed = s ^ last_s[pcfIndex];
    
    if (changed) {
      for (uint8_t pin = 0; pin < 16; pin++) {
        if (changed & (1 << pin)) {
          bool pressed = !(s & (1 << pin)); // PCF8575 is active low
          if (pressed) {
            uint8_t buttonIndex = (pcfIndex * 16) + pin;
            handlePress(buttonIndex);
          }
        }
      }
      last_s[pcfIndex] = s;
    }
  }
  
  // Check extra GPIO pins
  for (uint8_t i = 0; i < EXTRA_COUNT; i++) {
    bool current = digitalRead(extraPins[i]);
    if (current != lastExtra[i]) {
      if (!current) { // Active low
        uint8_t buttonIndex = TOTAL_EXPANDER_PINS + i;
        handlePress(buttonIndex);
      }
      lastExtra[i] = current;
    }
  }
}

// Helper function to find audio mapping by label
AudioMapping* findAudioByLabel(const char* label) {
  for (uint8_t i = 0; i < AUDIO_MAPPINGS_COUNT; i++) {
    if (strcmp(audioMappings[i].label, label) == 0) {
      return &audioMappings[i];
    }
  }
  return nullptr;
}

void printMap() {
  Serial.println(F("\n=== CURRENT BUTTON MAPPINGS (VS1053) ==="));
  for (uint8_t i = 0; i < TOTAL_BUTTONS; i++) {
    if (mapTab[i].used) {
      if (i < 48) {
        Serial.print(F("GPIO "));
        Serial.print(i);
      } else {
        uint8_t xp = extraPins[i - 48];
        Serial.print(F("Pin "));
        Serial.print(xp);
      }
      Serial.print(F(" → "));
      Serial.print(mapTab[i].label);
      
      // Show audio info if available
      AudioMapping* audioMap = findAudioByLabel(mapTab[i].label);
      if (audioMap && (audioMap->recCount > 0 || audioMap->ttsCount > 0)) {
        Serial.print(F(" [REC:"));
        Serial.print(audioMap->recFolder);
        Serial.print(F("/"));
        Serial.print(audioMap->recBase);
        Serial.print(F("/"));
        Serial.print(audioMap->recCount);
        Serial.print(F(", TTS:"));
        Serial.print(audioMap->ttsFolder);
        Serial.print(F("/"));
        Serial.print(audioMap->ttsBase);
        Serial.print(F("/"));
        Serial.print(audioMap->ttsCount);
        Serial.print(F("]"));
      } else {
        Serial.print(F(" [No audio]"));
      }
      Serial.println();
    }
  }
  Serial.println(F("=========================================="));
}

void saveConfig() {
  SD.remove("config.csv");
  File cfg = SD.open("config.csv", FILE_WRITE);
  if (!cfg) {
    Serial.println(F("Failed to create config.csv"));
    return;
  }
  
  // Write header (simplified format - just index and label)
  cfg.println("index,label");
  
  // Write mappings
  for (uint8_t i = 0; i < TOTAL_BUTTONS; i++) {
    if (mapTab[i].used) {
      cfg.print(i);
      cfg.print(',');
      cfg.println(mapTab[i].label);
    }
  }
  
  cfg.close();
  Serial.println(F("Config saved to config.csv"));
}
 

// Enhanced audio text content mapping for console logging
// Uses SD-loaded index with fallback to compiled mapping
const char* getAudioText(uint8_t folder, uint8_t track) {
  // Try SD-loaded audio index first
  if (sdConfigLoaded && audioIndex) {
    for (uint16_t i = 0; i < audioIndexCount; i++) {
      if (audioIndex[i].folder == folder && audioIndex[i].track == track) {
        return audioIndex[i].text;
      }
    }
  }
  
  // Fallback to compiled mapping
  // Folder 5 (A button)
  if (folder == 5) {
    switch (track) {
      case 1: return "Alari [REC]";
      case 2: return "Amer";
      case 3: return "Apple";
      case 4: return "Arabic Show";
      default: return "Unknown A track";
    }
  }
  // Folder 6 (B button)
  else if (folder == 6) {
    switch (track) {
      case 1: return "Bagel";
      case 2: return "Bathroom";
      case 3: return "Bed";
      case 4: return "Blanket";
      case 5: return "Breathe";
      case 6: return "Bye";
      default: return "Unknown B track";
    }
  }
  // Folder 7 (C button)
  else if (folder == 7) {
    switch (track) {
      case 1: return "Call";
      case 2: return "Car";
      case 3: return "Chair";
      case 4: return "Coffee";
      case 5: return "Cold";
      case 6: return "Cucumber";
      default: return "Unknown C track";
    }
  }
  // Folder 8 (D button)
  else if (folder == 8) {
    switch (track) {
      case 1: return "Daddy [REC]";
      case 2: return "Deen";
      case 3: return "Doctor";
      case 4: return "Door";
      case 5: return "Down";
      default: return "Unknown D track";
    }
  }
  // Folder 10 (F button)
  else if (folder == 10) {
    switch (track) {
      case 1: return "FaceTime";
      case 2: return "Funny";
      default: return "Unknown F track";
    }
  }
  // Folder 11 (G button)
  else if (folder == 11) {
    switch (track) {
      case 1: return "Garage";
      case 2: return "Go";
      case 3: return "Good Morning";
      default: return "Unknown G track";
    }
  }
  // Folder 12 (H button)
  else if (folder == 12) {
    switch (track) {
      case 1: return "Happy";
      case 2: return "Heartburn";
      case 3: return "Hot";
      case 4: return "How are you";
      case 5: return "Hungry";
      default: return "Unknown H track";
    }
  }
  // Folder 13 (I button)
  else if (folder == 13) {
    switch (track) {
      case 1: return "Inside";
      case 2: return "iPad";
      default: return "Unknown I track";
    }
  }
  // Folder 15 (K button)
  else if (folder == 15) {
    switch (track) {
      case 1: return "Kaiser";
      case 2: return "Kiyah";
      case 3: return "Kleenex";
      case 4: return "Kyan";
      default: return "Unknown K track";
    }
  }
  // Folder 16 (L button)
  else if (folder == 16) {
    switch (track) {
      case 1: return "I love you [REC]";
      case 2: return "Lee";
      case 3: return "Light Down";
      case 4: return "Light Up";
      default: return "Unknown L track";
    }
  }
  // Folder 17 (M button)
  else if (folder == 17) {
    switch (track) {
      case 1: return "Mad";
      case 2: return "Medical";
      case 3: return "Medicine";
      case 4: return "Meditate";
      case 5: return "Mohammad";
      default: return "Unknown M track";
    }
  }
  // Folder 18 (N button)
  else if (folder == 18) {
    switch (track) {
      case 1: return "Nada [REC]";
      case 2: return "Nadowie [REC]";
      case 3: return "Noah [REC]";
      case 4: return "No";
      default: return "Unknown N track";
    }
  }
  // Folder 19 (O button)
  else if (folder == 19) {
    switch (track) {
      case 1: return "Outside";
      default: return "Unknown O track";
    }
  }
  // Folder 20 (P button)
  else if (folder == 20) {
    switch (track) {
      case 1: return "Pain";
      case 2: return "Period";
      case 3: return "Phone";
      case 4: return "Purple";
      default: return "Unknown P track";
    }
  }
  // Folder 22 (R button)
  else if (folder == 22) {
    switch (track) {
      case 1: return "Rest";
      case 2: return "Room";
      default: return "Unknown R track";
    }
  }
  // Folder 23 (S button)
  else if (folder == 23) {
    switch (track) {
      case 1: return "Susu [REC]";
      case 2: return "Sad";
      case 3: return "Scarf";
      case 4: return "Shoes";
      case 5: return "Sinemet";
      case 6: return "Sleep";
      case 7: return "Socks";
      case 8: return "Stop";
      case 9: return "Space";
      default: return "Unknown S track";
    }
  }
  // Folder 24 (T button)
  else if (folder == 24) {
    switch (track) {
      case 1: return "TV";
      case 2: return "Togamet";
      case 3: return "Tylenol";
      default: return "Unknown T track";
    }
  }
  // Folder 25 (U button)
  else if (folder == 25) {
    switch (track) {
      case 1: return "Up";
      case 2: return "Urgent Care";
      default: return "Unknown U track";
    }
  }
  // Folder 27 (W button)
  else if (folder == 27) {
    switch (track) {
      case 1: return "Walk";
      case 2: return "Walker";
      case 3: return "Water";
      case 4: return "Wheelchair";
      default: return "Unknown W track";
    }
  }
  // Folder 29 (Y button)
  else if (folder == 29) {
    switch (track) {
      case 1: return "Yes";
      default: return "Unknown Y track";
    }
  }
  // Special folders
  else if (folder == 1) {
    switch (track) {
      case 1: return "Yes [Special]";
      case 2: return "No [Special]";
      case 3: return "Water [Special]";
      case 4: return "Help [Special]";
      default: return "Unknown Special track";
    }
  }
  else if (folder == 33) {
    switch (track) {
      case 1: return "Shift Help";
      case 2: return "Instructions";
      case 3: return "Detailed Help";
      case 4: return "Personal voice first";
      case 5: return "Computer voice first";
      default: return "Unknown System track";
    }
  }
  
  return "Unknown audio file";
}

// ===== SD CARD CSV LOADING FUNCTIONS =====

// Load audio index from /config/audio_index.csv
bool loadAudioIndex() {
  File file = SD.open("/config/audio_index.csv");
  if (!file) {
    Serial.println(F("[SD] /config/audio_index.csv not found, using compiled defaults"));
    return false;
  }
  
  // Count lines first
  audioIndexCount = 0;
  String line;
  file.readStringUntil('\n'); // Skip header
  while (file.available()) {
    line = file.readStringUntil('\n');
    if (line.length() > 0) audioIndexCount++;
  }
  file.close();
  
  if (audioIndexCount == 0) {
    Serial.println(F("[SD] No audio index entries found"));
    return false;
  }
  
  // Allocate memory
  audioIndex = new AudioIndex[audioIndexCount];
  if (!audioIndex) {
    Serial.println(F("[SD] Failed to allocate memory for audio index"));
    return false;
  }
  
  // Load data
  file = SD.open("/config/audio_index.csv");
  file.readStringUntil('\n'); // Skip header
  uint16_t idx = 0;
  
  while (file.available() && idx < audioIndexCount) {
    line = file.readStringUntil('\n');
    if (line.length() == 0) continue;
    
    // Parse CSV: folder,track,text,bank
    int comma1 = line.indexOf(',');
    int comma2 = line.indexOf(',', comma1 + 1);
    int comma3 = line.indexOf(',', comma2 + 1);
    
    if (comma1 > 0 && comma2 > comma1 && comma3 > comma2) {
      audioIndex[idx].folder = line.substring(0, comma1).toInt();
      audioIndex[idx].track = line.substring(comma1 + 1, comma2).toInt();
      strncpy(audioIndex[idx].text, line.substring(comma2 + 1, comma3).c_str(), 23);
      audioIndex[idx].text[23] = '\0';
      strncpy(audioIndex[idx].bank, line.substring(comma3 + 1).c_str(), 3);
      audioIndex[idx].bank[3] = '\0';
      idx++;
    }
  }
  file.close();
  
  Serial.print(F("[SD] Loaded "));
  Serial.print(audioIndexCount);
  Serial.println(F(" audio index entries"));
  return true;
}

// Load audio mappings from /config/audio_map.csv
bool loadAudioMappings() {
  File file = SD.open("/config/audio_map.csv");
  if (!file) {
    Serial.println(F("[SD] /config/audio_map.csv not found, using compiled defaults"));
    return false;
  }
  
  // Count lines first
  dynamicMappingsCount = 0;
  String line;
  file.readStringUntil('\n'); // Skip header
  while (file.available()) {
    line = file.readStringUntil('\n');
    if (line.length() > 0) dynamicMappingsCount++;
  }
  file.close();
  
  if (dynamicMappingsCount == 0) {
    Serial.println(F("[SD] No audio mapping entries found"));
    return false;
  }
  
  // Allocate memory
  dynamicMappings = new AudioMapping[dynamicMappingsCount];
  if (!dynamicMappings) {
    Serial.println(F("[SD] Failed to allocate memory for audio mappings"));
    return false;
  }
  
  // Load data
  file = SD.open("/config/audio_map.csv");
  file.readStringUntil('\n'); // Skip header
  uint8_t idx = 0;
  
  while (file.available() && idx < dynamicMappingsCount) {
    line = file.readStringUntil('\n');
    if (line.length() == 0) continue;
    
    // Parse CSV: label,rec_folder,rec_base,rec_count,tts_folder,tts_base,tts_count,fallback
    int commas[7];
    int pos = 0;
    for (int i = 0; i < 7; i++) {
      commas[i] = line.indexOf(',', pos);
      if (commas[i] == -1) break;
      pos = commas[i] + 1;
    }
    
    if (commas[6] > 0) {
      strncpy(dynamicMappings[idx].label, line.substring(0, commas[0]).c_str(), 11);
      dynamicMappings[idx].label[11] = '\0';
      dynamicMappings[idx].recFolder = line.substring(commas[0] + 1, commas[1]).toInt();
      dynamicMappings[idx].recBase = line.substring(commas[1] + 1, commas[2]).toInt();
      dynamicMappings[idx].recCount = line.substring(commas[2] + 1, commas[3]).toInt();
      dynamicMappings[idx].ttsFolder = line.substring(commas[3] + 1, commas[4]).toInt();
      dynamicMappings[idx].ttsBase = line.substring(commas[4] + 1, commas[5]).toInt();
      dynamicMappings[idx].ttsCount = line.substring(commas[5] + 1, commas[6]).toInt();
      strncpy(dynamicMappings[idx].fallbackLabel, line.substring(commas[6] + 1).c_str(), 11);
      dynamicMappings[idx].fallbackLabel[11] = '\0';
      idx++;
    }
  }
  file.close();
  
  Serial.print(F("[SD] Loaded "));
  Serial.print(dynamicMappingsCount);
  Serial.println(F(" audio mapping entries"));
  return true;
}

// Initialize SD-based configuration
void initSDConfig() {
  Serial.println(F("[SD] Loading configuration from SD card..."));
  
  bool indexLoaded = loadAudioIndex();
  bool mappingsLoaded = loadAudioMappings();
  
  sdConfigLoaded = indexLoaded && mappingsLoaded;
  
  if (sdConfigLoaded) {
    Serial.println(F("[SD] Configuration loaded successfully from SD card"));
  } else {
    Serial.println(F("[SD] Using compiled defaults"));
  }
}

// Initialize hardware button mappings
void initializeHardwareMapping() {
  Serial.println(F("[INIT] Initializing hardware-dependent button mappings..."));
  
  // Clear existing mapTab entries
  for (uint8_t i = 0; i < TOTAL_BUTTONS; i++) {
    mapTab[i].used = false;
    memset(mapTab[i].label, 0, sizeof(mapTab[i].label));
  }
  
  // Try to load hardware mappings from SD card first
  if (loadHardwareMapping()) {
    // Set up hardware mappings in mapTab for compatibility
    for (uint8_t i = 0; i < HARDWARE_BUTTON_COUNT; i++) {
      uint8_t hwIndex = hardwareButtonMap[i].hardwareIndex;
      if (hwIndex < TOTAL_BUTTONS) {
        strncpy(mapTab[hwIndex].label, hardwareButtonMap[i].label, sizeof(mapTab[hwIndex].label) - 1);
        mapTab[hwIndex].label[sizeof(mapTab[hwIndex].label) - 1] = '\0';
        mapTab[hwIndex].used = true;
      }
    }
    
    Serial.print(F("[INIT] Configured "));
    Serial.print(HARDWARE_BUTTON_COUNT);
    Serial.println(F(" hardware button mappings from CONFIG.CSV"));
  } else {
    Serial.println(F("[INIT] No CONFIG.CSV found - use calibration mode to assign buttons"));
    Serial.println(F("[INIT] Audio mappings are ready for any button labels"));
  }
}

// Load configuration (legacy entry point)
// In the new architecture, this initializes hardware mapping from SD if available.
void loadConfig() {
  Serial.println(F("[CONFIG] Loading configuration..."));
  initializeHardwareMapping();
}

// Check if any button mappings are currently valid
bool hasValidMappings() {
  // If dynamic hardware map is present and populated, it's valid
  if (hardwareButtonMap != nullptr && HARDWARE_BUTTON_COUNT > 0) {
    return true;
  }
  // Otherwise, check calibrated mapTab entries
  for (uint8_t i = 0; i < TOTAL_BUTTONS; i++) {
    if (mapTab[i].used && mapTab[i].label[0] != '\0') {
      return true;
    }
  }
  return false;
}

// Provide minimal defaults when no mappings are present
// Keeps system functional enough for calibration and testing
void initializeDefaultMappings() {
  Serial.println(F("[CONFIG] Initializing minimal default mappings"));
  // Clear any existing
  for (uint8_t i = 0; i < TOTAL_BUTTONS; i++) {
    mapTab[i].used = false;
    mapTab[i].label[0] = '\0';
  }
  // Optionally set a couple of helpful defaults
  // Map index 0 to PERIOD so triple-press toggling can be demonstrated
  if (TOTAL_BUTTONS > 0) {
    strncpy(mapTab[0].label, "PERIOD", sizeof(mapTab[0].label) - 1);
    mapTab[0].label[sizeof(mapTab[0].label) - 1] = '\0';
    mapTab[0].used = true;
  }
}

// Print serial command menu
void printMenu() {
  Serial.println(F("\n=== TACTILE COMMUNICATOR COMMANDS ==="));
  Serial.println(F("L/l - Load config from SD"));
  Serial.println(F("S/s - Save config to SD"));
  Serial.println(F("P/p - Print current mappings"));
  Serial.println(F("H/h - Show this help menu"));
  Serial.println(F("M/m - Toggle priority mode (HUMAN_FIRST/GENERATED_FIRST)"));
  Serial.println(F("R/r - Reload playlists and configuration"));
  Serial.println(F("T/t - Test all buttons"));
  Serial.println(F("U/u - Check audio file sanity (verify all mapped files exist)"));
  Serial.println(F("V/v - Show volume commands"));
  Serial.println(F("+   - Increase volume to maximum"));
  Serial.println(F("-   - Decrease volume to moderate"));
  Serial.println(F("1-9 - Set volume level (1=max, 9=quiet)"));
  Serial.println(F("X/x - Stop current audio playback"));
  Serial.println(F("\nPriority Mode: Triple-press Period button to toggle"));
  Serial.println(F("Console Logging: Shows text content of played audio files"));
  Serial.println(F("========================================\n"));
}

// Audio sanity check function - verifies all mapped files exist
void sanityCheckAudio() {
  Serial.println(F("[CHECK] Verifying mapped audio files..."));
  
  for (uint8_t i = 0; i < AUDIO_MAPPINGS_COUNT; i++) {
    const AudioMapping& m = audioMappings[i];
    
    // Check REC bank files
    if (m.recCount > 0) {
      for (uint8_t t = 0; t < m.recCount; t++) {
        String path = "/";
        if (m.recFolder < 10) path += "0";
        path += String(m.recFolder);
        path += "/";
        if ((m.recBase + t) < 10) path += "00";
        else if ((m.recBase + t) < 100) path += "0";
        path += String(m.recBase + t);
        path += ".mp3";
        
        if (!SD.exists(path.c_str())) {
          Serial.print(F("⚠ Missing REC file for "));
          Serial.print(m.label);
          Serial.print(F(": "));
          Serial.print(path);
          Serial.print(F(" -> \""));
          Serial.print(getAudioText(m.recFolder, m.recBase + t));
          Serial.println(F("\""));
        }
      }
    }
    
    // Check TTS bank files
    if (m.ttsCount > 0) {
      for (uint8_t t = 0; t < m.ttsCount; t++) {
        String path = "/";
        if (m.ttsFolder < 10) path += "0";
        path += String(m.ttsFolder);
        path += "/";
        if ((m.ttsBase + t) < 10) path += "00";
        else if ((m.ttsBase + t) < 100) path += "0";
        path += String(m.ttsBase + t);
        path += ".mp3";
        
        if (!SD.exists(path.c_str())) {
          Serial.print(F("⚠ Missing TTS file for "));
          Serial.print(m.label);
          Serial.print(F(": "));
          Serial.print(path);
          Serial.print(F(" -> \""));
          Serial.print(getAudioText(m.ttsFolder, m.ttsBase + t));
          Serial.println(F("\""));
        }
      }
    }
  }
  
  Serial.println(F("[CHECK] Audio file verification complete."));
}


// Play button audio with playlist integration
void playButtonAudio(const char* label, uint8_t pressCount) {
#ifdef FEATURE_SD_PLAYLISTS
  if (modeCfg.strictPlaylists) {
    // Use playlist engine
    // Select bank order based on configured priority mode
    const bool humanFirst = (modeCfg.priority == GlobalPriority::HUMAN_FIRST);
    const char* trackPath = getNextTrack(label, humanFirst);
    if (trackPath) {
      // Playlist entries are relative to /audio
      String fullPath = "/audio/";
      fullPath += trackPath;

      Serial.print(F("[PLAYLIST] Playing: "));
      Serial.println(fullPath);
      
      if (musicPlayer.startPlayingFile(fullPath.c_str())) {
        currentTrackPath = fullPath;
        isPlaying = true;
      } else {
        Serial.print(F("[ERROR] Failed to play: "));
        Serial.println(fullPath);
      }
      return;
    } else {
      Serial.print(F("[PLAYLIST] No track found for key: "));
      Serial.println(label);
    }
  }
#endif
  
  // Fall back to legacy audio mapping system
  AudioMapping* mapping = findAudioByLabel(label);
  if (!mapping) {
    Serial.print(F("[AUDIO] No mapping found for label: "));
    Serial.println(label);
    return;
  }
  
  // Legacy priority mode logic
  bool useRecorded = (currentMode == GlobalPriority::HUMAN_FIRST);
  uint8_t folder, track;
  
  if (useRecorded && mapping->recCount > 0) {
    // Use recorded audio
    folder = mapping->recFolder;
    track = mapping->recBase + ((pressCount - 1) % mapping->recCount);
  } else if (mapping->ttsCount > 0) {
    // Use TTS audio
    folder = mapping->ttsFolder;
    track = mapping->ttsBase + ((pressCount - 1) % mapping->ttsCount);
  } else {
    Serial.print(F("[AUDIO] No audio available for label: "));
    Serial.println(label);
    return;
  }
  
  // Build file path
  String path = "/";
  if (folder < 10) path += "0";
  path += String(folder);
  path += "/";
  if (track < 10) path += "00";
  else if (track < 100) path += "0";
  path += String(track);
  path += ".mp3";
  
  Serial.print(F("[AUDIO] Playing: "));
  Serial.print(path);
  Serial.print(F(" -> \""));
  Serial.print(getAudioText(folder, track));
  Serial.println(F("\""));
  
  if (musicPlayer.startPlayingFile(path.c_str())) {
    currentTrackPath = path;
    isPlaying = true;
  } else {
    Serial.print(F("[ERROR] Failed to play: "));
    Serial.println(path);
  }
}
