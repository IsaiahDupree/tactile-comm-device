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

// PCF8575 I2C port expanders for 32-button support
Adafruit_PCF8575 pcf0;
Adafruit_PCF8575 pcf1;

// Audio interruption support
volatile bool audioInterrupted = false;
volatile unsigned long lastAudioStart = 0;
const unsigned long MAX_AUDIO_LENGTH = 5000; // 5 second max per audio clip

// Extra Arduino pins for additional controls (avoid pins 0,1 for Serial)
const uint8_t extraPins[]    = { 8,  9,  2,  5 };   // Safe pins: VS1053 uses pins 3,4,6,7
const uint8_t extraIndices[] = {32, 33, 34, 35};
const uint8_t EXTRA_COUNT    = sizeof(extraPins) / sizeof(extraPins[0]);

// Button mapping structure (now just stores button labels)
struct MapEntry { 
  bool used; 
  char label[12];
};

MapEntry mapTab[32 + EXTRA_COUNT];

// State for edge-detection
uint16_t last_s0, last_s1;
bool     lastExtra[EXTRA_COUNT];

// Button press timing for multi-press detection
unsigned long lastPressTime[32 + EXTRA_COUNT];
uint8_t pressCount[32 + EXTRA_COUNT];
const unsigned long MULTI_PRESS_WINDOW = 1000; // milliseconds (increased for better multi-press detection)

// Audio playback state
bool isPlaying = false;
String currentTrackPath = "";

// Calibration mode flag
bool inCalibrate = false;

// Debug logging control
bool debugMode = true;

// Priority-based audio mapping system
// Priority 1: Human recorded audio (preferred)
// Priority 2: Generated TTS audio (fallback)
struct AudioMapping {
  const char* label;
  uint8_t folder;
  uint8_t tracks;
  uint8_t baseTrack;  // Base track number for this button (for shared folders)
  bool hasRecorded;  // True if folder contains human recorded audio
  const char* fallbackLabel; // Alternative label for TTS generation
};

// NEW PRIORITY SYSTEM - FRESH SD CARD SETUP
// 1st Press: Generated TTS (clear, consistent)
// 2nd Press: Personal Recorded Words (familiar voices)
// 3rd+ Press: Additional TTS/Recorded words
//
// DETAILED BUTTON MAPPINGS:
AudioMapping audioMappings[] = {
  // Special Buttons - Each starts from specific track in folder 1
  {"YES", 1, 4, 1, false, "yes"},      // Starts from track 1: /01/001.mp3
  {"NO", 1, 4, 2, false, "no"},       // Starts from track 2: /01/002.mp3  
  {"WATER", 1, 4, 3, false, "water"}, // Starts from track 3: /01/003.mp3
  {"HELP", 1, 4, 4, false, "help"},   // Starts from track 4: /01/004.mp3
  
  // Letters A-Z with Clear Press Mappings
  // A: 1=Apple[TTS], 2=Amer[REC], 3=Alari[REC], 4=Arabic[TTS], 5=Amory[REC]
  {"A", 5, 5, 1, true, "Apple"},
  
  // B: 1=Ball[TTS], 2=Bye[REC], 3=Bathroom[TTS], 4=Bed[TTS]
  {"B", 6, 4, 1, true, "Ball"},
  
  // C: 1=Cat[TTS], 2=Chair[TTS], 3=Car[TTS]
  {"C", 7, 3, 1, false, "Cat"},
  
  // D: 1=Dog[TTS], 2=Deen[REC], 3=Daddy[REC], 4=Doctor[TTS]
  {"D", 8, 4, 1, true, "Dog"},
  
  // E: 1=Elephant[TTS]
  {"E", 9, 1, 1, false, "Elephant"},
  
  // F: 1=Fish[TTS], 2=FaceTime[TTS]
  {"F", 10, 2, 1, false, "Fish"},
  
  // G: 1=Go[TTS], 2=Good Morning[TTS]
  {"G", 11, 2, 1, false, "Go"},
  
  // H: 1=House[TTS], 2=Hello[TTS], 3=How are you[TTS]
  {"H", 12, 3, 1, false, "House"},
  
  // I: 1=Ice[TTS], 2=Inside[TTS]
  {"I", 13, 2, 1, false, "Ice"},
  
  // J: 1=Jump[TTS]
  {"J", 14, 1, 1, false, "Jump"},
  
  // K: 1=Key[TTS], 2=Kiyah[REC], 3=Kyan[REC], 4=Kleenex[TTS]
  {"K", 15, 4, 1, true, "Key"},
  
  // L: 1=Love[TTS], 2=Lee[REC], 3=I love you[REC], 4=Light[TTS]
  {"L", 16, 4, 1, true, "Love"},
  
  // M: 1=Moon[TTS], 2=Medicine[TTS], 3=Mohammad[TTS]
  {"M", 17, 3, 1, false, "Moon"},
  
  // N: 1=Net[TTS], 2=Nadowie[REC], 3=Noah[REC]
  {"N", 18, 3, 1, true, "Net"},
  
  // O: 1=Orange[TTS], 2=Outside[TTS]
  {"O", 19, 2, 1, false, "Orange"},
  
  // P: 1=Purple[TTS], 2=Phone[TTS], 3=Pain[TTS]
  {"P", 20, 3, 1, false, "Purple"},
  
  // Q: 1=Queen[TTS]
  {"Q", 21, 1, 1, false, "Queen"},
  
  // R: 1=Red[TTS], 2=Room[TTS]
  {"R", 22, 2, 1, false, "Red"},
  
  // S: 1=Sun[TTS], 2=Susu[REC], 3=Scarf[TTS]
  {"S", 23, 3, 1, true, "Sun"},
  
  // T: 1=Tree[TTS], 2=TV[TTS]
  {"T", 24, 2, 1, false, "Tree"},
  
  // U: 1=Up[TTS], 2=Urgent Care[TTS]
  {"U", 25, 2, 1, false, "Up"},
  
  // V: 1=Van[TTS]
  {"V", 26, 1, 1, false, "Van"},
  
  // W: 1=Water[TTS], 2=Walker[REC], 3=Wheelchair[REC], 4=Walk[TTS]
  {"W", 27, 4, 1, true, "Water"},
  
  // X: 1=X-ray[TTS]
  {"X", 28, 1, 1, false, "X-ray"},
  
  // Y: 1=Yellow[TTS]
  {"Y", 29, 1, 1, false, "Yellow"},
  
  // Z: 1=Zebra[TTS]
  {"Z", 30, 1, 1, false, "Zebra"},
  
  // Symbols
  {"SPACE", 31, 1, 1, false, "Space"},   // 1=Space[TTS]
  {"PERIOD", 32, 1, 1, false, "Period"}, // 1=Period[TTS]
  {".", 32, 1, 1, false, "Period"},      // Alternative for period
  {"_", 31, 1, 1, false, "Space"},       // Alternative for space
  
  // SHIFT with Enhanced Help System: 1=Shift[TTS], 2=Detailed Device Help[TTS], 3=Word Mapping Guide[TTS]
  {"SHIFT", 33, 3, 1, false, "Shift"}
};

const uint8_t AUDIO_MAPPINGS_COUNT = sizeof(audioMappings) / sizeof(audioMappings[0]);

// Forward declarations
void printMenu();
void printCalibrationInstructions();
void loadConfig();
void saveConfig();
void printMap();
void handlePress(uint8_t idx);
void initializeDefaultMappings();
void playButtonAudio(const char* label);
void playButtonAudioWithCount(const char* label, uint8_t pressCount);
void handleMultiPress();
void checkAudioStatus();
void testAllButtons();
bool hasValidMappings();
AudioMapping* findAudioByLabel(const char* label);

void setup() {
  Serial.begin(115200);
  while (!Serial && millis() < 3000); // Wait up to 3 seconds for Serial

  Serial.println(F("\n=================================================="));
  Serial.println(F("    TACTILE COMMUNICATION DEVICE - VS1053"));
  Serial.println(F("            Detailed Logging Version"));
  Serial.println(F("=================================================="));
  Serial.println(F("[INIT] Starting hardware initialization..."));

  // Initialize all timing arrays
  Serial.println(F("[INIT] Initializing button timing arrays..."));
  for (uint8_t i = 0; i < 32 + EXTRA_COUNT; i++) {
    lastPressTime[i] = 0;
    pressCount[i] = 0;
  }
  Serial.print(F("[INIT] Configured for "));
  Serial.print(32 + EXTRA_COUNT);
  Serial.println(F(" total buttons (32 PCF8575 + 3 Arduino pins)"));

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

  // Initialize I²C for PCF8575 expanders  
  Serial.println(F("[I2C] Initializing I2C bus for port expanders..."));
  Serial.println(F("[I2C] Using Wire1 bus (STEMMA QT connector)"));
  Wire1.begin();
  Serial.println(F("[I2C] I2C bus initialized on Wire1"));
  
  Serial.println(F("[I2C] Scanning for PCF8575 expanders..."));
  if (!pcf0.begin(0x20, &Wire1)) {
    Serial.println(F("[WARNING] PCF8575 #0 (0x20) not found on Wire1!"));
    Serial.println(F("[WARNING] Check STEMMA QT connection to 0x20"));
    Serial.println(F("[WARNING] GPIO pins 0-15 will not be available"));
  } else {
    Serial.println(F("[SUCCESS] PCF8575 #0 (0x20) online - GPIO 0-15 ready"));
  }
  
  if (!pcf1.begin(0x21, &Wire1)) {
    Serial.println(F("[WARNING] PCF8575 #1 (0x21) not found on Wire1!"));
    Serial.println(F("[WARNING] Check STEMMA QT connection to 0x21"));
    Serial.println(F("[WARNING] GPIO pins 16-31 will not be available"));
  } else {
    Serial.println(F("[SUCCESS] PCF8575 #1 (0x21) online - GPIO 16-31 ready"));
  }

  // Configure PCF8575 pins as inputs with pullup
  for (uint8_t i = 0; i < 16; i++) {
    pcf0.pinMode(i, INPUT_PULLUP);
    pcf1.pinMode(i, INPUT_PULLUP);
  }

  // Initialize extra Arduino pins
  for (uint8_t x = 0; x < EXTRA_COUNT; x++) {
    pinMode(extraPins[x], INPUT_PULLUP);
    lastExtra[x] = digitalRead(extraPins[x]);
  }

  // Prime the expander states
  last_s0 = pcf0.digitalReadWord();
  last_s1 = pcf1.digitalReadWord();

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
  musicPlayer.feedBuffer();
  musicPlayer.setVolume(1, 1);   // MAXIMUM default volume (0=loudest, 100=quiet)
  
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
      case 'T': case 't': testAllButtons(); break;
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
  uint16_t s0 = pcf0.digitalReadWord();   // GPIO 0–15
  uint16_t s1 = pcf1.digitalReadWord();   // GPIO 16–31

  // Edge-detect PCF8575 #0 → indices 0–15
  for (uint8_t i = 0; i < 16; i++) {
    bool prev = bitRead(last_s0, i);
    bool cur  = bitRead(s0, i);
    if (prev && !cur) handlePress(i);
  }

  // Edge-detect PCF8575 #1 → indices 16–31
  for (uint8_t i = 0; i < 16; i++) {
    bool prev = bitRead(last_s1, i);
    bool cur  = bitRead(s1, i);
    if (prev && !cur) handlePress(i + 16);
  }

  // Edge-detect Arduino extras
  for (uint8_t x = 0; x < EXTRA_COUNT; x++) {
    bool cur = digitalRead(extraPins[x]);
    if (lastExtra[x] == HIGH && cur == LOW) {
      handlePress(extraIndices[x]);
    }
    lastExtra[x] = cur;
  }

  // Handle multi-press timeout and audio status
  handleMultiPress();
  checkAudioStatus();

  // Save last states
  last_s0 = s0;
  last_s1 = s1;

  delay(20);
}

void handlePress(uint8_t idx) {
  if (idx >= 32 + EXTRA_COUNT) return;
  
  unsigned long currentTime = millis();
  
  // Check if this is part of a multi-press sequence
  if (currentTime - lastPressTime[idx] < MULTI_PRESS_WINDOW) {
    pressCount[idx]++;
  } else {
    pressCount[idx] = 1;
  }
  
  lastPressTime[idx] = currentTime;
  
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
  } else {
    uint8_t xp = extraPins[idx - 32];
    Serial.print(F("Arduino Pin "));
    Serial.print(xp);
    Serial.print(F(" (idx "));
    Serial.print(idx);
    Serial.print(F(")"));
  }
  
  if (mapTab[idx].used) {
    Serial.print(F(" → "));
    Serial.print(mapTab[idx].label);
    
    // Show audio info if available
    AudioMapping* audioMap = findAudioByLabel(mapTab[idx].label);
    if (audioMap && audioMap->tracks > 0) {
      Serial.print(F(" [F:"));
      Serial.print(audioMap->folder);
      Serial.print(F("/T:"));
      Serial.print(audioMap->tracks);
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
  
  for (uint8_t i = 0; i < 32 + EXTRA_COUNT; i++) {
    if (pressCount[i] > 0 && 
        (currentTime - lastPressTime[i]) > MULTI_PRESS_WINDOW) {
      
      // Time to play the audio using the actual press count
      if (!inCalibrate && mapTab[i].used) {
        playButtonAudioWithCount(mapTab[i].label, pressCount[i]);
      }
      pressCount[i] = 0; // Reset press count
    }
  }
}

void playButtonAudio(const char* label) {
  if (!label || strlen(label) == 0) {
    Serial.println(F("Invalid label for audio playback"));
    return;
  }
  
  // Find audio mapping for this label
  AudioMapping* audioMap = findAudioByLabel(label);
  if (!audioMap) {
    Serial.print(F("No audio mapping found for label: "));
    Serial.println(label);
    return;
  }
  
  Serial.print(F("Playing audio for label '"));
  Serial.print(label);
  Serial.print(F("' from folder "));
  Serial.print(audioMap->folder);
  if (audioMap->hasRecorded) {
    Serial.print(F(" [RECORDED]"));
  } else {
    Serial.print(F(" [GENERATED]"));
  }
  Serial.print(F(", track count: "));
  Serial.println(audioMap->tracks);
  
  // Find track count and current track for multi-press
  static unsigned long lastPressTime = 0;
  static char lastLabel[16] = "";
  static uint8_t currentTrack = 1;
  
  unsigned long currentTime = millis();
  bool isMultiPress = (currentTime - lastPressTime < 1000) && 
                      (strcmp(lastLabel, label) == 0);
  
  if (isMultiPress && audioMap->tracks > 1) {
    currentTrack++;
    if (currentTrack > audioMap->tracks) {
      currentTrack = 1; // Wrap around
    }
    Serial.print(F("Multi-press detected, switching to track "));
    Serial.println(currentTrack);
  } else {
    currentTrack = 1; // Reset to first track
    strncpy(lastLabel, label, sizeof(lastLabel) - 1);
    lastLabel[sizeof(lastLabel) - 1] = '\0';
  }
  
  lastPressTime = currentTime;
  
  // Build file path
  String filePath = "/";
  if (audioMap->folder < 10) filePath += "0";
  filePath += String(audioMap->folder);
  filePath += "/";
  if (currentTrack < 10) filePath += "00";
  else if (currentTrack < 100) filePath += "0";
  filePath += String(currentTrack);
  filePath += ".mp3";
  
  Serial.print(F("Attempting to play: "));
  Serial.println(filePath);
  
  // Check if file exists
  if (SD.exists(filePath.c_str())) {
    musicPlayer.startPlayingFile(filePath.c_str());
    Serial.println(F("✓ Audio playback started"));
  } else {
    Serial.print(F("⚠ Audio file not found: "));
    Serial.println(filePath);
    
    // If this is a label that should have recorded audio but file is missing
    if (audioMap->hasRecorded) {
      Serial.print(F("⚠ Missing recorded audio for: "));
      Serial.println(label);
    }
    
    // Try track 001 as fallback if we were looking for a different track
    if (currentTrack != 1) {
      String fallbackPath = "/";
      if (audioMap->folder < 10) fallbackPath += "0";
      fallbackPath += String(audioMap->folder);
      fallbackPath += "/001.mp3";
      
      if (SD.exists(fallbackPath.c_str())) {
        Serial.print(F("↳ Playing fallback track: "));
        Serial.println(fallbackPath);
        musicPlayer.startPlayingFile(fallbackPath.c_str());
        currentTrack = 1; // Reset to track 1
      } else {
        Serial.println(F("✗ No audio files found for this label"));
        if (audioMap->fallbackLabel) {
          Serial.print(F("ℹ Suggestion: Generate TTS for '"));
          Serial.print(audioMap->fallbackLabel);
          Serial.println(F("'"));
        }
      }
    } else {
      Serial.println(F("✗ Primary audio file missing"));
      if (audioMap->fallbackLabel) {
        Serial.print(F("ℹ Suggestion: Generate TTS for '"));
        Serial.print(audioMap->fallbackLabel);
        Serial.println(F("'"));
      }
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
  Serial.print(F("' from folder "));
  Serial.print(audioMap->folder);
  Serial.print(F(" [GENERATED], track count: "));
  Serial.print(audioMap->tracks);
  Serial.print(F(", press #"));
  Serial.println(pressCount);
  
  // Calculate track number using baseTrack + (press count - 1)
  // For special buttons: YES(base=1), NO(base=2), WATER(base=3), HELP(base=4)
  // For regular buttons: all start from base=1
  uint8_t trackNumber = audioMap->baseTrack + (pressCount - 1);
  
  // Wrap around if calculated track exceeds available tracks in the folder
  uint8_t maxTrack = audioMap->baseTrack + audioMap->tracks - 1;
  if (trackNumber > maxTrack) {
    trackNumber = audioMap->baseTrack + ((trackNumber - audioMap->baseTrack) % audioMap->tracks);
    Serial.print(F("Wrapping around: press "));
    Serial.print(pressCount);
    Serial.print(F(" -> track "));
    Serial.println(trackNumber);
  }
  
  Serial.print(F("Base track: "));
  Serial.print(audioMap->baseTrack);
  Serial.print(F(", Final track: "));
  Serial.println(trackNumber);
  
  // Build file path
  String filePath = "/";
  if (audioMap->folder < 10) filePath += "0";
  filePath += String(audioMap->folder);
  filePath += "/";
  if (trackNumber < 10) filePath += "00";
  else if (trackNumber < 100) filePath += "0";
  filePath += String(trackNumber);
  filePath += ".mp3";
  
  Serial.print(F("Attempting to play: "));
  Serial.println(filePath);
  
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
    if (audioMap->folder < 10) fallbackPath += "0";
    fallbackPath += String(audioMap->folder);
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

void initializeDefaultMappings() {
  // Clear all mappings first
  for (uint8_t i = 0; i < 32 + EXTRA_COUNT; i++) {
    mapTab[i].used = false;
  }
  
  Serial.println(F("[CONFIG] No default button mappings loaded - use calibration mode to assign buttons"));
  Serial.println(F("[CONFIG] Audio mappings are ready for any button labels"));
}

// Helper function to find audio mapping by label
AudioMapping* findAudioByLabel(const char* label) {
  for (uint8_t i = 0; i < AUDIO_MAPPINGS_COUNT; i++) {
    if (strcmp(audioMappings[i].label, label) == 0) {
      return (AudioMapping*)&audioMappings[i];
    }
  }
  return nullptr;
}

bool hasValidMappings() {
  for (uint8_t i = 0; i < 32 + EXTRA_COUNT; i++) {
    if (mapTab[i].used) return true;
  }
  return false;
}

void loadConfig() {
  File cfg = SD.open("config.csv");
  if (!cfg) {
    Serial.println(F("No config.csv found"));
    return;
  }

  // Clear existing mappings
  for (uint8_t i = 0; i < 32 + EXTRA_COUNT; i++) {
    mapTab[i].used = false;
  }

  // Parse CSV: index,label,folder,maxTracks
  while (cfg.available()) {
    String line = cfg.readStringUntil('\n');
    line.trim();
    
    // Skip header or empty lines
    if (line.startsWith("index") || line.length() < 3) continue;
    
    // Split by commas
    int comma1 = line.indexOf(',');
    if (comma1 < 1) continue;
    
    int comma2 = line.indexOf(',', comma1 + 1);
    int comma3 = line.indexOf(',', comma2 + 1);
    
    uint8_t idx = (uint8_t)line.substring(0, comma1).toInt();
    String lbl = line.substring(comma1 + 1, comma2);
    // Note: comma2 and comma3 variables for folder/tracks are no longer used
    
    lbl.trim();
    if (idx < 32 + EXTRA_COUNT && lbl.length()) {
      lbl.toCharArray(mapTab[idx].label, sizeof(mapTab[idx].label));
      mapTab[idx].used = true;
    }
  }
  
  cfg.close();
  Serial.println(F("Config loaded from config.csv"));
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
  for (uint8_t i = 0; i < 32 + EXTRA_COUNT; i++) {
    if (mapTab[i].used) {
      cfg.print(i);
      cfg.print(',');
      cfg.println(mapTab[i].label);
    }
  }
  
  cfg.close();
  Serial.println(F("Config saved to config.csv"));
}

void printMap() {
  Serial.println(F("\n=== CURRENT BUTTON MAPPINGS (VS1053) ==="));
  for (uint8_t i = 0; i < 32 + EXTRA_COUNT; i++) {
    if (mapTab[i].used) {
      if (i < 32) {
        Serial.print(F("GPIO "));
        Serial.print(i);
      } else {
        uint8_t xp = extraPins[i - 32];
        Serial.print(F("Pin "));
        Serial.print(xp);
      }
      Serial.print(F(" → "));
      Serial.print(mapTab[i].label);
      
      // Show audio info if available
      AudioMapping* audioMap = findAudioByLabel(mapTab[i].label);
      if (audioMap && audioMap->tracks > 0) {
        Serial.print(F(" [Folder "));
        Serial.print(audioMap->folder);
        Serial.print(F(", "));
        Serial.print(audioMap->tracks);
        Serial.print(F(" tracks]"));
      } else {
        Serial.print(F(" [No audio]"));
      }
      Serial.println();
    }
  }
  Serial.println(F("=========================================="));
}

void printMenu() {
  Serial.println(F("\n=== TACTILE COMMUNICATION DEVICE (VS1053) ==="));
  Serial.println(F("C → Enter Calibration mode"));
  Serial.println(F("E → Exit Calibration mode"));
  Serial.println(F("L → Load config from SD (config.csv)"));
  Serial.println(F("S → Save config to SD (config.csv)"));
  Serial.println(F("P → Print current mappings"));
  Serial.println(F("T → Test all buttons"));
  Serial.println(F("+ → Volume up, - → Volume down, 1-9 → Set level"));
  Serial.println(F("X → Stop current playback"));
  Serial.println(F("H → Show this menu"));
  Serial.println(F("\nPress buttons to communicate!"));
}

void printCalibrationInstructions() {
  Serial.println(F("\n*** CALIBRATION MODE ON ***"));
  Serial.println(F("• Press any button to assign/update its label"));
  Serial.println(F("• After press, type label and hit Enter"));
  Serial.println(F("• Press 'E' to exit calibration"));
}

void testAllButtons() {
  Serial.println(F("Testing all configured buttons with VS1053..."));
  Serial.println(F("Press 's' to stop test."));
  
  for (uint8_t i = 0; i < 32 + EXTRA_COUNT; i++) {
    if (Serial.available() && Serial.read() == 's') break;
    
    if (mapTab[i].used) {
      // Check if this label has audio
      AudioMapping* audioMap = findAudioByLabel(mapTab[i].label);
      if (audioMap && audioMap->tracks > 0) {
        Serial.print(F("Testing button "));
        Serial.print(i);
        Serial.print(F(" ("));
        Serial.print(mapTab[i].label);
        Serial.println(F(")"));
        
        // Build file path for first track
        String filePath = "/";
        if (audioMap->folder < 10) filePath += "0";
        filePath += String(audioMap->folder);
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
