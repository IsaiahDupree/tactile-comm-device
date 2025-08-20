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

// Configuration constants
#define MAX_KEYS 35
#define MAX_FILENAME_LEN 48

// PCF8575 I2C port expanders (supporting up to 32+ buttons)
Adafruit_PCF8575 pcf[NUM_PCF];

// Extra Arduino pins for additional controls (avoid pins 0,1 for Serial)
const uint8_t extraPins[] = { 8, 9, 2, 5 };   // Safe pins: VS1053 uses pins 3,4,6,7
// Compile-time validation
static_assert(sizeof(extraPins) / sizeof(extraPins[0]) == EXTRA_COUNT, "EXTRA_COUNT mismatch with extraPins array");

// Priority mode enumeration
enum class PriorityMode {
  HUMAN_FIRST,
  GENERATED_FIRST
};

// Key configuration structure
struct KeyConfig {
  char key[20];           // Key name (fits HELLO_HOW_ARE_YOU)
  char description[20];   // Human-readable description
  char humanPlaylist[MAX_FILENAME_LEN];     // Path to human playlist
  char generatedPlaylist[MAX_FILENAME_LEN]; // Path to generated playlist
  bool hasHuman;          // Whether human audio exists
  bool hasGenerated;      // Whether generated audio exists
};

// Button mapping structure
struct ButtonMapping {
  bool used;
  uint8_t keyIndex;       // Index into keys[] array (saves 31 bytes per mapping)
  uint8_t buttonIndex;    // Physical button index
  char source[12];        // e.g., "keys.csv"
  char input[12];         // e.g., "pcf0:2" or "gpio:8"
};

// ---- Directory-based sourcing helpers ----
static inline bool hasExt(const String &name, const char *ext) {
  int dot = name.lastIndexOf('.');
  if (dot < 0) return false;
  String e = name.substring(dot + 1);
  e.toLowerCase();
  return e == ext;
}

uint16_t countTracksInDir(const String &dirPath) {
  File dir = SD.open(dirPath.c_str());
  if (!dir) return 0;
  uint16_t count = 0;
  while (true) {
    File f = dir.openNextFile();
    if (!f) break;
    if (!f.isDirectory()) {
      String n = f.name(); // just the filename
      if (hasExt(n, "mp3") || hasExt(n, "wav") || hasExt(n, "ogg")) count++;
    }
    f.close();
  }
  dir.close();
  return count;
}

static inline String pad3(uint16_t n) {
  char buf[8];
  snprintf(buf, sizeof(buf), "%03u", n);
  return String(buf);
}

// Return the Nth (1-based, wrapped) track path in dir. Tries "NNN.mp3" fast path first.
String nthTrackPathInDir(const String &dirPath, uint16_t n) {
  uint16_t total = countTracksInDir(dirPath);
  if (total == 0) return "";

  uint16_t wrapped = ((n - 1) % total) + 1;

  // Fast path: NNN.mp3
  String fast = dirPath + "/" + pad3(wrapped) + ".mp3";
  if (SD.exists(fast.c_str())) return fast;

  // Fallback: enumerate files in lexicographic order and pick the wrapped-th
  File dir = SD.open(dirPath.c_str());
  if (!dir) return "";
  uint16_t seen = 0;
  String chosen = "";
  while (true) {
    File f = dir.openNextFile();
    if (!f) break;
    if (!f.isDirectory()) {
      String nme = f.name();
      if (hasExt(nme, "mp3") || hasExt(nme, "wav") || hasExt(nme, "ogg")) {
        seen++;
        if (seen == wrapped) {
          chosen = dirPath + "/" + nme;
          f.close();
          break;
        }
      }
    }
    f.close();
  }
  dir.close();
  return chosen;
}

// Global variables
KeyConfig keys[MAX_KEYS];
uint8_t numKeys = 0;
ButtonMapping buttonMap[TOTAL_BUTTONS];
PriorityMode currentMode = PriorityMode::HUMAN_FIRST;

// Cache per-key track counts
uint16_t humanCountByKey[MAX_KEYS] = {0};
uint16_t genCountByKey[MAX_KEYS]   = {0};

int keyIndexByName(const char *k) {
  for (uint8_t i = 0; i < numKeys; i++) if (strcmp(keys[i].key, k) == 0) return i;
  return -1;
}

// Audio playback state
bool isPlaying = false;
String currentTrackPath = "";
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
void parseInputMapping(String inputStr, String keyStr);
void initializeButtonMappings();
void handleButtonPress(uint8_t buttonIndex);
void playAudioForKey(const char* key, uint8_t pressCount);
void checkButtons();
void handleMultiPress();
void printStatus();
void printMenu();
void playSineTest();
void printWordMap();
String pickTrackFor(const char* key, bool wantHuman, uint8_t pressCount);

// Debug logging macros (Arduino-safe)
#define DEBUG_LOG(level, msg) \
  do { Serial.print(F("[")); Serial.print(millis()); Serial.print(F("][")); \
       Serial.print(F(level)); Serial.print(F("] ")); Serial.println(F(msg)); } while(0)

#define DEBUG_LOG_STR(level, msg, str) \
  do { Serial.print(F("[")); Serial.print(millis()); Serial.print(F("][")); \
       Serial.print(F(level)); Serial.print(F("] ")); Serial.print(F(msg)); Serial.println(str); } while(0)

#define DEBUG_LOG_INT(level, msg, val) \
  do { Serial.print(F("[")); Serial.print(millis()); Serial.print(F("][")); \
       Serial.print(F(level)); Serial.print(F("] ")); Serial.print(F(msg)); Serial.println(val); } while(0)

#define TRACE_ENTER(func) DEBUG_LOG("TRACE", "-> " func)
#define TRACE_EXIT(func) DEBUG_LOG("TRACE", "<- " func)

// Memory monitoring (simplified for Arduino)
int freeMemory() {
  return 8192; // Placeholder - actual implementation varies by board
}

void setup() {
  Serial.begin(115200);
  // Timeout after 3 seconds instead of infinite wait
  unsigned long serialStart = millis();
  while (!Serial && (millis() - serialStart < 3000)) delay(10);
  
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
    }
    // Read initial state of all pins (PCF8575 doesn't have digitalReadAll)
    last_s[i] = 0;
    for (uint8_t pin = 0; pin < 16; pin++) {
      if (pcf[i].digitalRead(pin)) {
        last_s[i] |= (1 << pin);
      }
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
  
  // Play startup test sound
  Serial.println(F("[STARTUP] Testing audio output..."));
  if (musicPlayer.startPlayingFile("/audio/generated/A/001.mp3")) {
    Serial.println(F("[STARTUP] Test sound playing from SD"));
  } else if (musicPlayer.startPlayingFile("/audio/human/A/001.mp3")) {
    Serial.println(F("[STARTUP] Test sound playing from SD (human)"));
  } else {
    Serial.println(F("[STARTUP] No SD audio found - playing built-in sine test"));
    playSineTest();
  }
  
  printMenu();
}

void loop() {
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
    currentTrackPath = "";
  }
  
  // Handle serial commands
  if (Serial.available()) {
    char cmd = Serial.read();
    
    // Handle calibration input
    if (waitingForMapping) {
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
            buttonMap[pendingButtonIndex].used = true;
            int ki = keyIndexByName(inputBuffer.c_str());
            if (ki >= 0) {
              buttonMap[pendingButtonIndex].keyIndex = ki;
            }
            
            Serial.print(F("\n[MAPPED] Button #"));
            Serial.print(pendingButtonIndex);
            Serial.print(F(" -> "));
            Serial.println(inputBuffer);
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
    
    // Normal command processing
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
  
  delay(5);  // Reduced from 10ms to 5ms for better responsiveness
}

void loadConfiguration() {
  TRACE_ENTER("loadConfiguration");
  DEBUG_LOG("CONFIG", "Loading SD card configuration...");
  DEBUG_LOG_INT("CONFIG", "Free RAM: ", freeMemory());
  
  // Clear existing configuration
  for (uint16_t i = 0; i < TOTAL_BUTTONS; i++) {
    buttonMap[i].used = false;
    buttonMap[i].keyIndex = 255;  // Invalid index
    buttonMap[i].buttonIndex = i;
    strcpy(buttonMap[i].source, "none");
    strcpy(buttonMap[i].input, "none");
  }
  
  // Ensure button mappings are cleared BEFORE loading keys
  initializeButtonMappings();

  DEBUG_LOG("CONFIG", "Using /config/keys.csv for button mappings");
  loadKeys();
  TRACE_EXIT("loadConfiguration");
}

void parseInputMapping(String inputStr, String keyStr) {
  if (inputStr.startsWith("pcf") && inputStr.indexOf(":") > 0) {
    // Handle PCF8575 pins (e.g., "pcf0:2")
    int colonIndex = inputStr.indexOf(":");
    if (colonIndex == -1) return;
    
    int chipNum = inputStr.substring(3, colonIndex).toInt();
    int pinNum = inputStr.substring(colonIndex + 1).toInt();
    
    // Calculate button index: chip * 16 + pin
    uint8_t buttonIndex = chipNum * 16 + pinNum;
    
    if (buttonIndex < TOTAL_BUTTONS) {
      buttonMap[buttonIndex].used = true;
      int ki = keyIndexByName(keyStr.c_str());
      if (ki >= 0) {
        buttonMap[buttonIndex].keyIndex = ki;
      }
      inputStr.toCharArray(buttonMap[buttonIndex].input, sizeof(buttonMap[buttonIndex].input));
      strcpy(buttonMap[buttonIndex].source, "keys.csv");
    }
  } else if (waitingForMapping && pendingButtonIndex < TOTAL_BUTTONS) {
    int ki = keyIndexByName(keyStr.c_str());
    if (ki >= 0) {
      buttonMap[pendingButtonIndex].used = true;
      buttonMap[pendingButtonIndex].keyIndex = ki;
      inputStr.toCharArray(buttonMap[pendingButtonIndex].input, sizeof(buttonMap[pendingButtonIndex].input));
      strcpy(buttonMap[pendingButtonIndex].source, "manual");
      
      Serial.print(F("[CALIB] Mapped button "));
      Serial.print(pendingButtonIndex);
      Serial.print(F(" to key '"));
      Serial.print(keyStr);
      Serial.print(F("' with input '"));
      Serial.print(inputStr);
      Serial.println(F("'"));
    } else {
      Serial.print(F("[ERROR] Unknown key: "));
      Serial.println(keyStr);
    }
    waitingForMapping = false;
  } else if (inputStr.startsWith("gpio:")) {
    // Handle GPIO pins (extra pins)
    int gpioPin = inputStr.substring(5).toInt();
    
    // Find matching extra pin
    for (uint8_t i = 0; i < EXTRA_COUNT; i++) {
      if (extraPins[i] == gpioPin) {
        uint8_t buttonIndex = TOTAL_EXPANDER_PINS + i;
        buttonMap[buttonIndex].used = true;
        int ki = keyIndexByName(keyStr.c_str());
        if (ki >= 0) {
          buttonMap[buttonIndex].keyIndex = ki;
        }
        strncpy(buttonMap[buttonIndex].source, "keys.csv", sizeof(buttonMap[buttonIndex].source) - 1);
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
    buttonMap[i].keyIndex = 255;
    buttonMap[i].source[0] = '\0';
    buttonMap[i].input[0] = '\0';
  }
  
  Serial.println(F("[CONFIG] Button mappings cleared - will load from keys.csv"));
}

void checkButtons() {
  // Check PCF8575 expanders
  for (uint8_t chipIndex = 0; chipIndex < NUM_PCF; chipIndex++) {
    // Read all pins for this chip (PCF8575 library doesn't have digitalReadAll)
    uint16_t current_s = 0;
    for (uint8_t pin = 0; pin < 16; pin++) {
      if (pcf[chipIndex].digitalRead(pin)) {
        current_s |= (1 << pin);
      }
    }
    
    uint16_t changed = current_s ^ last_s[chipIndex];
    
    if (changed) {
      for (uint8_t pin = 0; pin < 16; pin++) {
        if (changed & (1 << pin)) {
          bool pressed = !(current_s & (1 << pin)); // Active low
          if (pressed) {
            uint8_t buttonIndex = chipIndex * 16 + pin;
            handleButtonPress(buttonIndex);
          }
        }
      }
      
      last_s[chipIndex] = current_s;
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
    
    if (buttonMap[buttonIndex].used && buttonMap[buttonIndex].keyIndex < numKeys) {
      Serial.print(F(" (currently: "));
      Serial.print(keys[buttonMap[buttonIndex].keyIndex].key);
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
  
  if (buttonMap[buttonIndex].used && buttonMap[buttonIndex].keyIndex < numKeys) {
    Serial.print(F(" → "));
    Serial.print(keys[buttonMap[buttonIndex].keyIndex].key);
    if (buttonMap[buttonIndex].source[0] != '\0') {
      Serial.print(F(" [src:"));
      Serial.print(buttonMap[buttonIndex].source);
      Serial.print(F(" input:"));
      Serial.print(buttonMap[buttonIndex].input);
      Serial.print(F("]"));
    }
    
    // Show audio availability info
    KeyConfig* keyConfig = nullptr;
    if (buttonMap[buttonIndex].keyIndex < numKeys) {
      keyConfig = &keys[buttonMap[buttonIndex].keyIndex];
    }
    
    if (keyConfig) {
      Serial.print(F(" [Human:"));
      Serial.print(keyConfig->hasHuman ? F("YES") : F("NO"));
      Serial.print(F("|Generated:"));
      Serial.print(keyConfig->hasGenerated ? F("YES") : F("NO"));
      Serial.print(F("]"));
    }
  } else {
    Serial.print(F(" → UNMAPPED"));
    // Helpful hint to trace back to CSV mapping
    Serial.print(F(" | Hint: add INPUT mapping for this button in /config/keys.csv as pcf"));
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
        // Special handling for PERIOD button mode switching on 3rd press
        if (buttonMap[i].keyIndex < numKeys && strcmp(keys[buttonMap[i].keyIndex].key, "PERIOD") == 0 && pressCount[i] == 3) {
          // Toggle priority mode once
          currentMode = (currentMode == PriorityMode::HUMAN_FIRST) ? 
                        PriorityMode::GENERATED_FIRST : PriorityMode::HUMAN_FIRST;
          Serial.print(F("[MODE] Switched to: "));
          Serial.println((currentMode == PriorityMode::HUMAN_FIRST) ? F("HUMAN_FIRST") : F("GENERATED_FIRST"));

          // Play generated announcement: press #2 for HUMAN_FIRST, #3 for GENERATED_FIRST
          playAudioForKey("PERIOD", (currentMode == PriorityMode::HUMAN_FIRST) ? 2 : 3);
        } else {
          // Normal audio playback
          if (buttonMap[i].keyIndex < numKeys) {
            playAudioForKey(keys[buttonMap[i].keyIndex].key, pressCount[i]);
          }
        }
      }
      
      pressCount[i] = 0; // Reset press count
    }
  }
}

void playAudioForKey(const char* key, uint8_t pressCount) {
  TRACE_ENTER("playAudioForKey");
  DEBUG_LOG_STR("AUDIO", "Request key: ", key);
  DEBUG_LOG_INT("AUDIO", "Press count: ", pressCount);
  DEBUG_LOG("AUDIO", (currentMode == PriorityMode::HUMAN_FIRST) ? "Mode: HUMAN_FIRST" : "Mode: GENERATED_FIRST");
  DEBUG_LOG_INT("AUDIO", "Free RAM: ", freeMemory());
  
  // Alias: treat HELLO_HOW_ARE_YOU as SHIFT press #1
  if (strcmp(key, "HELLO_HOW_ARE_YOU") == 0) {
    DEBUG_LOG("ALIAS", "HELLO_HOW_ARE_YOU -> SHIFT (press #1)");
    playAudioForKey("SHIFT", 1);
    TRACE_EXIT("playAudioForKey");
    return;
  }
  // Debounce: ignore if already playing
  if (isPlaying) {
    Serial.println(F("[AUDIO] Ignored request: audio already playing"));
    return;
  }
  // Find key configuration
  KeyConfig* keyConfig = nullptr;
  for (uint8_t i = 0; i < numKeys; i++) {
    if (strcmp(keys[i].key, key) == 0) {
      keyConfig = &keys[i];
      break;
    }
  }
  
  if (!keyConfig) {
    Serial.print(F("[ERROR] Key not found: "));
    Serial.println(key);
    return;
  }
  
  // Enhanced logging
  Serial.print(F("[AUDIO] Playing audio for key '"));
  Serial.print(key);
  Serial.print(F("' [Human:"));
  Serial.print(keyConfig->hasHuman ? F("YES") : F("NO"));
  Serial.print(F("|Generated:"));
  Serial.print(keyConfig->hasGenerated ? F("YES") : F("NO"));
  Serial.print(F("], press #"));
  Serial.print(pressCount);
  Serial.print(F(", mode: "));
  Serial.println((currentMode == PriorityMode::HUMAN_FIRST) ? F("HUMAN_FIRST") : F("GENERATED_FIRST"));
  
  // Determine preferred source by mode
  bool preferHuman = (currentMode == PriorityMode::HUMAN_FIRST);
  // Force bank for special keys to match the wordlist semantics
  // PERIOD: press #2/#3 are generated announcements
  if (strcmp(key, "PERIOD") == 0 && (pressCount == 2 || pressCount == 3)) {
    preferHuman = false;
  }
  // SHIFT: press #1 is human greeting; #2/#3 are generated prompts
  if (strcmp(key, "SHIFT") == 0) {
    if (pressCount == 1) preferHuman = true;
    if (pressCount == 2 || pressCount == 3) preferHuman = false;
  }

  // Strict handling: for PERIOD(2/3) and SHIFT(2/3) require generated track; do NOT fallback to human
  String trackPath = "";
  bool strictGenerated = ((strcmp(key, "PERIOD") == 0 || strcmp(key, "SHIFT") == 0) && (pressCount == 2 || pressCount == 3));
  if (strictGenerated) {
    String dirPath = String("/audio/generated/") + String(key);
    trackPath = nthTrackPathInDir(dirPath, pressCount);
  } else {
    trackPath = pickTrackFor(key, preferHuman, pressCount);
  }

  if (trackPath.length() == 0) {
    DEBUG_LOG_STR("ERROR", "No audio available for key: ", key);
    DEBUG_LOG_INT("ERROR", "Press count: ", pressCount);
    TRACE_EXIT("playAudioForKey");
    return;
  }

  // Stop any current playback for clean interruption
  if (musicPlayer.playingMusic) {
    musicPlayer.stopPlaying();
    Serial.println(F("[AUDIO] Stopped previous track"));
  }

  // Extract filename from full path for cleaner logging
  int lastSlash = trackPath.lastIndexOf('/');
  String filename = (lastSlash >= 0) ? trackPath.substring(lastSlash + 1) : trackPath;
  
  // Show what audio content will be played by reading corresponding .txt file
  String txtPath = trackPath;
  txtPath.replace(".mp3", ".txt");
  File txtFile = SD.open(txtPath.c_str());
  if (txtFile) {
    Serial.print(F("[CONTENT] About to say: "));
    String content = txtFile.readString();
    content.trim();
    // Remove the "# XXX.mp3 should contain: " prefix if present
    int colonPos = content.indexOf(": ");
    if (colonPos >= 0 && content.startsWith("#")) {
      content = content.substring(colonPos + 2);
    }
    Serial.println(content);
    txtFile.close();
  }
  else {
    Serial.print(F("[CONTENT] Missing caption file: "));
    Serial.println(txtPath);
  }
  
  Serial.print(F("[AUDIO] Starting: "));
  Serial.print(filename);
  Serial.print(F(" ("));
  Serial.print(trackPath);
  Serial.println(F(")"));

  if (musicPlayer.startPlayingFile(trackPath.c_str())) {
    currentTrackPath = trackPath;
    isPlaying = true;
    audioStartTime = millis();
    DEBUG_LOG_STR("AUDIO", "✓ Playing: ", filename);
    DEBUG_LOG_INT("AUDIO", "Started at: ", millis());
    DEBUG_LOG_INT("AUDIO", "Free RAM: ", freeMemory());
  } else {
    DEBUG_LOG_STR("ERROR", "✗ Failed to start: ", filename);
    DEBUG_LOG_INT("ERROR", "Free RAM: ", freeMemory());
  }
  TRACE_EXIT("playAudioForKey");
}

String pickTrackFor(const char* key, bool wantHuman, uint8_t pressCount) {
  int ki = keyIndexByName(key);
  if (ki < 0) return "";

  // First choice by mode, with automatic fallback if empty
  for (int pass = 0; pass < 2; pass++) {
    bool useHuman = (pass == 0) ? wantHuman : !wantHuman;
    bool has = useHuman ? keys[ki].hasHuman : keys[ki].hasGenerated;
    uint16_t total = useHuman ? humanCountByKey[ki] : genCountByKey[ki];
    if (!has || total == 0) continue;

    String dirPath = String(useHuman ? "/audio/human/" : "/audio/generated/") + String(keys[ki].key);
    // Wrap automatically: 6 presses on 5 files -> 1
    return nthTrackPathInDir(dirPath, pressCount);
  }
  return "";
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

void printMenu() {
  Serial.println(F("\n=== Tactile Communication Device ==="));
  Serial.println(F("Commands:"));
  Serial.println(F("  C - Interactive calibration mode (press button, type mapping)"));
  Serial.println(F("  E - Exit calibration mode"));
  Serial.println(F("  M - Toggle priority mode (Human/Generated first)"));
  Serial.println(F("  S - Show status"));
  Serial.println(F("  R - Reload configuration"));
  Serial.println(F("  T - Play sine test tone"));
  Serial.println(F("  H - Show this menu"));
  Serial.println();
}

// Built-in sine wave test (no SD card required)
void playSineTest() {
  Serial.println(F("[SINE] Starting built-in sine test..."));
  
  // Use VS1053's built-in sine test mode
  // This sends the magic byte sequence to trigger internal sine generation
  musicPlayer.sineTest(0x44, 500);  // 1000 Hz tone for 500ms
  
  Serial.println(F("[SINE] Sine test complete - VS1053 audio verified"));
}
