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

// Feature switch for SD-defined, hardware-agnostic playlists (Phase 0: disabled, scaffolding only)
#ifndef FEATURE_SD_PLAYLISTS
#define FEATURE_SD_PLAYLISTS 0
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
    if (key.equalsIgnoreCase("PRIORITY")) {
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
  f.print(F("PRIORITY="));
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
const uint8_t EXTRA_COUNT = sizeof(extraPins) / sizeof(extraPins[0]);

// Button mapping structure (now just stores button labels)
struct MapEntry { 
  bool used; 
  char label[12];
};

MapEntry mapTab[EXPANDER_BUTTONS + EXTRA_COUNT];

// State for edge-detection
uint16_t last_s[NUM_PCF];
bool     lastExtra[EXTRA_COUNT];

// Button press timing for multi-press detection
unsigned long lastPressTime[48 + EXTRA_COUNT];
uint8_t pressCount[48 + EXTRA_COUNT];
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
enum PriorityMode : uint8_t {
  HUMAN_FIRST = 0,      // Personal recordings play first, then TTS
  GENERATED_FIRST = 1   // TTS plays first, then personal recordings
};

const int EEPROM_ADDR_MODE = 0;  // EEPROM address to store mode (1 byte)
PriorityMode currentMode = HUMAN_FIRST;

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
  if (hardwareIndex < 48 + EXTRA_COUNT && mapTab[hardwareIndex].used) {
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

// Load hardware button mapping from CONFIG.CSV
bool loadHardwareMapping() {
  File cfg = SD.open("CONFIG.CSV");
  if (!cfg) {
    Serial.println(F("[CONFIG] No CONFIG.CSV found - using calibration mode"));
    return false;
  }

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
    Serial.println(F("[CONFIG] No valid entries found in CONFIG.CSV"));
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
        
        if (hwIndex < 48 + EXTRA_COUNT && label.length() > 0) {
          hardwareButtonMap[idx].hardwareIndex = hwIndex;
          strncpy(hardwareButtonMap[idx].label, label.c_str(), 3);
          hardwareButtonMap[idx].label[3] = '\0';
          idx++;
        }
      }
    }
  }
  cfg.close();
  
  HARDWARE_BUTTON_COUNT = idx; // Update to actual loaded count
  
  Serial.print(F("[CONFIG] Loaded "));
  Serial.print(HARDWARE_BUTTON_COUNT);
  Serial.println(F(" hardware button mappings from CONFIG.CSV"));
  
  return true;
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
        // Toggle priority mode manually
        currentMode = (currentMode == HUMAN_FIRST) ? GENERATED_FIRST : HUMAN_FIRST;
        savePriorityMode();
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
  if (idx >= 48 + EXTRA_COUNT) return;
  
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
  
  for (uint8_t i = 0; i < 48 + EXTRA_COUNT; i++) {
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

// playButtonAudio function removed - replaced by playButtonAudioWithCount with two-bank priority system

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
  Serial.println(currentMode == HUMAN_FIRST ? F("HUMAN_FIRST") : F("GENERATED_FIRST"));
  
  // Two-bank priority mode track selection
  uint8_t k = (pressCount - 1); // 0-based press index
  bool humanFirst = (currentMode == HUMAN_FIRST);
  
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
      if (audioMap && (audioMap->recCount > 0 || audioMap->ttsCount > 0)) {
        Serial.print(F("Testing button "));
        Serial.print(i);
        Serial.print(F(" ("));
        Serial.print(mapTab[i].label);
        Serial.println(F(")"));
        
        // Build file path for first track (use recFolder if available, else ttsFolder)
        uint8_t testFolder = (audioMap->recCount > 0) ? audioMap->recFolder : audioMap->ttsFolder;
        String filePath = "/";
        if (testFolder < 10) filePath += "0";
        filePath += String(testFolder);
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

// ===== PRIORITY MODE FUNCTIONS =====

// Load priority mode from EEPROM
void loadPriorityMode() {
  uint8_t savedMode = EEPROM.read(EEPROM_ADDR_MODE);
  if (savedMode <= GENERATED_FIRST) {
    currentMode = (PriorityMode)savedMode;
  } else {
    currentMode = HUMAN_FIRST;  // Default to human first
  }
  
  Serial.print(F("Priority mode loaded: "));
  Serial.println(currentMode == HUMAN_FIRST ? F("HUMAN_FIRST") : F("GENERATED_FIRST"));
}

// Save priority mode to EEPROM
void savePriorityMode() {
  EEPROM.update(EEPROM_ADDR_MODE, (uint8_t)currentMode);
  Serial.print(F("Priority mode saved: "));
  Serial.println(currentMode == HUMAN_FIRST ? F("HUMAN_FIRST") : F("GENERATED_FIRST"));
}

// Play mode announcement audio
void announcePriorityMode(PriorityMode mode) {
  String audioFile;
  
  if (mode == HUMAN_FIRST) {
    audioFile = "/33/004.mp3";  // "Personal voice first" - correct announcement
    Serial.println(F("🎵 Announcing: Personal voice first"));
  } else {
    audioFile = "/33/005.mp3";  // "Computer voice first" - correct announcement
    Serial.println(F("🎵 Announcing: Computer voice first"));
  }
  
  // Stop any current playback
  if (musicPlayer.playingMusic) {
    musicPlayer.stopPlaying();
    delay(100);
  }
  
  // Play announcement
  if (SD.exists(audioFile.c_str())) {
    musicPlayer.startPlayingFile(audioFile.c_str());
    Serial.print(F("Playing mode announcement: "));
    Serial.println(audioFile);
  } else {
    Serial.print(F("⚠️  Mode announcement file not found: "));
    Serial.println(audioFile);
  }
}

// Handle Period button press with triple-press detection
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
    currentMode = (currentMode == HUMAN_FIRST) ? GENERATED_FIRST : HUMAN_FIRST;
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

// Finalize period window - call this in main loop
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
  for (uint8_t i = 0; i < 48 + EXTRA_COUNT; i++) {
    mapTab[i].used = false;
    memset(mapTab[i].label, 0, sizeof(mapTab[i].label));
  }
  
  // Try to load hardware mappings from SD card first
  if (loadHardwareMapping()) {
    // Set up hardware mappings in mapTab for compatibility
    for (uint8_t i = 0; i < HARDWARE_BUTTON_COUNT; i++) {
      uint8_t hwIndex = hardwareButtonMap[i].hardwareIndex;
      if (hwIndex < 48 + EXTRA_COUNT) {
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

// Print serial command menu
void printMenu() {
  Serial.println(F("\n=== TACTILE COMMUNICATOR COMMANDS ==="));
  Serial.println(F("L/l - Load config from SD"));
  Serial.println(F("S/s - Save config to SD"));
  Serial.println(F("P/p - Print current mappings"));
  Serial.println(F("H/h - Show this help menu"));
  Serial.println(F("M/m - Toggle priority mode (HUMAN_FIRST/GENERATED_FIRST)"));
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

// Priority mode integration complete - using existing functions with enhancements
