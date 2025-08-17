/*
 * Tactile Communication Device - Arduino Code with PCF8575 Support
 * 
 * This version uses PCF8575 I2C port expanders to support more buttons
 * and includes SD card configuration management.
 * 
 * Hardware Components:
 * - Arduino with I2C support
 * - 2x PCF8575 I2C port expanders (0x20, 0x21)
 * - DFPlayer Mini MP3 module
 * - MicroSD card (formatted as FAT32)
 * - 32+ tactile buttons
 * - Speaker (3W, 4-8 ohms)
 * - Rechargeable battery pack
 * 
 * Button Layout:
 * - PCF8575 #0 (0x20): GPIO 0-15  → Special buttons + Letters A-N
 * - PCF8575 #1 (0x21): GPIO 16-31 → Letters O-Z + Punctuation
 * - Arduino pins: 32-34 → Extra buttons/controls
 */

#include <SPI.h>
#include <SD.h>
#include <Wire.h>
#include <Adafruit_PCF8575.h>
#include <SoftwareSerial.h>
#include <DFRobotDFPlayerMini.h>

// SD card and DFPlayer configuration
#define CARDCS     4    // SD card chip-select
#define DFPLAYER_RX 10  // DFPlayer RX (connect to Arduino TX)
#define DFPLAYER_TX 11  // DFPlayer TX (connect to Arduino RX)

// DFPlayer Serial Communication
SoftwareSerial dfSerial(DFPLAYER_RX, DFPLAYER_TX);
DFRobotDFPlayerMini myDFPlayer;

// List of "extra" Arduino pins and their map indices:
const uint8_t extraPins[]    = { 8,  7,  0 };
const uint8_t extraIndices[] = {32, 33, 34};
const uint8_t EXTRA_COUNT    = sizeof(extraPins) / sizeof(extraPins[0]);

Adafruit_PCF8575 pcf0, pcf1;

// mapTab size = 32 (PCF8575) + EXTRA_COUNT (Arduino extras)
struct MapEntry { 
  bool used; 
  char label[12];
  uint8_t folder;     // DFPlayer folder number
  uint8_t maxTracks;  // Number of audio files for this button
  uint8_t currentTrack; // Current track for multi-press cycling
};

MapEntry mapTab[32 + EXTRA_COUNT];

// State for edge-detection
uint16_t last_s0, last_s1;
bool     lastExtra[EXTRA_COUNT];

// Button press timing for multi-press detection
unsigned long lastPressTime[32 + EXTRA_COUNT];
uint8_t pressCount[32 + EXTRA_COUNT];
const unsigned long MULTI_PRESS_WINDOW = 500; // milliseconds

// Calibration mode flag
bool inCalibrate = false;

// Audio playback state
bool isPlaying = false;
unsigned long playStartTime = 0;

// Default button mappings (based on letter_mappings.json)
struct DefaultMapping {
  uint8_t index;
  const char* label;
  uint8_t folder;
  uint8_t tracks;
};

// Default mappings for tactile communication device
// Priority given to RECORDED words (marked with *)
const DefaultMapping defaultMappings[] = {
  // Special buttons (folder 1)
  {0, "YES", 1, 1},
  {1, "NO", 1, 1},
  {2, "WATER", 1, 1},
  {3, "AUX", 1, 4},   // *Hello How are You [RECORDED track 4]
  
  // Letters A-Z (folders 2-27)
  {4, "A", 2, 5},   // *Amer, *Alari, Apple, Arabic Show, *Amory [RECORDED: tracks 1,2,5]
  {5, "B", 3, 5},   // Bathroom, *Bye, Bed, Breathe, blanket [RECORDED: track 2]
  {6, "C", 4, 3},   // Chair, car, Cucumber
  {7, "D", 5, 4},   // *Deen, *Daddy, Doctor, Door [RECORDED: tracks 1,2]
  {8, "E", 6, 0},   // No words assigned
  {9, "F", 7, 2},   // FaceTime, funny
  {10, "G", 8, 2},  // *Good Morning, Go [RECORDED: track 1]
  {11, "H", 9, 2},  // How are you, Heartburn
  {12, "I", 10, 1}, // Inside
  {13, "J", 11, 0}, // No words assigned
  {14, "K", 12, 4}, // *Kiyah, *Kyan, Kleenex, Kaiser [RECORDED: tracks 1,2]
  {15, "L", 13, 4}, // *Lee, *I love you, light down, light up [RECORDED: tracks 1,2]
  
  {16, "M", 14, 3}, // Mohammad, Medicine, Medical
  {17, "N", 15, 3}, // Nada, *Nadowie, *Noah [RECORDED: tracks 2,3]
  {18, "O", 16, 1}, // Outside
  {19, "P", 17, 2}, // Pain, Phone
  {20, "Q", 18, 0}, // No words assigned
  {21, "R", 19, 1}, // Room
  {22, "S", 20, 3}, // Scarf, *Susu, Sinemet [RECORDED: track 2]
  {23, "T", 21, 1}, // TV
  {24, "U", 22, 1}, // *Urgent Care [RECORDED: track 1]
  {25, "V", 23, 0}, // No words assigned
  {26, "W", 24, 4}, // Water, *Walker, *wheelchair, walk [RECORDED: tracks 2,3]
  {27, "X", 25, 0}, // No words assigned
  {28, "Y", 26, 0}, // No words assigned
  {29, "Z", 27, 0}, // No words assigned
  
  // Punctuation (folder 28)
  {30, "SPACE", 28, 1},
  {31, "PERIOD", 28, 1}
};

const uint8_t DEFAULT_MAPPINGS_COUNT = sizeof(defaultMappings) / sizeof(defaultMappings[0]);

// Forward declarations
void printMenu();
void printCalibrationInstructions();
void loadConfig();
void saveConfig();
void printMap();
void handlePress(uint8_t idx);
void initializeDefaultMappings();
void playButtonAudio(uint8_t idx);
void handleMultiPress();
void checkDFPlayerStatus();

void setup() {
  Serial.begin(115200);
  while (!Serial && millis() < 3000); // Wait up to 3 seconds for Serial

  Serial.println(F("Initializing Tactile Communication Device..."));

  // Initialize all timing arrays
  for (uint8_t i = 0; i < 32 + EXTRA_COUNT; i++) {
    lastPressTime[i] = 0;
    pressCount[i] = 0;
  }

  // Initialize SD card
  if (!SD.begin(CARDCS)) {
    Serial.println(F("SD card initialization failed!"));
  } else {
    Serial.println(F("SD card initialized."));
  }

  // Load any existing mappings, or use defaults
  loadConfig();
  if (!hasValidMappings()) {
    Serial.println(F("Loading default mappings..."));
    initializeDefaultMappings();
  }

  // Init I²C on STEMMA QT (Wire1) or standard Wire
  #ifdef WIRE1_SUPPORTED
    Wire1.begin();
    if (!pcf0.begin(0x20, &Wire1)) {
      Serial.println(F("PCF8575 #0 (0x20) not found!"));
      while (1);
    }
    if (!pcf1.begin(0x21, &Wire1)) {
      Serial.println(F("PCF8575 #1 (0x21) not found!"));
      while (1);
    }
  #else
    Wire.begin();
    if (!pcf0.begin(0x20, &Wire)) {
      Serial.println(F("PCF8575 #0 (0x20) not found!"));
      while (1);
    }
    if (!pcf1.begin(0x21, &Wire)) {
      Serial.println(F("PCF8575 #1 (0x21) not found!"));
      while (1);
    }
  #endif

  // Configure PCF8575 pins as inputs with pullup
  for (uint8_t i = 0; i < 16; i++) {
    pcf0.pinMode(i, INPUT_PULLUP);
    pcf1.pinMode(i, INPUT_PULLUP);
  }

  // Init extra Arduino pins and read initial state
  for (uint8_t x = 0; x < EXTRA_COUNT; x++) {
    pinMode(extraPins[x], INPUT_PULLUP);
    lastExtra[x] = digitalRead(extraPins[x]);
  }

  // Prime the expander states
  last_s0 = pcf0.digitalReadWord();
  last_s1 = pcf1.digitalReadWord();

  // Initialize DFPlayer Mini
  dfSerial.begin(9600);
  Serial.println(F("Initializing DFPlayer Mini..."));
  
  if (!myDFPlayer.begin(dfSerial)) {
    Serial.println(F("Unable to begin DFPlayer!"));
    Serial.println(F("Please check connections and SD card"));
  } else {
    Serial.println(F("DFPlayer Mini online."));
    
    // Configure DFPlayer settings
    myDFPlayer.volume(25);  // Set volume (0-30)
    myDFPlayer.outputDevice(DFPLAYER_DEVICE_SD);
    delay(500);
    
    // Play startup sound (optional)
    Serial.println(F("Device ready for communication!"));
  }

  // Show menu
  printMenu();
}

void loop() {
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
        Serial.print(F("Current volume: "));
        Serial.println(myDFPlayer.readVolume());
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

  // Handle multi-press timeout and audio playback
  handleMultiPress();
  checkDFPlayerStatus();

  // Save last states
  last_s0 = s0;
  last_s1 = s1;

  delay(20); // Reduced delay for better responsiveness
}

// ——— Menus ——————————————————————————————————————————————

void printMenu() {
  Serial.println(F("\n=== TACTILE COMMUNICATION DEVICE ==="));
  Serial.println(F("C → Enter Calibration mode"));
  Serial.println(F("E → Exit Calibration mode"));
  Serial.println(F("L → Load config from SD (config.csv)"));
  Serial.println(F("S → Save config to SD (config.csv)"));
  Serial.println(F("P → Print current mappings"));
  Serial.println(F("T → Test all buttons"));
  Serial.println(F("V → Show current volume"));
  Serial.println(F("H → Show this menu"));
  Serial.println(F("\nPress buttons to communicate!"));
}

void printCalibrationInstructions() {
  Serial.println(F("\n*** CALIBRATION MODE ON ***"));
  Serial.println(F("• Press any button to assign/update its label"));
  Serial.println(F("• After press, type label and hit Enter"));
  Serial.println(F("• Press 'E' to exit calibration"));
  Serial.print(F("\nValid indices: 0-31 (PCF8575)"));
  for (uint8_t x = 0; x < EXTRA_COUNT; x++) {
    Serial.print(F(", "));
    Serial.print(extraIndices[x]);
    Serial.print(F("(pin "));
    Serial.print(extraPins[x]);
    Serial.print(F(")"));
  }
  Serial.println();
}

// ——— Configuration Management ————————————————————————————

void initializeDefaultMappings() {
  // Clear all mappings first
  for (uint8_t i = 0; i < 32 + EXTRA_COUNT; i++) {
    mapTab[i].used = false;
    mapTab[i].folder = 0;
    mapTab[i].maxTracks = 0;
    mapTab[i].currentTrack = 1;
  }
  
  // Apply default mappings
  for (uint8_t i = 0; i < DEFAULT_MAPPINGS_COUNT; i++) {
    uint8_t idx = defaultMappings[i].index;
    if (idx < 32 + EXTRA_COUNT) {
      strcpy(mapTab[idx].label, defaultMappings[i].label);
      mapTab[idx].folder = defaultMappings[i].folder;
      mapTab[idx].maxTracks = defaultMappings[i].tracks;
      mapTab[idx].currentTrack = 1;
      mapTab[idx].used = true;
    }
  }
  
  Serial.println(F("Default mappings loaded."));
}

bool hasValidMappings() {
  for (uint8_t i = 0; i < 32 + EXTRA_COUNT; i++) {
    if (mapTab[i].used) return true;
  }
  return false;
}

void loadConfig() {
  if (!SD.begin(CARDCS)) {
    Serial.println(F("SD init failed"));
    return;
  }
  
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
    
    // Split by commas
    int comma1 = line.indexOf(',');
    if (comma1 < 1) continue;
    
    int comma2 = line.indexOf(',', comma1 + 1);
    int comma3 = line.indexOf(',', comma2 + 1);
    
    uint8_t idx = (uint8_t)line.substring(0, comma1).toInt();
    String lbl = line.substring(comma1 + 1, comma2);
    uint8_t folder = (comma2 > 0) ? (uint8_t)line.substring(comma2 + 1, comma3).toInt() : 0;
    uint8_t tracks = (comma3 > 0) ? (uint8_t)line.substring(comma3 + 1).toInt() : 1;
    
    lbl.trim();
    if (idx < 32 + EXTRA_COUNT && lbl.length()) {
      lbl.toCharArray(mapTab[idx].label, sizeof(mapTab[idx].label));
      mapTab[idx].folder = folder;
      mapTab[idx].maxTracks = tracks;
      mapTab[idx].currentTrack = 1;
      mapTab[idx].used = true;
    }
  }
  
  cfg.close();
  Serial.println(F("Config loaded from config.csv"));
}

void saveConfig() {
  if (!SD.begin(CARDCS)) {
    Serial.println(F("SD init failed"));
    return;
  }
  
  SD.remove("config.csv"); // Remove old file
  File cfg = SD.open("config.csv", FILE_WRITE);
  if (!cfg) {
    Serial.println(F("Failed to create config.csv"));
    return;
  }
  
  // Write header
  cfg.println("index,label,folder,maxTracks");
  
  // Write mappings
  for (uint8_t i = 0; i < 32 + EXTRA_COUNT; i++) {
    if (mapTab[i].used) {
      cfg.print(i);
      cfg.print(',');
      cfg.print(mapTab[i].label);
      cfg.print(',');
      cfg.print(mapTab[i].folder);
      cfg.print(',');
      cfg.println(mapTab[i].maxTracks);
    }
  }
  
  cfg.close();
  Serial.println(F("Config saved to config.csv"));
}

void printMap() {
  Serial.println(F("\n=== CURRENT BUTTON MAPPINGS ==="));
  for (uint8_t i = 0; i < 32 + EXTRA_COUNT; i++) {
    if (mapTab[i].used) {
      if (i < 32) {
        Serial.print(F("GPIO "));
        Serial.print(i);
      } else {
        uint8_t xp = extraPins[i - 32];
        Serial.print(F("Pin "));
        Serial.print(xp);
        Serial.print(F(" ("));
        Serial.print(i);
        Serial.print(')');
      }
      Serial.print(F(" → "));
      Serial.print(mapTab[i].label);
      if (mapTab[i].folder > 0) {
        Serial.print(F(" [Folder "));
        Serial.print(mapTab[i].folder);
        Serial.print(F(", "));
        Serial.print(mapTab[i].maxTracks);
        Serial.print(F(" tracks]"));
      }
      Serial.println();
    }
  }
  Serial.println(F("================================"));
}

// ——— Button Handling ——————————————————————————————————————

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
  
  // Print button info
  Serial.print(F("Button "));
  if (idx < 32) {
    Serial.print(F("GPIO "));
    Serial.print(idx);
  } else {
    uint8_t xp = extraPins[idx - 32];
    Serial.print(F("Pin "));
    Serial.print(xp);
  }
  
  if (mapTab[idx].used) {
    Serial.print(F(" ("));
    Serial.print(mapTab[idx].label);
    Serial.print(F(")"));
  }
  Serial.print(F(" pressed! (Press #"));
  Serial.print(pressCount[idx]);
  Serial.println(F(")"));

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
      // You can also set folder/track info here if needed
      Serial.print(F("Mapped "));
      Serial.print(idx);
      Serial.print(F(" → "));
      Serial.println(lbl);
    } else {
      Serial.println(F("(no label entered, skipped)"));
    }
  }
}

void handleMultiPress() {
  unsigned long currentTime = millis();
  
  for (uint8_t i = 0; i < 32 + EXTRA_COUNT; i++) {
    if (pressCount[i] > 0 && 
        (currentTime - lastPressTime[i]) > MULTI_PRESS_WINDOW) {
      
      // Time to play the audio
      if (!inCalibrate) {
        playButtonAudio(i);
      }
      pressCount[i] = 0; // Reset press count
    }
  }
}

void playButtonAudio(uint8_t idx) {
  if (!mapTab[idx].used || mapTab[idx].folder == 0 || mapTab[idx].maxTracks == 0) {
    Serial.print(F("No audio for button "));
    Serial.println(idx);
    return;
  }
  
  // Calculate which track to play based on press count
  uint8_t trackToPlay = ((pressCount[idx] - 1) % mapTab[idx].maxTracks) + 1;
  
  Serial.print(F("Playing: "));
  Serial.print(mapTab[idx].label);
  Serial.print(F(" - Folder "));
  Serial.print(mapTab[idx].folder);
  Serial.print(F(", Track "));
  Serial.println(trackToPlay);
  
  // Play the audio file
  myDFPlayer.playFolder(mapTab[idx].folder, trackToPlay);
  
  isPlaying = true;
  playStartTime = millis();
  
  delay(100); // Brief delay to let playback start
}

void checkDFPlayerStatus() {
  // Check if playback has finished (optional)
  if (isPlaying && (millis() - playStartTime > 5000)) { // Max 5 second timeout
    isPlaying = false;
  }
  
  // Handle DFPlayer status messages (optional)
  if (myDFPlayer.available()) {
    uint8_t type = myDFPlayer.readType();
    int value = myDFPlayer.read();
    
    switch (type) {
      case DFPlayerPlayFinished:
        Serial.println(F("Playback finished"));
        isPlaying = false;
        break;
      case DFPlayerError:
        Serial.print(F("DFPlayer Error: "));
        Serial.println(value);
        isPlaying = false;
        break;
    }
  }
}

void testAllButtons() {
  Serial.println(F("Testing all configured buttons..."));
  Serial.println(F("Press any key to stop test."));
  
  for (uint8_t i = 0; i < 32 + EXTRA_COUNT; i++) {
    if (Serial.available()) break; // Stop if user presses key
    
    if (mapTab[i].used && mapTab[i].folder > 0 && mapTab[i].maxTracks > 0) {
      Serial.print(F("Testing button "));
      Serial.print(i);
      Serial.print(F(" ("));
      Serial.print(mapTab[i].label);
      Serial.println(F(")"));
      
      myDFPlayer.playFolder(mapTab[i].folder, 1); // Play first track
      delay(3000); // Wait between tests
    }
  }
  
  // Clear any input
  while (Serial.available()) Serial.read();
  Serial.println(F("Button test complete."));
}
