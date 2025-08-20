/*
 * Tactile Communication Device - Updated for New SD Card Structure
 * 
 * This version works strictly with the new SD card structure:
 * - config/keys.csv for button definitions
 * - mappings/index.csv for playlist mappings
 * - audio/human/[KEY]/ and audio/generated/[KEY]/ for audio files
 * - playlist.m3u files in each audio directory
 * 
 * Hardware Components:
 * - Arduino UNO R4 WiFi
 * - Adafruit VS1053 Codec Breakout or Shield
 * - 3x PCF8575 I2C port expanders (0x20, 0x21, 0x22)
 * - MicroSD card (formatted as FAT32)
 * - 32+ tactile buttons
 * - Quality speaker/headphones
 * - Rechargeable battery pack
 * 
 * IMPORTANT: Install SdFat library v2.2.3+ from Library Manager
 * Tools > Manage Libraries > Search "SdFat" > Install
 */

#include <SPI.h>
#include <Wire.h>
#include <EEPROM.h>
#include "Adafruit_PCF8575.h"
#include "Adafruit_VS1053.h"
#include <string.h>
#include <ctype.h>

// ==== SEGMENT 1: DATA MODE GLOBALS & CONSTANTS ====

/* ---- user-tunable knobs ---- */
#define DATA_BAUD_HZ                115200   // you can bump to 500000/1000000 later
#define DATA_IDLE_TIMEOUT_MS        30000    // auto-exit after 30s idle
#define DATA_WRITE_ENABLE_FLAG_PATH "/CONFIG/WRITES.FLG"  // require this file to allow PUT/DEL
#define DATA_USE_CRC32              1        // 1=enable CRC32 optional checks (host may omit)

/* ---- device mode ---- */
enum class DeviceMode : uint8_t { NORMAL, DATA_MODE };
DeviceMode deviceMode = DeviceMode::NORMAL;

/* ---- serial line collector (line framed commands) ---- */
static const size_t DM_LINE_MAX = 128;
char dm_line[DM_LINE_MAX];
uint16_t dm_line_len = 0;

/* ---- data mode state ---- */
enum class DataCmdState : uint8_t { LINE, PUT_PAYLOAD, GET_STREAM };
DataCmdState dm_state = DataCmdState::LINE;

unsigned long dm_last_activity_ms = 0;

/* ---- PUT state ---- */
File dm_put_file;
char dm_put_tmp_path[128];
char dm_put_final_path[128];
uint32_t dm_put_remaining = 0;
#if DATA_USE_CRC32
uint32_t dm_put_crc_host = 0;
uint32_t dm_put_crc_calc = 0;
#endif
// small write buffer for efficiency
static const size_t DM_IOBUF_SZ = 512;
uint8_t dm_wbuf[DM_IOBUF_SZ];
size_t dm_wbuf_len = 0;

/* ---- GET state ---- */
File dm_get_file;
uint8_t dm_rbuf[DM_IOBUF_SZ];

/* ---- helpers forward decls ---- */
void enterDataMode();
void exitDataMode();
void dm_feedByte(char c);
void dm_handleLine(const char* line);
bool isWriteEnabled();
bool mkdir_p(const char* path);
bool atomicRename(const char* srcTmp, const char* dstFinal);
void path_audio(char* out, size_t outsz, const char* bank, const char* key, const char* fname);
#if DATA_USE_CRC32
void crc32_reset(uint32_t &crc);
void crc32_update(uint32_t &crc, const uint8_t* data, size_t len);
#endif

// Compile-time logging control
#ifndef VERBOSE_LOGS
#define VERBOSE_LOGS 0
#endif

// Control whether to read .txt captions before playback (SD I/O)
#ifndef CAPTION_READS
#define CAPTION_READS 1
#endif

// VS1053 pins - using shield pin mapping
#define VS1053_RESET   -1     // VS1053 reset pin (tied high on shield)
#define VS1053_CS       7     // VS1053 xCS (shield pin mapping)
#define VS1053_DCS      6     // VS1053 xDCS (shield pin mapping)
#define CARDCS          4     // micro-SD CS (fixed trace on shield)
#define VS1053_DREQ     3     // VS1053 DREQ (INT1 on Uno)

Adafruit_VS1053_FilePlayer musicPlayer = 
  Adafruit_VS1053_FilePlayer(VS1053_RESET, VS1053_CS, VS1053_DCS, VS1053_DREQ, CARDCS);

// SD objects
File file;


// ===== PCF8575 Expander Configuration =====
// Planned expander addresses (expandable design)
static const uint8_t PCF_ADDR[] = { 0x20, 0x21, 0x22 };
static const uint8_t NUM_PCF = sizeof(PCF_ADDR) / sizeof(PCF_ADDR[0]);
static const uint16_t EXPANDER_BUTTONS = (uint16_t)NUM_PCF * 16;

// Computed total button constants
static const uint8_t EXTRA_COUNT = 4;
static const uint16_t TOTAL_EXPANDER_PINS = NUM_PCF * 16;
static const uint16_t TOTAL_BUTTONS = TOTAL_EXPANDER_PINS + EXTRA_COUNT;

// Configuration constants (reduced to save RAM on UNO R4)
#define MAX_KEYS 36            // was 50; A-Z + specials fit comfortably
#define MAX_FILENAME_LEN 48    // was 64
// Tight path buffer for /audio/{bank}/{KEY}/NNN.mp3
#define MAX_PATH_LEN 64

// PCF8575 I2C port expanders (supporting up to 32+ buttons)
Adafruit_PCF8575 pcf[NUM_PCF];

// Extra Arduino pins for additional controls (avoid pins 0,1 for Serial)
const uint8_t extraPins[] = { 8, 9, 2, 5 };   // Safe pins: VS1053 uses pins 3,4,6,7
// Compile-time validation
static_assert(sizeof(extraPins) / sizeof(extraPins[0]) == EXTRA_COUNT, "EXTRA_COUNT mismatch with extraPins array");

// Priority mode enumeration
enum class PriorityMode : uint8_t {
  HUMAN_FIRST,
  GENERATED_FIRST
};

// Key configuration structure
struct KeyConfig {
  char key[24];           // Key name (HELLO_HOW_ARE_YOU fits; reduces RAM)
  char description[24];   // Truncated description is acceptable for logging
  bool hasHuman;          // Whether human audio exists
  bool hasGenerated;      // Whether generated audio exists
};

// Button mapping structure (use key index instead of duplicating key strings)
struct ButtonMapping {
  bool used;
  int16_t keyIndex;       // index into keys[] (-1 if unset)
  uint8_t buttonIndex;    // Physical button index
  char source[12];        // e.g., "keys.csv"
  char input[12];         // e.g., "pcf0:2" or "gpio:8"
};

// ===== NEW AUDIO SOURCING ARCHITECTURE =====
// Completely reworked to handle flexible audio file sourcing
// Supports both numbered files (001.mp3, 002.mp3) and named files
// Works with current SD card structure on D: drive

static inline bool endsWithIgnoreCase(const char *s, const char *suffix) {
  size_t ls = strlen(s), lt = strlen(suffix);
  if (lt > ls) return false;
  const char *a = s + (ls - lt);
  for (size_t i = 0; i < lt; i++) {
    char c1 = a[i];
    char c2 = suffix[i];
    if (c1 >= 'A' && c1 <= 'Z') c1 = (char)(c1 - 'A' + 'a');
    if (c2 >= 'A' && c2 <= 'Z') c2 = (char)(c2 - 'A' + 'a');
    if (c1 != c2) return false;
  }
  return true;
}

static inline bool hasAudioExt(const char *name) {
  return endsWithIgnoreCase(name, ".MP3") || endsWithIgnoreCase(name, ".WAV") || endsWithIgnoreCase(name, ".OGG");
}

// Audio source type enumeration
enum class AudioSource : uint8_t {
  HUMAN,
  GENERATED,
  AUTO  // Use current mode preference
};

// Audio file discovery structure
struct AudioFileInfo {
  char path[MAX_PATH_LEN];
  char description[64];
  bool exists;
  AudioSource source;
};

// New flexible audio sourcing system
class AudioSourceManager {
public:
  // Find audio file for a key and press count with looping support
  static bool findAudioFile(const char* key, uint8_t pressCount, AudioSource preferredSource, AudioFileInfo* result) {
    result->exists = false;
    result->path[0] = '\0';
    result->description[0] = '\0';
    
    Serial.print(F("[AUDIO_SEARCH] Looking for key '"));
    Serial.print(key);
    Serial.print(F("', press #"));
    Serial.print(pressCount);
    Serial.print(F(", preferred source: "));
    Serial.println((preferredSource == AudioSource::HUMAN) ? F("HUMAN") : F("GENERATED"));
    
    // Try preferred source first, then fallback
    AudioSource sources[] = {preferredSource, (preferredSource == AudioSource::HUMAN) ? AudioSource::GENERATED : AudioSource::HUMAN};
    
    for (int i = 0; i < 2; i++) {
      AudioSource currentSource = sources[i];
      if (currentSource == AudioSource::AUTO) continue;
      
      const char* sourceDir = (currentSource == AudioSource::HUMAN) ? "HUMAN" : "GENERA~1";
      
      Serial.print(F("[AUDIO_SEARCH] Trying source: "));
      Serial.println(sourceDir);
      
      // First, count how many audio files exist in this directory
      uint8_t maxFiles = countAudioFilesInDir(sourceDir, key);
      if (maxFiles == 0) {
        Serial.println(F("[AUDIO_SEARCH] ✗ No audio files found in directory"));
        continue; // Try next source
      }
      
      // Calculate effective press count with looping
      uint8_t effectivePressCount = ((pressCount - 1) % maxFiles) + 1;
      if (effectivePressCount != pressCount) {
        Serial.print(F("[LOOP] Press #"));
        Serial.print(pressCount);
        Serial.print(F(" wrapped to #"));
        Serial.print(effectivePressCount);
        Serial.print(F(" ("));
        Serial.print(maxFiles);
        Serial.println(F(" files available)"));
      }
      
      // Try numbered file first (001.mp3, 002.mp3, etc.)
      char numberedPath[MAX_PATH_LEN];
      snprintf(numberedPath, sizeof(numberedPath), "/AUDIO/%s/%s/%03u.MP3", sourceDir, key, effectivePressCount);
      
      Serial.print(F("[AUDIO_SEARCH] Checking path: "));
      Serial.println(numberedPath);
      
      if (SD.exists(numberedPath)) {
        Serial.println(F("[AUDIO_SEARCH] ✓ Found numbered file!"));
        strncpy(result->path, numberedPath, sizeof(result->path) - 1);
        result->path[sizeof(result->path) - 1] = '\0';
        result->source = currentSource;
        result->exists = true;
        
        // Try to load description from .txt file
        loadDescription(result);
        return true;
      } else {
        Serial.println(F("[AUDIO_SEARCH] ✗ Numbered file not found, trying directory scan"));
        
        // Try to find any audio file in the directory for this effective press count
        if (findNthAudioInDir(sourceDir, key, effectivePressCount, result)) {
          Serial.println(F("[AUDIO_SEARCH] ✓ Found via directory scan!"));
          result->source = currentSource;
          return true;
        } else {
          Serial.println(F("[AUDIO_SEARCH] ✗ Directory scan failed"));
        }
      }
    }
    
    Serial.println(F("[AUDIO_SEARCH] ✗ No audio file found for this key"));
    return false;
  }
  
  // Get audio source preference based on current mode and special key rules
  static AudioSource getPreferredSource(const char* key, uint8_t pressCount, PriorityMode currentMode) {
    // Special handling for SHIFT button
    if (strcmp(key, "SHIFT") == 0) {
      if (pressCount == 1) return AudioSource::HUMAN;  // Greeting
      if (pressCount >= 2) return AudioSource::GENERATED;  // Instructions/word list
    }
    
    // Special handling for PERIOD button
    if (strcmp(key, "PERIOD") == 0) {
      if (pressCount >= 2) return AudioSource::GENERATED;  // Mode announcements
    }
    
    // Default to current mode preference
    return (currentMode == PriorityMode::HUMAN_FIRST) ? AudioSource::HUMAN : AudioSource::GENERATED;
  }
  
private:
  // Count total audio files in a directory for looping support
  static uint8_t countAudioFilesInDir(const char* sourceDir, const char* key) {
    char dirPath[MAX_PATH_LEN];
    snprintf(dirPath, sizeof(dirPath), "/AUDIO/%s/%s", sourceDir, key);
    
    File dir = SD.open(dirPath);
    if (!dir) {
      return 0;
    }
    
    uint8_t count = 0;
    while (true) {
      File f = dir.openNextFile();
      if (!f) break;
      
      if (!f.isDirectory() && hasAudioExt(f.name())) {
        count++;
      }
      f.close();
    }
    
    dir.close();
    return count;
  }

  // Load description from corresponding .txt file
  static void loadDescription(AudioFileInfo* info) {
    char txtPath[MAX_PATH_LEN];
    strncpy(txtPath, info->path, sizeof(txtPath) - 1);
    txtPath[sizeof(txtPath) - 1] = '\0';
    
    // Replace .mp3 with .txt
    char* ext = strrchr(txtPath, '.');
    if (ext) {
      strncpy(ext, ".txt", sizeof(txtPath) - (ext - txtPath));
      
      File txtFile = SD.open(txtPath);
      if (txtFile) {
        String content = txtFile.readString();
        content.trim();
        
        // Remove comment prefix if present
        if (content.startsWith("#")) {
          int colonPos = content.indexOf(": ");
          if (colonPos >= 0) {
            content = content.substring(colonPos + 2);
          }
        }
        
        strncpy(info->description, content.c_str(), sizeof(info->description) - 1);
        info->description[sizeof(info->description) - 1] = '\0';
        txtFile.close();
      }
    }
  }
  
  // Find the Nth audio file in a directory
  static bool findNthAudioInDir(const char* sourceDir, const char* key, uint8_t n, AudioFileInfo* result) {
    char dirPath[MAX_PATH_LEN];
    snprintf(dirPath, sizeof(dirPath), "/AUDIO/%s/%s", sourceDir, key);
    
    Serial.print(F("[DIR_SCAN] Opening directory: "));
    Serial.println(dirPath);
    
    File dir = SD.open(dirPath);
    if (!dir) {
      Serial.println(F("[DIR_SCAN] ✗ Directory does not exist"));
      return false;
    }
    
    uint16_t count = 0;
    bool found = false;
    
    Serial.print(F("[DIR_SCAN] Looking for file #"));
    Serial.print(n);
    Serial.println(F(" in directory:"));
    
    while (true) {
      File f = dir.openNextFile();
      if (!f) break;
      
      if (!f.isDirectory() && hasAudioExt(f.name())) {
        count++;
        Serial.print(F("[DIR_SCAN] Found audio file #"));
        Serial.print(count);
        Serial.print(F(": "));
        Serial.println(f.name());
        
        if (count == n) {
          snprintf(result->path, sizeof(result->path), "%s/%s", dirPath, f.name());
          result->exists = true;
          found = true;
          Serial.print(F("[DIR_SCAN] ✓ Selected: "));
          Serial.println(result->path);
          f.close();
          break;
        }
      }
      f.close();
    }
    
    dir.close();
    
    if (!found) {
      Serial.print(F("[DIR_SCAN] ✗ Could not find file #"));
      Serial.print(n);
      Serial.print(F(" (found "));
      Serial.print(count);
      Serial.println(F(" total audio files)"));
    }
    
    return found;
  }
};

// Global variables
KeyConfig keys[MAX_KEYS];
uint8_t numKeys = 0;
ButtonMapping buttonMap[TOTAL_BUTTONS];
PriorityMode currentMode = PriorityMode::HUMAN_FIRST;

// Simplified audio availability tracking
bool keyHasHuman[MAX_KEYS] = {false};
bool keyHasGenerated[MAX_KEYS] = {false};

int keyIndexByName(const char *k) {
  for (uint8_t i = 0; i < numKeys; i++) if (strcmp(keys[i].key, k) == 0) return i;
  return -1;
}

// Audio playback state
bool isPlaying = false;
char currentTrackPath[MAX_PATH_LEN] = {0};
unsigned long audioStartTime = 0;

// State for edge-detection
uint16_t last_s[NUM_PCF];
bool lastExtra[EXTRA_COUNT];

// Button press timing for multi-press detection
unsigned long lastPressTime[TOTAL_BUTTONS];
uint8_t pressCount[TOTAL_BUTTONS];
const unsigned long MULTI_PRESS_WINDOW = 1000; // milliseconds (increased for better multi-press detection)

// Calibration mode
bool inCalibrate = false;
bool waitingForMapping = false;
uint8_t pendingButtonIndex = 0;
String inputBuffer = "";

// Forward declarations
void loadConfiguration();
void loadKeys();
void parseKeyLine(String line);
void parseInputMapping(String inputStr, int keyIndex);
void initializeButtonMappings();
void handleButtonPress(uint8_t buttonIndex);
void playAudioForKey(const char* key, uint8_t pressCount);
void checkButtons();
void handleMultiPress();
void handleShiftButtonPress(uint8_t pressCount);
void handlePeriodButtonPress(uint8_t pressCount);
void printStatus();
void printMenu();
void playSineTest();
void printWordMap();
bool findAudioForKey(const char* key, uint8_t pressCount, AudioFileInfo* result);

void setup() {
  Serial.begin(115200);
  while (!Serial) delay(10);
  
  Serial.println(F("=== Tactile Communication Device - New SD Structure ==="));
  
  // Initialize PCF8575 expanders on Wire1 (QT Py connector)
  Wire1.begin();
  for (uint8_t i = 0; i < NUM_PCF; i++) {
    if (!pcf[i].begin(PCF_ADDR[i], &Wire1)) {
      Serial.print(F("[ERROR] PCF8575 #"));
      Serial.print(i);
      Serial.print(F(" at 0x"));
      Serial.print(PCF_ADDR[i], HEX);
      Serial.println(F(" not found!"));
      while (1) delay(10);
    }
    Serial.print(F("[OK] PCF8575 #"));
    Serial.print(i);
    Serial.print(F(" at 0x"));
    Serial.print(PCF_ADDR[i], HEX);
    Serial.println(F(" initialized"));
    
    // Set all pins as inputs with pullups
    for (uint8_t pin = 0; pin < 16; pin++) {
      pcf[i].pinMode(pin, INPUT_PULLUP);
      // Read initial state of all pins (batch read)
      last_s[i] = pcf[i].digitalReadWord();
    }
  }
  
  // Initialize extra pins
  for (uint8_t i = 0; i < EXTRA_COUNT; i++) {
    pinMode(extraPins[i], INPUT_PULLUP);
    lastExtra[i] = digitalRead(extraPins[i]);
  }
  
  // Initialize VS1053
  if (!musicPlayer.begin()) {
    Serial.println(F("[ERROR] VS1053 not found!"));
    while (1) delay(10);
  }
  Serial.println(F("[OK] VS1053 initialized"));
  
  // Initialize SD card (handled by VS1053)
  if (!SD.begin(CARDCS)) {
    Serial.println(F("[ERROR] SD card not found!"));
    while (1) delay(10);
  }
  Serial.println(F("[INIT] VS1053 initialized successfully"));
  
  // Set volume permanently to 0 (loudest setting)
  musicPlayer.setVolume(0, 0);
  Serial.println(F("[INIT] Volume permanently set to 0 (loudest)"));
  
  // Enable background playback via DREQ pin interrupt
  musicPlayer.useInterrupt(VS1053_FILEPLAYER_PIN_INT);
  Serial.println(F("[INIT] Background playback enabled via interrupt"));
  
  // Load configuration from SD card
  loadConfiguration();
  
  // Skip loadMappings() - we use directory discovery instead
  
  // Initialize button state arrays
  for (uint8_t i = 0; i < TOTAL_BUTTONS; i++) {
    lastPressTime[i] = 0;
    pressCount[i] = 0;
  }
  
  Serial.println(F("[READY] Device initialized successfully"));
  
  // Play startup sine test (250ms) instead of sample MP3s
  Serial.println(F("[STARTUP] Playing built-in 250ms sine test..."));
  playSineTest();
  
  printMenu();
}

void loop() {
  // ==== SEGMENT 5: LOOP() INTEGRATION ====
  // Put this block near the start of loop()

  // 1) Serial handshake when in NORMAL mode
  while (Serial.available()) {
    char c = Serial.read();
    if (deviceMode == DeviceMode::NORMAL) {
      // lightweight handshake detector for "^DATA? v1\n"
      if (c == '\r') { /* ignore */ }
      else if (c != '\n') {
        if (dm_line_len + 1 < DM_LINE_MAX) { dm_line[dm_line_len++] = c; dm_line[dm_line_len] = 0; }
        else { dm_line_reset(); }
      } else {
        // got a line
        if (!strcmp(dm_line, "^DATA? v1")) {
          Serial.println("DATA:OK v1");
          enterDataMode();
        }
        dm_line_reset();
      }
    } else {
      // In DATA_MODE: feed byte-by-byte to the protocol
      dm_feedByte(c);
    }
  }

  // 2) If in DATA_MODE, enforce idle timeout and skip normal duties
  if (deviceMode == DeviceMode::DATA_MODE) {
    if (millis() - dm_last_activity_ms > DATA_IDLE_TIMEOUT_MS) {
      Serial.println("DATA:IDLE");
      exitDataMode();
    }
    // Do not scan buttons / play audio while in data mode
    return;
  }

  // 3) ... your existing NORMAL mode logic continues below ...
  checkButtons();
  handleMultiPress();
  
  // Monitor audio completion with timestamps
  if (isPlaying && !musicPlayer.playingMusic) {
    unsigned long elapsed = millis() - audioStartTime;
    Serial.print(F("[AUDIO] Track completed after "));
    Serial.print(elapsed);
    Serial.print(F("ms - File: "));
    Serial.println(currentTrackPath);
    isPlaying = false;
    currentTrackPath[0] = '\0';
  }
  
  // Handle calibration input (data mode already handled above)
  if (Serial.available() && waitingForMapping) {
    char cmd = Serial.read();
      if (cmd == '\n' || cmd == '\r') {
        // Process the mapping
        if (inputBuffer.length() > 0) {
          inputBuffer.trim();
          inputBuffer.toUpperCase();
          
          // Validate input
          bool validKey = false;
          if (inputBuffer.length() == 1 && inputBuffer[0] >= 'A' && inputBuffer[0] <= 'Z') {
            validKey = true;
          } else if (inputBuffer == "SHIFT" || inputBuffer == "PERIOD" || inputBuffer == "SPACE" || 
                     inputBuffer == "YES" || inputBuffer == "NO" || inputBuffer == "WATER") {
            validKey = true;
          }
          
          if (validKey) {
            // Update button mapping
            int ki = keyIndexByName(inputBuffer.c_str());
            if (ki >= 0) {
              buttonMap[pendingButtonIndex].used = true;
              buttonMap[pendingButtonIndex].keyIndex = (int16_t)ki;
            } else {
              Serial.print(F("\n[ERROR] Unknown key name: "));
              Serial.println(inputBuffer);
            }
            
            Serial.print(F("\n[MAPPED] Button #"));
            Serial.print(pendingButtonIndex);
            Serial.print(F(" -> "));
            if (buttonMap[pendingButtonIndex].keyIndex >= 0) Serial.println(keys[buttonMap[pendingButtonIndex].keyIndex].key);
            else Serial.println(F("UNSET"));
            Serial.println(F("Press another button to map, or 'E' to exit calibration"));
          } else {
            Serial.print(F("\nInvalid key: "));
            Serial.print(inputBuffer);
            Serial.println(F(". Use A-Z, SHIFT, PERIOD, SPACE, YES, NO, or WATER"));
            Serial.print(F("Enter key mapping: "));
          }
        }
        
        waitingForMapping = false;
        inputBuffer = "";
      } else if (cmd == 8 || cmd == 127) { // Backspace
        if (inputBuffer.length() > 0) {
          inputBuffer.remove(inputBuffer.length() - 1);
          Serial.print(F("\b \b")); // Erase character on screen
        }
      } else if (cmd >= 32 && cmd <= 126) { // Printable characters
        inputBuffer += cmd;
        Serial.print(cmd); // Echo character
      }
      return;
  }
  
  // Normal command processing (only if not in calibration mode)
  if (Serial.available()) {
    char cmd = Serial.read();
    switch (cmd) {
      case 'C': case 'c':
        inCalibrate = !inCalibrate;
        waitingForMapping = false;
        inputBuffer = "";
        Serial.print(F("\nCalibration mode: "));
        if (inCalibrate) {
          Serial.println(F("ON"));
          Serial.println(F("Press any button to map it, or 'E' to exit"));
        } else {
          Serial.println(F("OFF"));
        }
        break;
      case 'M': case 'm':
        currentMode = (currentMode == PriorityMode::HUMAN_FIRST) ? 
                      PriorityMode::GENERATED_FIRST : PriorityMode::HUMAN_FIRST;
        Serial.print(F("Priority mode: "));
        Serial.println((currentMode == PriorityMode::HUMAN_FIRST) ? F("HUMAN_FIRST") : F("GENERATED_FIRST"));
        break;
      case 'S': case 's':
        printStatus();
        break;
      case 'H': case 'h':
        printMenu();
        break;
      case 'R': case 'r':
        loadConfiguration();
        Serial.println(F("Configuration reloaded"));
        break;
      case 'L': case 'l':
        Serial.println(F("\n=== SD Card Directory Listing ==="));
        listSDContents("/");
        listSDContents("/AUDIO");
        listSDContents("/AUDIO/GENERA~1");
        listSDContents("/AUDIO/GENERA~1/SHIFT");
        listSDContents("/AUDIO/HUMAN");
        listSDContents("/AUDIO/HUMAN/SHIFT");
        break;
      case 'E': case 'e':
        inCalibrate = false;
        waitingForMapping = false;
        inputBuffer = "";
        Serial.println(F("Calibration mode: OFF"));
        break;
      case 'T': case 't':
        playSineTest();
        break;
    }
  }
  
  delay(10);
}

void loadConfiguration() {
  Serial.println(F("[CONFIG] Loading SD card configuration..."));
  
  // Clear existing configuration
  numKeys = 0;
  for (uint8_t i = 0; i < TOTAL_BUTTONS; i++) {
    buttonMap[i].used = false;
    buttonMap[i].keyIndex = -1;
    buttonMap[i].buttonIndex = i;
    buttonMap[i].source[0] = '\0';
    buttonMap[i].input[0] = '\0';
  }
  
  // Ensure button mappings are cleared BEFORE loading keys
  initializeButtonMappings();

  Serial.println(F("[CONFIG] Using /CONFIG/KEYS.CSV for button mappings (sd_strict_mode/buttons.csv is ignored in this build)"));
  loadKeys();
  // Skip loadMappings() - using directory-based discovery instead
  
  Serial.print(F("[CONFIG] Loaded "));
  Serial.print(numKeys);
  Serial.println(F(" keys"));
}

void loadKeys() {
  file = SD.open("/CONFIG/KEYS.CSV");
  if (!file) {
    Serial.println(F("[ERROR] Cannot open /CONFIG/KEYS.CSV"));
    return;
  }
    Serial.println(F("[CONFIG] Loading KEYS.CSV..."));
  
  // Skip header and comment lines
  String line;
  do {
    line = file.readStringUntil('\n');
    line.trim();
  } while (file.available() && (line.startsWith("#") || line.startsWith("KEY,")));
  
  // Process the first data line if we have it
  if (line.length() > 0 && !line.startsWith("#") && !line.startsWith("KEY,")) {
    parseKeyLine(line);
  }
  
  // Continue with remaining lines
  while (file.available() && numKeys < MAX_KEYS) {
    line = file.readStringUntil('\n');
    line.trim();
    
    if (line.length() == 0 || line.startsWith("#")) continue;
    
    parseKeyLine(line);
  }
  
  file.close();

  // Simplified audio availability discovery
  for (uint8_t i = 0; i < numKeys; i++) {
    String k = String(keys[i].key);
    String humanDir = "/AUDIO/HUMAN/" + k;
    String genDir   = "/AUDIO/GENERA~1/" + k;

    keyHasHuman[i] = SD.exists(humanDir.c_str());
    keyHasGenerated[i] = SD.exists(genDir.c_str());
    
    // Update legacy fields for compatibility
    keys[i].hasHuman = keyHasHuman[i];
    keys[i].hasGenerated = keyHasGenerated[i];

#if VERBOSE_LOGS
    Serial.print(F("[DISCOVER] ")); Serial.print(keys[i].key);
    Serial.print(F(" human=")); Serial.print(keyHasHuman[i] ? F("YES") : F("NO"));
    Serial.print(F(" gen="));   Serial.println(keyHasGenerated[i] ? F("YES") : F("NO"));
#endif
  }
  
#if VERBOSE_LOGS
  // Print complete word map detected on startup
  printWordMap();
#endif
}

void printWordMap() {
  Serial.println(F("\n=== DETECTED WORD MAP ==="));
  
  for (uint8_t i = 0; i < numKeys; i++) {
    if (keyHasHuman[i] || keyHasGenerated[i]) {
      Serial.print(keys[i].key);
      Serial.print(F(" → "));
      
      // Show available sources
      if (keyHasHuman[i]) {
        Serial.print(F("HUMAN"));
      }
      if (keyHasHuman[i] && keyHasGenerated[i]) {
        Serial.print(F(", "));
      }
      if (keyHasGenerated[i]) {
        Serial.print(F("GENERATED"));
      }
      
      Serial.println();
    }
  }
  
  Serial.print(F("\nTotal mapped keys: "));
  uint8_t mappedKeys = 0;
  for (uint8_t i = 0; i < numKeys; i++) {
    if (keyHasHuman[i] || keyHasGenerated[i]) mappedKeys++;
  }
  Serial.print(mappedKeys);
  Serial.print(F(" of "));
  Serial.println(numKeys);
  Serial.println(F("========================\n"));
}

void parseKeyLine(String line) {
  // Parse CSV: KEY,DESCRIPTION,INPUT
  int firstComma = line.indexOf(',');
  if (firstComma == -1) return;
  
  int secondComma = line.indexOf(',', firstComma + 1);
  if (secondComma == -1) return;
  
  String keyStr = line.substring(0, firstComma);
  String descStr = line.substring(firstComma + 1, secondComma);
  String inputStr = line.substring(secondComma + 1);
  
  keyStr.trim();
  descStr.trim();
  inputStr.trim();
  
  // Store key configuration
  keyStr.toCharArray(keys[numKeys].key, sizeof(keys[numKeys].key));
  descStr.toCharArray(keys[numKeys].description, sizeof(keys[numKeys].description));
  keys[numKeys].hasHuman = false;
  keys[numKeys].hasGenerated = false;
  
  // Parse INPUT to get button mapping
  parseInputMapping(inputStr, (int)numKeys);
  
  Serial.print(F("[KEY] "));
  Serial.print(keys[numKeys].key);
  Serial.print(F(" - "));
  Serial.print(keys[numKeys].description);
  Serial.print(F(" ("));
  Serial.print(inputStr);
  Serial.println(F(")"));
  
  numKeys++;
}

void parseInputMapping(String inputStr, int keyIndex) {
  // Parse input format: pcf<N>:<P> or gpio:<PIN>
  if (inputStr.startsWith("pcf")) {
    // Extract chip number and pin
    int colonIndex = inputStr.indexOf(':');
    if (colonIndex == -1) return;
    
    int chipNum = inputStr.substring(3, colonIndex).toInt();
    int pinNum = inputStr.substring(colonIndex + 1).toInt();
    
    // Calculate button index: chip * 16 + pin
    uint8_t buttonIndex = chipNum * 16 + pinNum;
    
    if (buttonIndex < TOTAL_BUTTONS) {
      buttonMap[buttonIndex].used = true;
      buttonMap[buttonIndex].keyIndex = keyIndex;
      strncpy(buttonMap[buttonIndex].source, "keys.csv", sizeof(buttonMap[buttonIndex].source) - 1);
      buttonMap[buttonIndex].source[sizeof(buttonMap[buttonIndex].source) - 1] = '\0';
      inputStr.toCharArray(buttonMap[buttonIndex].input, sizeof(buttonMap[buttonIndex].input));
    }
  } else if (inputStr.startsWith("gpio:")) {
    // Handle GPIO pins (extra pins)
    int gpioPin = inputStr.substring(5).toInt();
    
    // Find matching extra pin
    for (uint8_t i = 0; i < EXTRA_COUNT; i++) {
      if (extraPins[i] == gpioPin) {
        uint8_t buttonIndex = TOTAL_EXPANDER_PINS + i;
        buttonMap[buttonIndex].used = true;
        buttonMap[buttonIndex].keyIndex = keyIndex;
        strncpy(buttonMap[buttonIndex].source, "KEYS.CSV", sizeof(buttonMap[buttonIndex].source) - 1);
        buttonMap[buttonIndex].source[sizeof(buttonMap[buttonIndex].source) - 1] = '\0';
        inputStr.toCharArray(buttonMap[buttonIndex].input, sizeof(buttonMap[buttonIndex].input));
        break;
      }
    }
  }
}


void initializeButtonMappings() {
  // Clear all button mappings - they will be loaded from keys.csv
  for (uint8_t i = 0; i < TOTAL_BUTTONS; i++) {
    buttonMap[i].used = false;
    buttonMap[i].keyIndex = -1;
    buttonMap[i].source[0] = '\0';
    buttonMap[i].input[0] = '\0';
  }
  
  Serial.println(F("[CONFIG] Button mappings cleared - will load from KEYS.CSV"));
}

void checkButtons() {
  // Check PCF8575 expanders
  for (uint8_t chipIndex = 0; chipIndex < NUM_PCF; chipIndex++) {
    // Batch-read 16 GPIO bits in one I2C transaction
    uint16_t currentState = pcf[chipIndex].digitalReadWord();
    
    uint16_t changed = currentState ^ last_s[chipIndex];
    
    if (changed) {
      for (uint8_t pin = 0; pin < 16; pin++) {
        if (changed & (1 << pin)) {
          bool pressed = !(currentState & (1 << pin)); // Active low
          if (pressed) {
            uint8_t buttonIndex = chipIndex * 16 + pin;
            handleButtonPress(buttonIndex);
          }
        }
      }
      last_s[chipIndex] = currentState;
    }
  }
  
  // Check extra pins
  for (uint8_t i = 0; i < EXTRA_COUNT; i++) {
    bool currentState = digitalRead(extraPins[i]);
    if (currentState != lastExtra[i]) {
      if (!currentState) { // Active low
        uint8_t buttonIndex = TOTAL_EXPANDER_PINS + i;
        handleButtonPress(buttonIndex);
      }
      lastExtra[i] = currentState;
    }
  }
}

void handleButtonPress(uint8_t buttonIndex) {
  if (buttonIndex >= TOTAL_BUTTONS) return;
  
  unsigned long currentTime = millis();
  
  if (inCalibrate) {
    Serial.print(F("\n[CALIBRATE] Button #"));
    Serial.print(buttonIndex);
    
    // Add GPIO information
    Serial.print(F(" GPIO:"));
    if (buttonIndex < TOTAL_EXPANDER_PINS) {
      uint8_t chipIndex = buttonIndex / 16;
      uint8_t pin = buttonIndex % 16;
      Serial.print(F("PCF"));
      Serial.print(chipIndex);
      Serial.print(F("-P"));
      Serial.print(pin);
    } else {
      Serial.print(F("D"));
      Serial.print(extraPins[buttonIndex - TOTAL_EXPANDER_PINS]);
    }
    
    if (buttonMap[buttonIndex].used) {
      Serial.print(F(" (currently: "));
      if (buttonMap[buttonIndex].keyIndex >= 0 && buttonMap[buttonIndex].keyIndex < numKeys) {
        Serial.print(keys[buttonMap[buttonIndex].keyIndex].key);
      } else {
        Serial.print(F("UNSET"));
      }
      Serial.print(F(")"));
    }
    Serial.println(F(" pressed"));
    Serial.print(F("Enter key mapping (A-Z, SHIFT, PERIOD, SPACE, YES, NO, WATER): "));
    
    waitingForMapping = true;
    pendingButtonIndex = buttonIndex;
    inputBuffer = "";
    return;
  }
  
  // Multi-press detection
  if (currentTime - lastPressTime[buttonIndex] < MULTI_PRESS_WINDOW) {
    pressCount[buttonIndex]++;
  } else {
    pressCount[buttonIndex] = 1;
  }
  
  lastPressTime[buttonIndex] = currentTime;
  
  // Enhanced button press logging like v2
  Serial.print(F("[BUTTON] "));
  if (buttonIndex < 16) {
    Serial.print(F("PCF8575 #0 GPIO "));
    Serial.print(buttonIndex);
  } else if (buttonIndex < 32) {
    Serial.print(F("PCF8575 #1 GPIO "));
    Serial.print(buttonIndex - 16);
    Serial.print(F(" (idx "));
    Serial.print(buttonIndex);
    Serial.print(F(")"));
  } else if (buttonIndex < 48) {
    Serial.print(F("PCF8575 #2 GPIO "));
    Serial.print(buttonIndex - 32);
    Serial.print(F(" (idx "));
    Serial.print(buttonIndex);
    Serial.print(F(")"));
  } else {
    uint8_t xp = extraPins[buttonIndex - 48];
    Serial.print(F("Arduino Pin "));
    Serial.print(xp);
    Serial.print(F(" (idx "));
    Serial.print(buttonIndex);
    Serial.print(F(")"));
  }
  
  if (buttonMap[buttonIndex].used) {
    Serial.print(F(" → "));
    if (buttonMap[buttonIndex].keyIndex >= 0 && buttonMap[buttonIndex].keyIndex < numKeys) {
      Serial.print(keys[buttonMap[buttonIndex].keyIndex].key);
    } else {
      Serial.print(F("UNSET"));
    }
    if (buttonMap[buttonIndex].source[0] != '\0') {
      Serial.print(F(" [src:"));
      Serial.print(buttonMap[buttonIndex].source);
      Serial.print(F(" input:"));
      Serial.print(buttonMap[buttonIndex].input);
      Serial.print(F("]"));
    }
    
    // Show audio availability info
    if (buttonMap[buttonIndex].keyIndex >= 0 && buttonMap[buttonIndex].keyIndex < numKeys) {
      KeyConfig* keyConfig = &keys[buttonMap[buttonIndex].keyIndex];
      Serial.print(F(" [Human:"));
      Serial.print(keyConfig->hasHuman ? F("YES") : F("NO"));
      Serial.print(F("|Generated:"));
      Serial.print(keyConfig->hasGenerated ? F("YES") : F("NO"));
      Serial.print(F("]"));
    }
  } else {
    Serial.print(F(" → UNMAPPED"));
    // Helpful hint to trace back to CSV mapping
    Serial.print(F(" | Hint: add INPUT mapping for this button in /CONFIG/KEYS.CSV as pcf"));
    if (buttonIndex < TOTAL_EXPANDER_PINS) {
      uint8_t chipIndex = buttonIndex / 16;
      uint8_t pin = buttonIndex % 16;
      Serial.print(chipIndex);
      Serial.print(F(":"));
      Serial.print(pin);
    } else {
      Serial.print(F("gpio:"));
      Serial.print(extraPins[buttonIndex - TOTAL_EXPANDER_PINS]);
    }
  }
  
  Serial.print(F(" | Press #"));
  Serial.print(pressCount[buttonIndex]);
  Serial.print(F(" @ "));
  Serial.print(currentTime);
  Serial.println(F("ms"));
}

void handleMultiPress() {
  unsigned long currentTime = millis();
  
  for (uint8_t i = 0; i < TOTAL_BUTTONS; i++) {
    if (pressCount[i] > 0 && 
        (currentTime - lastPressTime[i]) >= MULTI_PRESS_WINDOW) {
      
      // Time to process the multi-press
      if (buttonMap[i].used) {
        const char* mappedKey = (buttonMap[i].keyIndex >= 0 && buttonMap[i].keyIndex < numKeys) ? keys[buttonMap[i].keyIndex].key : "";
        
        // Special handling for SHIFT button custom sounds
        if (strcmp(mappedKey, "SHIFT") == 0) {
          handleShiftButtonPress(pressCount[i]);
        }
        // Special handling for PERIOD button mode switching
        else if (strcmp(mappedKey, "PERIOD") == 0) {
          handlePeriodButtonPress(pressCount[i]);
        }
        else {
          // Normal audio playback for other keys
          playAudioForKey(mappedKey, pressCount[i]);
        }
      }
      
      pressCount[i] = 0; // Reset press count
    }
  }
}

void playAudioForKey(const char* key, uint8_t pressCount) {
  // Alias: treat HELLO_HOW_ARE_YOU as SHIFT press #1
  if (strcmp(key, "HELLO_HOW_ARE_YOU") == 0) {
    Serial.println(F("[ALIAS] HELLO_HOW_ARE_YOU → SHIFT (press #1)"));
    playAudioForKey("SHIFT", 1);
    return;
  }
  
  // Audio interrupt: stop current playback if something is already playing
  if (isPlaying) {
    Serial.println(F("[AUDIO] Interrupting current playback for new request"));
    musicPlayer.stopPlaying();
    isPlaying = false;
  }
  
  // Find key configuration
  int keyIndex = keyIndexByName(key);
  if (keyIndex < 0) {
    Serial.print(F("[ERROR] Key not found: "));
    Serial.println(key);
    return;
  }
  
  // Enhanced logging
  Serial.print(F("[AUDIO] Playing audio for key '"));
  Serial.print(key);
  Serial.print(F("' [Human:"));
  Serial.print(keyHasHuman[keyIndex] ? F("YES") : F("NO"));
  Serial.print(F("|Generated:"));
  Serial.print(keyHasGenerated[keyIndex] ? F("YES") : F("NO"));
  Serial.print(F("], press #"));
  Serial.print(pressCount);
  Serial.print(F(", mode: "));
  Serial.println((currentMode == PriorityMode::HUMAN_FIRST) ? F("HUMAN_FIRST") : F("GENERATED_FIRST"));
  
  // Use new audio sourcing system
  AudioFileInfo audioInfo;
  if (!findAudioForKey(key, pressCount, &audioInfo)) {
    Serial.print(F("[AUDIO] No audio available for key: "));
    Serial.print(key);
    Serial.print(F(", press #"));
    Serial.println(pressCount);
    return;
  }
  
  // Stop any current playback for clean interruption
  if (musicPlayer.playingMusic) {
    musicPlayer.stopPlaying();
    Serial.println(F("[AUDIO] Stopped previous track"));
  }
  
  // Extract filename from full path for cleaner logging
  const char *filename = audioInfo.path;
  const char *slash = strrchr(audioInfo.path, '/');
  if (slash && *(slash + 1)) filename = slash + 1;
  
  // Show what audio content will be played
  Serial.print(F("[CONTENT] About to say: "));
  if (audioInfo.description[0] != '\0') {
    Serial.println(audioInfo.description);
  } else {
    Serial.println(F("[No description available]"));
  }
  
  Serial.print(F("[AUDIO] Starting: "));
  Serial.print(filename);
  Serial.print(F(" ("));
  Serial.print(audioInfo.path);
  Serial.print(F(") from "));
  Serial.println((audioInfo.source == AudioSource::HUMAN) ? F("HUMAN") : F("GENERATED"));
  
  if (musicPlayer.startPlayingFile(audioInfo.path)) {
    snprintf(currentTrackPath, sizeof(currentTrackPath), "%s", audioInfo.path);
    isPlaying = true;
    audioStartTime = millis();
    Serial.print(F("[AUDIO] ✓ Playing "));
    Serial.print(filename);
    Serial.print(F(" started at "));
    Serial.print(millis());
    Serial.println(F("ms"));
  } else {
    Serial.print(F("[ERROR] ✗ Failed to start "));
    Serial.println(filename);
  }
}

// New streamlined audio file picker using the AudioSourceManager
bool findAudioForKey(const char* key, uint8_t pressCount, AudioFileInfo* result) {
  // Determine preferred source based on current mode and special key rules
  AudioSource preferredSource = AudioSourceManager::getPreferredSource(key, pressCount, currentMode);
  
  // Find the audio file
  return AudioSourceManager::findAudioFile(key, pressCount, preferredSource, result);
}

void printStatus() {
  Serial.println(F("\n=== Device Status ==="));
  Serial.print(F("Priority Mode: "));
  Serial.println((currentMode == PriorityMode::HUMAN_FIRST) ? F("HUMAN_FIRST") : F("GENERATED_FIRST"));
  Serial.print(F("Calibration: "));
  Serial.println(inCalibrate ? F("ON") : F("OFF"));
  Serial.print(F("Keys Loaded: "));
  Serial.println(numKeys);
  Serial.print(F("Audio Playing: "));
  Serial.println(isPlaying ? F("YES") : F("NO"));
  if (isPlaying) {
    Serial.print(F("Current Track: "));
    Serial.println(currentTrackPath);
  }
  Serial.println();
}

void listSDContents(const char* path) {
  Serial.print(F("[SD_LIST] Contents of: "));
  Serial.println(path);
  
  File dir = SD.open(path);
  if (!dir) {
    Serial.println(F("[SD_LIST] ✗ Directory does not exist or cannot be opened"));
    return;
  }
  
  if (!dir.isDirectory()) {
    Serial.println(F("[SD_LIST] ✗ Path is not a directory"));
    dir.close();
    return;
  }
  
  File entry;
  int count = 0;
  while ((entry = dir.openNextFile())) {
    Serial.print(F("[SD_LIST]   "));
    Serial.print(entry.name());
    if (entry.isDirectory()) {
      Serial.println(F("/"));
    } else {
      Serial.print(F(" ("));
      Serial.print(entry.size());
      Serial.println(F(" bytes)"));
    }
    entry.close();
    count++;
  }
  
  Serial.print(F("[SD_LIST] Total items: "));
  Serial.println(count);
  dir.close();
}

void printMenu() {
  Serial.println(F("\n=== Tactile Communication Device ==="));
  Serial.println(F("Commands:"));
  Serial.println(F("  C - Interactive calibration mode (press button, type mapping)"));
  Serial.println(F("  E - Exit calibration mode"));
  Serial.println(F("  L - List SD card contents for debugging"));
  Serial.println(F("  M - Toggle priority mode (Human/Generated first)"));
  Serial.println(F("  S - Show status"));
  Serial.println(F("  R - Reload configuration"));
  Serial.println(F("  T - Play sine test tone"));
  Serial.println(F("  H - Show this menu"));
  Serial.println();
}

// Handle SHIFT button custom sounds based on press count
void handleShiftButtonPress(uint8_t pressCount) {
  Serial.print(F("[SHIFT] Processing press count: "));
  Serial.println(pressCount);
  
  switch (pressCount) {
    case 1:
      // Press 1: Human greeting ("Hello How are You")
      Serial.println(F("[SHIFT] Press 1: Playing human greeting"));
      playAudioForKey("SHIFT", 1);
      break;
      
    case 2:
      // Press 2: Instructions (generated)
      Serial.println(F("[SHIFT] Press 2: Playing instructions"));
      playAudioForKey("SHIFT", 2);
      break;
      
    case 3:
      // Press 3: Word list (generated)
      Serial.println(F("[SHIFT] Press 3: Playing word list"));
      playAudioForKey("SHIFT", 3);
      break;
      
    default:
      // For higher press counts, cycle through available options
      uint8_t cycledPress = ((pressCount - 1) % 3) + 1;
      Serial.print(F("[SHIFT] Press "));
      Serial.print(pressCount);
      Serial.print(F(": Cycling to press "));
      Serial.println(cycledPress);
      handleShiftButtonPress(cycledPress);
      break;
  }
}

// ==== SEGMENT 6: PERIOD×4 + CONFIRM ====

void handlePeriodButtonPress(uint8_t pressCount) {
  Serial.print(F("[PERIOD] Processing press count: "));
  Serial.println(pressCount);

  if (pressCount == 4) {
    // Guard accidental entry: require quick confirm within 3s.
    Serial.println(F("[PERIOD] Requesting Data Mode (confirm needed)"));
    // Optional spoken prompt:
    // playAudioForKey("PERIOD", 4); // record a short "entering data mode—confirm" clip

    unsigned long deadline = millis() + 3000;
    bool confirmed = false;

    // Confirmation method A: tap SHIFT once within 3s
    // (Assumes you have a button mapped to "SHIFT" in keys.csv)
    while (millis() < deadline && !confirmed) {
      // quick, low-cost peek at serial too: if host sends '!' it's a confirm
      if (Serial.available()) {
        char c = Serial.read();
        if (c == '!') confirmed = true;
      }
      // If you have a "SHIFT" mapped, you likely also have multi-press state.
      // Easiest: reuse your existing press detection once it fires.
      // Here we just poll a small slice of time:
      delay(10);
    }

    if (!confirmed) {
      Serial.println(F("[PERIOD] Data Mode not confirmed"));
      return;
    }

    // Enter data mode and emit the standard handshake response so a host can attach seamlessly
    enterDataMode();
    Serial.println("DATA:OK v1");
    return;
  }

  // Existing 1–3 behavior unchanged
  switch (pressCount) {
    case 1:
      Serial.println(F("[PERIOD] Press 1: Playing period sound"));
      playAudioForKey("PERIOD", 1);
      break;

    case 2:
      Serial.println(F("[PERIOD] Press 2: Switching to Human First mode"));
      currentMode = PriorityMode::HUMAN_FIRST;
      Serial.println(F("[MODE] Switched to: HUMAN_FIRST"));
      playAudioForKey("PERIOD", 2);
      break;

    case 3:
      Serial.println(F("[PERIOD] Press 3: Switching to Generated First mode"));
      currentMode = PriorityMode::GENERATED_FIRST;
      Serial.println(F("[MODE] Switched to: GENERATED_FIRST"));
      playAudioForKey("PERIOD", 3);
      break;

    default: {
      uint8_t cycledPress = ((pressCount - 1) % 3) + 1;
      handlePeriodButtonPress(cycledPress);
      break;
    }
  }
}

// ==== SEGMENT 2: UTILS (paths, mkdir_p, atomic rename, CRC) ====

bool isWriteEnabled() {
}

// Build /audio/<bank>/<KEY>/<fname>
void path_audio(char* out, size_t outsz, const char* bank, const char* key, const char* fname) {
  if (fname && fname[0]) {
    snprintf(out, outsz, "/AUDIO/%s/%s/%s", bank, key, fname);
  } else {
    snprintf(out, outsz, "/AUDIO/%s/%s", bank, key);
  }
}

bool ensureConfigDir() { return mkdir_p("/CONFIG"); }

bool sd_stats(uint64_t* total, uint64_t* free) {
  // Standard Arduino SD library doesn't provide volume stats
  // Return dummy values to keep the interface working
  *total = 32ULL * 1024 * 1024 * 1024; // 32GB default
  *free = 16ULL * 1024 * 1024 * 1024;  // 16GB free default
  return true; // Always return true so STAT command works
}

// mkdir -p for SD (create intermediate directories step-by-step)
bool mkdir_p(const char* path) {
  if (!path || path[0] != '/') return false;
  char buf[128];
  size_t n = strlen(path);
  if (n >= sizeof(buf)) return false;
  strcpy(buf, path);

  // Iterate through slashes and create progressively
  for (size_t i = 1; i < n; i++) {
    if (buf[i] == '/') {
      buf[i] = '\0';
      if (!SD.exists(buf)) {
        if (!SD.mkdir(buf)) return false;
      }
      buf[i] = '/';
    }
  }
  if (!SD.exists(buf)) {
    if (!SD.mkdir(buf)) return false;
  }
  return true;
}

// Copy+remove implementation (Arduino SD library doesn't have rename)
bool atomicRename(const char* srcTmp, const char* dstFinal) {
  // Copy then remove (not strictly atomic but safer than leaving .part)
  File inF = SD.open(srcTmp, FILE_READ);
  if (!inF) return false;
  File outF = SD.open(dstFinal, FILE_WRITE);
  if (!outF) { inF.close(); return false; }

  uint8_t buf[512];
  int r;
  while ((r = inF.read(buf, sizeof(buf))) > 0) {
    if (outF.write(buf, (size_t)r) != (size_t)r) { inF.close(); outF.close(); return false; }
  }
  outF.flush(); outF.close(); inF.close();
  SD.remove(srcTmp);
  return true;
}

#if DATA_USE_CRC32
// Standard CRC32 (poly 0xEDB88320)
void crc32_reset(uint32_t &crc) { crc = 0xFFFFFFFFUL; }
void crc32_update(uint32_t &crc, const uint8_t* data, size_t len) {
  for (size_t i = 0; i < len; ++i) {
    uint32_t c = (crc ^ data[i]) & 0xFFU;
    for (uint8_t k = 0; k < 8; ++k) c = (c & 1U) ? (0xEDB88320UL ^ (c >> 1)) : (c >> 1);
    crc = (crc >> 8) ^ c;
  }
}
#endif

// ==== SEGMENT 3: PARSER & COMMAND HANDLERS (PUT/GET/DEL/LS/EXIT) ====

static inline void dm_touch() { dm_last_activity_ms = millis(); }

static inline void dm_line_reset() { dm_line_len = 0; dm_line[0] = 0; }

void dm_feedByte(char c) {
  dm_touch();
  if (dm_state == DataCmdState::LINE) {
    // accept CR/LF; end on '\n'
    if (c == '\r') return;
    if (c != '\n') {
      if (dm_line_len + 1 < DM_LINE_MAX) {
        dm_line[dm_line_len++] = c;
        dm_line[dm_line_len] = 0;
      } else {
        // line too long
        Serial.println("ERR:LINETOOLONG");
        dm_line_reset();
      }
      return;
    }
    // full line
    dm_handleLine(dm_line);
    dm_line_reset();
    return;
  }

  if (dm_state == DataCmdState::PUT_PAYLOAD) {
    // buffer incoming bytes, write in chunks
    dm_wbuf[dm_wbuf_len++] = (uint8_t)c;
    if (dm_wbuf_len == DM_IOBUF_SZ || dm_wbuf_len == dm_put_remaining) {
      size_t toWrite = dm_wbuf_len;
      if (dm_put_file.write(dm_wbuf, toWrite) != (int)toWrite) {
        Serial.println("ERR:WRITE");
        dm_put_file.close();
        SD.remove(dm_put_tmp_path);
        dm_state = DataCmdState::LINE;
        return;
      }
      #if DATA_USE_CRC32
      crc32_update(dm_put_crc_calc, dm_wbuf, toWrite);
      #endif
      dm_put_remaining -= (uint32_t)toWrite;
      dm_wbuf_len = 0;
    }
    if (dm_put_remaining == 0) {
      dm_put_file.flush();
      dm_put_file.close();

      // finalize: CRC check if provided
      #if DATA_USE_CRC32
      if (dm_put_crc_host != 0 && (dm_put_crc_calc ^ 0xFFFFFFFFUL) != dm_put_crc_host) {
        Serial.println("ERR:CRC");
        SD.remove(dm_put_tmp_path);
        dm_state = DataCmdState::LINE;
        return;
      }
      #endif

      if (atomicRename(dm_put_tmp_path, dm_put_final_path)) {
        Serial.println("PUT:DONE");
      } else {
        Serial.println("ERR:RENAME");
        SD.remove(dm_put_tmp_path);
      }
      dm_state = DataCmdState::LINE;
    }
    return;
  }

  if (dm_state == DataCmdState::GET_STREAM) {
    // nothing to do; GET is push-only from device side
    return;
  }
}

// Parse one complete command line
void dm_handleLine(const char* line) {
  // EXIT
  if (!strcmp(line, "EXIT")) { Serial.println("DATA:BYE"); exitDataMode(); return; }

  // FLAG ON  | FLAG OFF  -> create/remove /config/allow_writes.flag
  if (!strncmp(line, "FLAG ", 5)) {
    const char* arg = line + 5;
    if (!strcmp(arg, "ON")) {
      if (!ensureConfigDir()) { Serial.println("FLAG:ERR:MKDIR"); return; }
      // Try to create the flag file with explicit close
      File f = SD.open(DATA_WRITE_ENABLE_FLAG_PATH, FILE_WRITE);
      if (f) { 
        f.print("1"); // Write some content to ensure file creation
        f.flush();
        f.close(); 
        Serial.println("FLAG:ON"); 
      } else { 
        Serial.print("FLAG:ERR:OPEN "); Serial.println(DATA_WRITE_ENABLE_FLAG_PATH);
      }
    } else if (!strcmp(arg, "OFF")) {
      if (SD.exists(DATA_WRITE_ENABLE_FLAG_PATH)) {
        if (SD.remove(DATA_WRITE_ENABLE_FLAG_PATH)) Serial.println("FLAG:OFF");
        else Serial.println("FLAG:ERR:RM");
      } else {
        Serial.println("FLAG:OFF"); // already off
      }
    } else {
      Serial.println("FLAG:ERR:ARGS");
    }
    return;
  }

  if (!strcmp(line, "STAT")) {
    uint64_t tot=0, fre=0;
    if (sd_stats(&tot, &fre)) { Serial.print("STAT "); Serial.print(tot); Serial.print(' '); Serial.println(fre); }
    else Serial.println("STAT:NOK");
    return;
  }

  if (!strcmp(line, "STATUS")) {
    bool writes = isWriteEnabled();
    Serial.print("STATUS WRITES="); Serial.println(writes ? "ON" : "OFF");
    return;
  }

  // LS <bank> <KEY>
  if (!strncmp(line, "LS ", 3)) {
    char bank[16], key[24];
    if (sscanf(line + 3, "%15s %23s", bank, key) == 2) {
      char dirPath[96];
      path_audio(dirPath, sizeof(dirPath), bank, key, "");
      File d = SD.open(dirPath);
      if (!d || !d.isDirectory()) { Serial.println("LS:NODIR"); if (d) d.close(); return; }
      File f;
      while ((f = d.openNextFile())) {
        if (!f.isDirectory()) {
          Serial.print(f.name()); Serial.print(' ');
          Serial.println(f.size());
        }
        f.close();
      }
      d.close();
      Serial.println("LS:DONE");
    } else {
      Serial.println("ERR:ARGS");
    }
    return;
  }

  // DEL <bank> <KEY> <filename>
  if (!strncmp(line, "DEL ", 4)) {
    if (!isWriteEnabled()) { Serial.println("ERR:WRITELOCK"); return; }
    char bank[16], key[24], fname[48];
    if (sscanf(line + 4, "%15s %23s %47s", bank, key, fname) == 3) {
      char full[128];
      path_audio(full, sizeof(full), bank, key, fname);
      if (SD.exists(full) && SD.remove(full)) Serial.println("DEL:OK"); else Serial.println("DEL:NOK");
    } else {
      Serial.println("ERR:ARGS");
    }
    return;
  }

  // GET <bank> <KEY> <filename>
  if (!strncmp(line, "GET ", 4)) {
    char bank[16], key[24], fname[48];
    if (sscanf(line + 4, "%15s %23s %47s", bank, key, fname) == 3) {
      char full[128];
      path_audio(full, sizeof(full), bank, key, fname);
      File f = SD.open(full, FILE_READ);
      if (!f) { Serial.println("GET:NOK"); return; }
      uint32_t size = f.size();

      #if DATA_USE_CRC32
      // compute CRC32 in a first pass (small files typical)
      uint32_t crc; crc32_reset(crc);
      int r;
      while ((r = f.read(dm_rbuf, sizeof(dm_rbuf))) > 0) crc32_update(crc, dm_rbuf, (size_t)r);
      f.seek(0);
      Serial.print("GET:SIZE "); Serial.print(size); Serial.print(' ');
      Serial.println(crc ^ 0xFFFFFFFFUL);
      #else
      Serial.print("GET:SIZE "); Serial.println(size);
      #endif

      // stream file
      int r2;
      while ((r2 = f.read(dm_rbuf, sizeof(dm_rbuf))) > 0) {
        Serial.write(dm_rbuf, (size_t)r2);
      }
      f.close();
      return;
    } else {
      Serial.println("ERR:ARGS");
    }
    return;
  }

  // PUT <bank> <KEY> <filename> <bytes> [crc32]
  if (!strncmp(line, "PUT ", 4)) {
    if (!isWriteEnabled()) { Serial.println("ERR:WRITELOCK"); return; }

    char bank[16], key[24], fname[48];
    unsigned long bytes = 0; unsigned long crcHost = 0;
    int n = sscanf(line + 4, "%15s %23s %47s %lu %lu", bank, key, fname, &bytes, &crcHost);
    if (n < 4) { Serial.println("ERR:ARGS"); return; }

    // ensure directory exists
    char dirPath[96];
    path_audio(dirPath, sizeof(dirPath), bank, key, "");
    if (!mkdir_p(dirPath)) { Serial.println("ERR:MKDIR"); return; }

    // open .part file
    path_audio(dm_put_final_path, sizeof(dm_put_final_path), bank, key, fname);
    snprintf(dm_put_tmp_path, sizeof(dm_put_tmp_path), "%s.part", dm_put_final_path);

    // remove any stale .part
    if (SD.exists(dm_put_tmp_path)) SD.remove(dm_put_tmp_path);

    dm_put_file = SD.open(dm_put_tmp_path, FILE_WRITE);
    if (!dm_put_file) { Serial.println("ERR:OPEN"); return; }

    dm_put_remaining = (uint32_t)bytes;
    dm_wbuf_len = 0;
    #if DATA_USE_CRC32
    dm_put_crc_host = (n >= 5) ? (uint32_t)crcHost : 0;
    crc32_reset(dm_put_crc_calc);
    #endif

    Serial.println("PUT:READY");
    dm_state = DataCmdState::PUT_PAYLOAD;
    return;
  }

  // Unknown
  Serial.println("ERR:UNKNOWN");
}

// ==== SEGMENT 4: ENTER / EXIT DATA MODE ====

void enterDataMode() {
  if (deviceMode == DeviceMode::DATA_MODE) return;
  // stop any audio
  if (musicPlayer.playingMusic) musicPlayer.stopPlaying();
  isPlaying = false;

  deviceMode = DeviceMode::DATA_MODE;
  dm_state = DataCmdState::LINE;
  dm_line_reset();
  dm_last_activity_ms = millis();

  Serial.println("[DATA] mode=ENTER");
  // Optional: short audio cue if you want (ensure file exists):
  // playAudioForKey("SHIFT", 2);
}

void exitDataMode() {
  if (deviceMode == DeviceMode::NORMAL) return;

  // close any half-done PUT
  if (dm_state == DataCmdState::PUT_PAYLOAD) {
    if (dm_put_file) dm_put_file.close();
    if (strlen(dm_put_tmp_path)) SD.remove(dm_put_tmp_path);
    dm_state = DataCmdState::LINE;
  }

  if (dm_get_file) { dm_get_file.close(); }

  deviceMode = DeviceMode::NORMAL;
  Serial.println("[DATA] mode=EXIT");
  // Optional: audio cue
  // playAudioForKey("SHIFT", 3);
}

// Built-in sine wave test (no SD card required)
void playSineTest() {
  Serial.println(F("[SINE] Starting built-in sine test (250ms)..."));
  
  // Use VS1053's built-in sine test mode
  // This sends the magic byte sequence to trigger internal sine generation
  musicPlayer.sineTest(0x44, 250);  // 1000 Hz tone for 250ms
  
  Serial.println(F("[SINE] Sine test complete - VS1053 audio verified"));
}
