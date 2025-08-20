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
 * - Arduino Uno/Nano with adequate I/O
 * - Adafruit VS1053 Codec Breakout or Shield
 * - 2x PCF8575 I2C port expanders (0x20, 0x21)
 * - MicroSD card (formatted as FAT32)
 * - 32+ tactile buttons
 * - Quality speaker/headphones
 * - Rechargeable battery pack
 */

#include <SPI.h>
#include <SD.h>
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

// Configuration constants
#define NUM_PCF 2
#define BUTTONS_PER_PCF 16
#define EXTRA_COUNT 4
#define TOTAL_BUTTONS (NUM_PCF * BUTTONS_PER_PCF + EXTRA_COUNT)
#define MAX_KEYS 50
#define MAX_FILENAME_LEN 64

// PCF8575 I2C addresses
const uint8_t PCF_ADDR[NUM_PCF] = { 0x20, 0x21 };
Adafruit_PCF8575 pcf[NUM_PCF];

// Extra Arduino pins for additional controls
const uint8_t extraPins[] = { 8, 9, 2, 5 };

// Priority mode enumeration
enum class PriorityMode {
  HUMAN_FIRST,
  GENERATED_FIRST
};

// Key configuration structure
struct KeyConfig {
  char key[16];           // Key name (A, B, SHIFT, etc.)
  char description[32];   // Human-readable description
  char humanPlaylist[MAX_FILENAME_LEN];     // Path to human playlist
  char generatedPlaylist[MAX_FILENAME_LEN]; // Path to generated playlist
  bool hasHuman;          // Whether human audio exists
  bool hasGenerated;      // Whether generated audio exists
};

// Button mapping structure
struct ButtonMapping {
  bool used;
  char key[16];           // Maps to KeyConfig.key
  uint8_t buttonIndex;    // Physical button index
};

// Global variables
KeyConfig keys[MAX_KEYS];
uint8_t numKeys = 0;
ButtonMapping buttonMap[TOTAL_BUTTONS];
PriorityMode currentMode = PriorityMode::HUMAN_FIRST;

// Audio playback state
bool isPlaying = false;
String currentTrackPath = "";
unsigned long audioStartTime = 0;

// Button state tracking
uint16_t lastPcfState[NUM_PCF];
bool lastExtraState[EXTRA_COUNT];
unsigned long lastPressTime[TOTAL_BUTTONS];
uint8_t pressCount[TOTAL_BUTTONS];
const unsigned long MULTI_PRESS_WINDOW = 1000; // milliseconds

// Calibration mode
bool inCalibrate = false;

// Forward declarations
void loadConfiguration();
void loadKeys();
void loadMappings();
void initializeButtonMappings();
void handleButtonPress(uint8_t buttonIndex);
void playAudioForKey(const char* key, uint8_t pressCount);
String getPlaylistPath(const char* key, bool useHuman);
String getTrackFromPlaylist(const String& playlistPath, uint8_t trackNumber);
void checkButtons();
void handleMultiPress();
void printStatus();
void printMenu();

void setup() {
  Serial.begin(115200);
  while (!Serial) delay(10);
  
  Serial.println(F("=== Tactile Communication Device - New SD Structure ==="));
  
  // Initialize I2C
  Wire.begin();
  
  // Initialize PCF8575 expanders
  for (uint8_t i = 0; i < NUM_PCF; i++) {
    if (!pcf[i].begin(PCF_ADDR[i])) {
      Serial.print(F("[ERROR] PCF8575 #"));
      Serial.print(i);
      Serial.print(F(" at 0x"));
      Serial.print(PCF_ADDR[i], HEX);
      Serial.println(F(" not found!"));
    } else {
      Serial.print(F("[OK] PCF8575 #"));
      Serial.print(i);
      Serial.print(F(" at 0x"));
      Serial.print(PCF_ADDR[i], HEX);
      Serial.println(F(" initialized"));
      
      // Set all pins as inputs with pullups
      pcf[i].pinMode(0xFFFF, INPUT_PULLUP);
      lastPcfState[i] = pcf[i].digitalReadBulk();
    }
  }
  
  // Initialize extra pins
  for (uint8_t i = 0; i < EXTRA_COUNT; i++) {
    pinMode(extraPins[i], INPUT_PULLUP);
    lastExtraState[i] = digitalRead(extraPins[i]);
  }
  
  // Initialize VS1053
  if (!musicPlayer.begin()) {
    Serial.println(F("[ERROR] VS1053 not found!"));
    while (1) delay(10);
  }
  Serial.println(F("[OK] VS1053 initialized"));
  
  // Initialize SD card
  if (!SD.begin(CARDCS)) {
    Serial.println(F("[ERROR] SD card not found!"));
    while (1) delay(10);
  }
  Serial.println(F("[OK] SD card initialized"));
  
  // Set volume (lower numbers = louder)
  musicPlayer.setVolume(20, 20);
  
  // Load configuration from SD card
  loadConfiguration();
  
  // Initialize button state arrays
  for (uint8_t i = 0; i < TOTAL_BUTTONS; i++) {
    lastPressTime[i] = 0;
    pressCount[i] = 0;
  }
  
  Serial.println(F("[READY] Device initialized successfully"));
  printMenu();
}

void loop() {
  checkButtons();
  handleMultiPress();
  
  // Handle serial commands
  if (Serial.available()) {
    char cmd = Serial.read();
    switch (cmd) {
      case 'C': case 'c':
        inCalibrate = !inCalibrate;
        Serial.print(F("Calibration mode: "));
        Serial.println(inCalibrate ? F("ON") : F("OFF"));
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
    buttonMap[i].key[0] = '\0';
    buttonMap[i].buttonIndex = i;
  }
  
  loadKeys();
  loadMappings();
  initializeButtonMappings();
  
  Serial.print(F("[CONFIG] Loaded "));
  Serial.print(numKeys);
  Serial.println(F(" keys"));
}

void loadKeys() {
  File file = SD.open("/config/keys.csv");
  if (!file) {
    Serial.println(F("[ERROR] Cannot open /config/keys.csv"));
    return;
  }
  
  Serial.println(F("[CONFIG] Loading keys.csv..."));
  
  // Skip header line
  String line = file.readStringUntil('\n');
  
  while (file.available() && numKeys < MAX_KEYS) {
    line = file.readStringUntil('\n');
    line.trim();
    
    if (line.length() == 0) continue;
    
    // Parse CSV: key,description
    int commaIndex = line.indexOf(',');
    if (commaIndex == -1) continue;
    
    String keyStr = line.substring(0, commaIndex);
    String descStr = line.substring(commaIndex + 1);
    
    keyStr.trim();
    descStr.trim();
    
    // Store key configuration
    keyStr.toCharArray(keys[numKeys].key, sizeof(keys[numKeys].key));
    descStr.toCharArray(keys[numKeys].description, sizeof(keys[numKeys].description));
    
    Serial.print(F("[KEY] "));
    Serial.print(keys[numKeys].key);
    Serial.print(F(" - "));
    Serial.println(keys[numKeys].description);
    
    numKeys++;
  }
  
  file.close();
}

void loadMappings() {
  File file = SD.open("/mappings/index.csv");
  if (!file) {
    Serial.println(F("[ERROR] Cannot open /mappings/index.csv"));
    return;
  }
  
  Serial.println(F("[CONFIG] Loading mappings/index.csv..."));
  
  // Skip header line
  String line = file.readStringUntil('\n');
  
  while (file.available()) {
    line = file.readStringUntil('\n');
    line.trim();
    
    if (line.length() == 0) continue;
    
    // Parse CSV: key,human_playlist,generated_playlist
    int firstComma = line.indexOf(',');
    if (firstComma == -1) continue;
    
    int secondComma = line.indexOf(',', firstComma + 1);
    if (secondComma == -1) continue;
    
    String keyStr = line.substring(0, firstComma);
    String humanPath = line.substring(firstComma + 1, secondComma);
    String generatedPath = line.substring(secondComma + 1);
    
    keyStr.trim();
    humanPath.trim();
    generatedPath.trim();
    
    // Find matching key configuration
    for (uint8_t i = 0; i < numKeys; i++) {
      if (strcmp(keys[i].key, keyStr.c_str()) == 0) {
        // Store playlist paths
        humanPath.toCharArray(keys[i].humanPlaylist, sizeof(keys[i].humanPlaylist));
        generatedPath.toCharArray(keys[i].generatedPlaylist, sizeof(keys[i].generatedPlaylist));
        
        // Check if playlists exist
        keys[i].hasHuman = (humanPath.length() > 0 && SD.exists(humanPath.c_str()));
        keys[i].hasGenerated = (generatedPath.length() > 0 && SD.exists(generatedPath.c_str()));
        
        Serial.print(F("[MAPPING] "));
        Serial.print(keys[i].key);
        Serial.print(F(" - Human: "));
        Serial.print(keys[i].hasHuman ? F("YES") : F("NO"));
        Serial.print(F(", Generated: "));
        Serial.println(keys[i].hasGenerated ? F("YES") : F("NO"));
        
        break;
      }
    }
  }
  
  file.close();
}

void initializeButtonMappings() {
  // Initialize default button mappings
  // This maps physical buttons to keys - customize based on your hardware layout
  
  // PCF0 buttons (0-15) - Letters A-P
  const char* pcf0Keys[] = {
    "A", "B", "C", "D", "E", "F", "G", "H",
    "I", "J", "K", "L", "M", "N", "O", "P"
  };
  
  // PCF1 buttons (16-31) - Letters Q-Z + special keys
  const char* pcf1Keys[] = {
    "Q", "R", "S", "T", "U", "V", "W", "X",
    "Y", "Z", "SHIFT", "PERIOD", "SPACE", "", "", ""
  };
  
  // Map PCF0 buttons
  for (uint8_t i = 0; i < 16; i++) {
    if (strlen(pcf0Keys[i]) > 0) {
      buttonMap[i].used = true;
      strcpy(buttonMap[i].key, pcf0Keys[i]);
    }
  }
  
  // Map PCF1 buttons
  for (uint8_t i = 0; i < 16; i++) {
    if (strlen(pcf1Keys[i]) > 0) {
      buttonMap[16 + i].used = true;
      strcpy(buttonMap[16 + i].key, pcf1Keys[i]);
    }
  }
  
  Serial.println(F("[CONFIG] Button mappings initialized"));
}

void checkButtons() {
  // Check PCF8575 expanders
  for (uint8_t chipIndex = 0; chipIndex < NUM_PCF; chipIndex++) {
    uint16_t currentState = pcf[chipIndex].digitalReadBulk();
    uint16_t changed = currentState ^ lastPcfState[chipIndex];
    
    if (changed) {
      for (uint8_t pin = 0; pin < BUTTONS_PER_PCF; pin++) {
        if (changed & (1 << pin)) {
          bool pressed = !(currentState & (1 << pin)); // Active low
          if (pressed) {
            uint8_t buttonIndex = chipIndex * BUTTONS_PER_PCF + pin;
            handleButtonPress(buttonIndex);
          }
        }
      }
      lastPcfState[chipIndex] = currentState;
    }
  }
  
  // Check extra pins
  for (uint8_t i = 0; i < EXTRA_COUNT; i++) {
    bool currentState = digitalRead(extraPins[i]);
    if (currentState != lastExtraState[i]) {
      if (!currentState) { // Active low
        uint8_t buttonIndex = NUM_PCF * BUTTONS_PER_PCF + i;
        handleButtonPress(buttonIndex);
      }
      lastExtraState[i] = currentState;
    }
  }
}

void handleButtonPress(uint8_t buttonIndex) {
  if (buttonIndex >= TOTAL_BUTTONS) return;
  
  unsigned long currentTime = millis();
  
  if (inCalibrate) {
    Serial.print(F("[CALIBRATE] Button "));
    Serial.print(buttonIndex);
    if (buttonMap[buttonIndex].used) {
      Serial.print(F(" ("));
      Serial.print(buttonMap[buttonIndex].key);
      Serial.print(F(")"));
    }
    Serial.println(F(" pressed"));
    return;
  }
  
  // Multi-press detection
  if (currentTime - lastPressTime[buttonIndex] < MULTI_PRESS_WINDOW) {
    pressCount[buttonIndex]++;
  } else {
    pressCount[buttonIndex] = 1;
  }
  
  lastPressTime[buttonIndex] = currentTime;
  
  Serial.print(F("[BUTTON] "));
  Serial.print(buttonIndex);
  if (buttonMap[buttonIndex].used) {
    Serial.print(F(" ("));
    Serial.print(buttonMap[buttonIndex].key);
    Serial.print(F(")"));
  }
  Serial.print(F(" press #"));
  Serial.println(pressCount[buttonIndex]);
}

void handleMultiPress() {
  unsigned long currentTime = millis();
  
  for (uint8_t i = 0; i < TOTAL_BUTTONS; i++) {
    if (pressCount[i] > 0 && 
        (currentTime - lastPressTime[i]) >= MULTI_PRESS_WINDOW) {
      
      // Time to process the multi-press
      if (buttonMap[i].used) {
        // Special handling for PERIOD button mode switching
        if (strcmp(buttonMap[i].key, "PERIOD") == 0 && pressCount[i] == 3) {
          // Toggle priority mode
          currentMode = (currentMode == PriorityMode::HUMAN_FIRST) ? 
                        PriorityMode::GENERATED_FIRST : PriorityMode::HUMAN_FIRST;
          
          Serial.print(F("[MODE] Switched to "));
          Serial.println((currentMode == PriorityMode::HUMAN_FIRST) ? F("HUMAN_FIRST") : F("GENERATED_FIRST"));
          
          // Play mode announcement
          playAudioForKey("PERIOD", (currentMode == PriorityMode::HUMAN_FIRST) ? 2 : 3);
        } else {
          // Normal audio playback
          playAudioForKey(buttonMap[i].key, pressCount[i]);
        }
      }
      
      pressCount[i] = 0; // Reset press count
    }
  }
}

void playAudioForKey(const char* key, uint8_t pressCount) {
  // Find key configuration
  KeyConfig* keyConfig = nullptr;
  for (uint8_t i = 0; i < numKeys; i++) {
    if (strcmp(keys[i].key, key) == 0) {
      keyConfig = &keys[i];
      break;
    }
  }
  
  if (!keyConfig) {
    Serial.print(F("[AUDIO] No configuration found for key: "));
    Serial.println(key);
    return;
  }
  
  // Determine which playlist to use based on priority mode
  String playlistPath;
  bool useHuman = (currentMode == PriorityMode::HUMAN_FIRST);
  
  if (useHuman && keyConfig->hasHuman) {
    playlistPath = String(keyConfig->humanPlaylist);
  } else if (keyConfig->hasGenerated) {
    playlistPath = String(keyConfig->generatedPlaylist);
  } else if (keyConfig->hasHuman) {
    playlistPath = String(keyConfig->humanPlaylist);
  } else {
    Serial.print(F("[AUDIO] No audio available for key: "));
    Serial.println(key);
    return;
  }
  
  // Get track from playlist
  String trackPath = getTrackFromPlaylist(playlistPath, pressCount);
  if (trackPath.length() == 0) {
    Serial.print(F("[AUDIO] No track #"));
    Serial.print(pressCount);
    Serial.print(F(" in playlist: "));
    Serial.println(playlistPath);
    return;
  }
  
  // Play the audio file
  Serial.print(F("[AUDIO] Playing: "));
  Serial.println(trackPath);
  
  if (musicPlayer.startPlayingFile(trackPath.c_str())) {
    currentTrackPath = trackPath;
    isPlaying = true;
    audioStartTime = millis();
  } else {
    Serial.print(F("[ERROR] Failed to play: "));
    Serial.println(trackPath);
  }
}

String getTrackFromPlaylist(const String& playlistPath, uint8_t trackNumber) {
  File file = SD.open(playlistPath.c_str());
  if (!file) {
    Serial.print(F("[ERROR] Cannot open playlist: "));
    Serial.println(playlistPath);
    return "";
  }
  
  uint8_t currentTrack = 1;
  String trackPath = "";
  
  while (file.available()) {
    String line = file.readStringUntil('\n');
    line.trim();
    
    if (line.length() == 0) continue;
    
    if (currentTrack == trackNumber) {
      // Build full path relative to playlist directory
      String playlistDir = playlistPath;
      int lastSlash = playlistDir.lastIndexOf('/');
      if (lastSlash != -1) {
        playlistDir = playlistDir.substring(0, lastSlash + 1);
        trackPath = playlistDir + line;
      } else {
        trackPath = line;
      }
      break;
    }
    currentTrack++;
  }
  
  file.close();
  return trackPath;
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
  Serial.println(F("  C - Toggle calibration mode"));
  Serial.println(F("  M - Toggle priority mode (Human/Generated first)"));
  Serial.println(F("  S - Show status"));
  Serial.println(F("  R - Reload configuration"));
  Serial.println(F("  H - Show this menu"));
  Serial.println();
}
