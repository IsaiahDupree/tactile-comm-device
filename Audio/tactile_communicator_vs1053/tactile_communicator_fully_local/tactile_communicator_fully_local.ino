/*
 * TACTILE COMMUNICATION DEVICE - DATA-DRIVEN VERSION
 * 
 * Future-proof, label-centric architecture:
 * - Hardware mapping: GPIO → Label (buttons.csv)
 * - Content mapping: Label → Ordered audio clips (playlist.csv)
 * - Text manifest: Audio index for console logging (audio_index.csv)
 * 
 * SD Card Layout:
 * /01 ... /33     <- TTS folders
 * /101 ... /133   <- REC folders (+100 convention)
 * /config/
 *   buttons.csv     <- GPIO index → label mapping
 *   playlist.csv    <- label → ordered clips (multi-press)
 *   audio_index.csv <- optional text manifest for logging
 */

#include <SPI.h>
#include "SD.h"
#include "Adafruit_VS1053.h"
#include <Wire.h>
#include "PCF8575.h"
#include <EEPROM.h>

// ===== HARDWARE CONFIGURATION =====
#define BREAKOUT_RESET  9
#define BREAKOUT_CS     10
#define BREAKOUT_DCS    8
#define CARDCS          4
#define DREQ            3

#define EXTRA_COUNT 4
const uint8_t extraPins[EXTRA_COUNT] = {A0, A1, A2, A3};

// I2C addresses for PCF8575 expanders
PCF8575 pcf0(0x20);
PCF8575 pcf1(0x21);

// VS1053 audio codec
Adafruit_VS1053_FilePlayer musicPlayer = 
  Adafruit_VS1053_FilePlayer(BREAKOUT_RESET, BREAKOUT_CS, BREAKOUT_DCS, DREQ, CARDCS);

// ===== DATA STRUCTURES =====

struct AudioClip {
  char bank[4];      // "REC" or "TTS"
  char path[32];     // Full path to MP3 file
  char text[24];     // Human-readable text for logging
};

struct ButtonMapping {
  uint8_t index;
  char label[4];
  bool used;
};

struct PlaylistEntry {
  char label[4];
  uint8_t press;
  AudioClip clip;
};

// ===== GLOBAL VARIABLES =====

ButtonMapping* buttonMappings = nullptr;
uint8_t buttonMappingCount = 0;

PlaylistEntry* playlist = nullptr;
uint16_t playlistCount = 0;

// State variables
uint16_t last_s0, last_s1;
uint8_t lastExtra[EXTRA_COUNT];
bool inCalibrate = false;
bool isPlaying = false;
String currentTrackPath = "";

// Multi-press detection
const unsigned long MULTI_PRESS_WINDOW = 1000;
unsigned long lastPressTime[32 + EXTRA_COUNT];
uint8_t pressCount[32 + EXTRA_COUNT];

// Priority mode
enum PriorityMode { HUMAN_FIRST = 0, GENERATED_FIRST = 1 };
PriorityMode currentMode = HUMAN_FIRST;
const uint8_t EEPROM_ADDR_MODE = 0;

// Period button triple-press detection
const unsigned long PERIOD_WINDOW_MS = 2000;
unsigned long periodWindowStart = 0;
uint8_t periodPressCount = 0;

// ===== SETUP FUNCTION =====
void setup() {
  Serial.begin(115200);
  Serial.println(F("\n=== TACTILE COMMUNICATION DEVICE (DATA-DRIVEN) ==="));
  
  // Initialize I2C
  Wire.begin();
  
  // Initialize PCF8575 expanders
  pcf0.begin();
  pcf1.begin();
  
  // Initialize extra pins
  for (uint8_t i = 0; i < EXTRA_COUNT; i++) {
    pinMode(extraPins[i], INPUT_PULLUP);
    lastExtra[i] = HIGH;
  }
  
  // Initialize VS1053
  if (!musicPlayer.begin()) {
    Serial.println(F("VS1053 not found"));
    while (1);
  }
  Serial.println(F("VS1053 found"));
  
  // Initialize SD card
  if (!SD.begin(CARDCS)) {
    Serial.println(F("SD failed, or not present"));
    while (1);
  }
  Serial.println(F("SD card initialized"));
  
  // Set volume (lower numbers = louder)
  musicPlayer.setVolume(10, 10);
  
  // Load priority mode from EEPROM
  loadPriorityMode();
  
  // Initialize state arrays
  for (uint8_t i = 0; i < 32 + EXTRA_COUNT; i++) {
    lastPressTime[i] = 0;
    pressCount[i] = 0;
  }
  
  // Prime the expander states
  last_s0 = pcf0.read16();
  last_s1 = pcf1.read16();
  
  // Load configuration from SD card
  loadConfiguration();
  
  // Test audio system
  Serial.println(F("Testing audio system..."));
  if (SD.exists("/01/001.mp3")) {
    Serial.println(F("Playing startup audio..."));
    musicPlayer.startPlayingFile("/01/001.mp3");
    delay(2000);
    musicPlayer.stopPlaying();
  }
  
  Serial.println(F("\n=================================================="));
  Serial.println(F("    TACTILE COMMUNICATION DEVICE READY!"));
  Serial.println(F("=================================================="));
  printMenu();
}

// ===== MAIN LOOP =====
void loop() {
  musicPlayer.feedBuffer();
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
        Serial.println(F("Calibration mode OFF"));
        break;
      case 'L': case 'l':
        loadConfiguration();
        break;
      case 'S': case 's':
        saveButtonMappings();
        break;
      case 'P': case 'p':
        printCurrentMappings();
        break;
      case 'H': case 'h':
        printMenu();
        break;
      case 'M': case 'm':
        togglePriorityMode();
        break;
      case 'T': case 't':
        testAllButtons();
        break;
      case 'U': case 'u':
        sanityCheckAudio();
        break;
      case 'X': case 'x':
        musicPlayer.stopPlaying();
        Serial.println(F("Audio stopped"));
        break;
      case '+':
        musicPlayer.setVolume(1, 1);
        Serial.println(F("Volume: Maximum"));
        break;
      case '-':
        musicPlayer.setVolume(20, 20);
        Serial.println(F("Volume: Moderate"));
        break;
    }
  }
  
  // Read PCF8575 expanders
  uint16_t s0 = pcf0.read16();
  uint16_t s1 = pcf1.read16();
  
  // Check for button presses on first expander (indices 0-15)
  for (uint8_t i = 0; i < 16; i++) {
    bool lastBit = (last_s0 >> i) & 1;
    bool curBit = (s0 >> i) & 1;
    if (lastBit == HIGH && curBit == LOW) {
      handlePress(i);
    }
  }
  
  // Check for button presses on second expander (indices 16-31)
  for (uint8_t i = 0; i < 16; i++) {
    bool lastBit = (last_s1 >> i) & 1;
    bool curBit = (s1 >> i) & 1;
    if (lastBit == HIGH && curBit == LOW) {
      handlePress(i + 16);
    }
  }
  
  // Check extra pins (indices 32+)
  for (uint8_t x = 0; x < EXTRA_COUNT; x++) {
    uint8_t cur = digitalRead(extraPins[x]);
    if (lastExtra[x] == HIGH && cur == LOW) {
      handlePress(32 + x);
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

// ===== CONFIGURATION LOADING FUNCTIONS =====

void loadConfiguration() {
  Serial.println(F("[CONFIG] Loading data-driven configuration..."));
  
  bool buttonsLoaded = loadButtonMappings();
  bool playlistLoaded = loadPlaylist();
  
  if (buttonsLoaded && playlistLoaded) {
    Serial.println(F("[CONFIG] Configuration loaded successfully"));
  } else {
    Serial.println(F("[CONFIG] Using fallback/calibration mode"));
  }
}

bool loadButtonMappings() {
  File file = SD.open("/config/buttons.csv");
  if (!file) {
    Serial.println(F("[CONFIG] /config/buttons.csv not found"));
    return false;
  }
  
  // Count lines first
  buttonMappingCount = 0;
  String line;
  file.readStringUntil('\n'); // Skip header
  while (file.available()) {
    line = file.readStringUntil('\n');
    if (line.length() > 0) buttonMappingCount++;
  }
  file.close();
  
  if (buttonMappingCount == 0) return false;
  
  // Allocate memory
  if (buttonMappings) free(buttonMappings);
  buttonMappings = (ButtonMapping*)malloc(buttonMappingCount * sizeof(ButtonMapping));
  if (!buttonMappings) return false;
  
  // Load data
  file = SD.open("/config/buttons.csv");
  file.readStringUntil('\n'); // Skip header
  uint8_t idx = 0;
  
  while (file.available() && idx < buttonMappingCount) {
    line = file.readStringUntil('\n');
    line.trim();
    if (line.length() == 0) continue;
    
    // Parse CSV: index,label
    int comma = line.indexOf(',');
    if (comma > 0) {
      buttonMappings[idx].index = line.substring(0, comma).toInt();
      String label = line.substring(comma + 1);
      label.trim();
      strncpy(buttonMappings[idx].label, label.c_str(), 3);
      buttonMappings[idx].label[3] = '\0';
      buttonMappings[idx].used = true;
      idx++;
    }
  }
  file.close();
  
  Serial.print(F("[CONFIG] Loaded "));
  Serial.print(buttonMappingCount);
  Serial.println(F(" button mappings"));
  return true;
}

bool loadPlaylist() {
  File file = SD.open("/config/playlist.csv");
  if (!file) {
    Serial.println(F("[CONFIG] /config/playlist.csv not found"));
    return false;
  }
  
  // Count lines first
  playlistCount = 0;
  String line;
  file.readStringUntil('\n'); // Skip header
  while (file.available()) {
    line = file.readStringUntil('\n');
    if (line.length() > 0) playlistCount++;
  }
  file.close();
  
  if (playlistCount == 0) return false;
  
  // Allocate memory
  if (playlist) free(playlist);
  playlist = (PlaylistEntry*)malloc(playlistCount * sizeof(PlaylistEntry));
  if (!playlist) return false;
  
  // Load data
  file = SD.open("/config/playlist.csv");
  file.readStringUntil('\n'); // Skip header
  uint16_t idx = 0;
  
  while (file.available() && idx < playlistCount) {
    line = file.readStringUntil('\n');
    line.trim();
    if (line.length() == 0) continue;
    
    // Parse CSV: label,press,bank,path,text
    int commas[4];
    int pos = 0;
    for (int i = 0; i < 4; i++) {
      commas[i] = line.indexOf(',', pos);
      if (commas[i] == -1) break;
      pos = commas[i] + 1;
    }
    
    if (commas[3] > 0) {
      String label = line.substring(0, commas[0]);
      String press = line.substring(commas[0] + 1, commas[1]);
      String bank = line.substring(commas[1] + 1, commas[2]);
      String path = line.substring(commas[2] + 1, commas[3]);
      String text = line.substring(commas[3] + 1);
      
      strncpy(playlist[idx].label, label.c_str(), 3);
      playlist[idx].label[3] = '\0';
      playlist[idx].press = press.toInt();
      strncpy(playlist[idx].clip.bank, bank.c_str(), 3);
      playlist[idx].clip.bank[3] = '\0';
      strncpy(playlist[idx].clip.path, path.c_str(), 31);
      playlist[idx].clip.path[31] = '\0';
      strncpy(playlist[idx].clip.text, text.c_str(), 23);
      playlist[idx].clip.text[23] = '\0';
      
      idx++;
    }
  }
  file.close();
  
  Serial.print(F("[CONFIG] Loaded "));
  Serial.print(playlistCount);
  Serial.println(F(" playlist entries"));
  return true;
}

// ===== BUTTON HANDLING FUNCTIONS =====

void handlePress(uint8_t idx) {
  if (idx >= 32 + EXTRA_COUNT) return;
  
  unsigned long currentTime = millis();
  
  if (currentTime - lastPressTime[idx] < MULTI_PRESS_WINDOW) {
    pressCount[idx]++;
  } else {
    pressCount[idx] = 1;
  }
  
  lastPressTime[idx] = currentTime;
  
  const char* buttonLabel = getButtonLabel(idx);
  bool hasMapping = (strlen(buttonLabel) > 0);
  
  Serial.print(F("[BUTTON] Index "));
  Serial.print(idx);
  Serial.print(F(" → "));
  
  if (hasMapping) {
    Serial.print(F("'"));
    Serial.print(buttonLabel);
    Serial.print(F("' (press "));
    Serial.print(pressCount[idx]);
    Serial.println(F(")"));
    
    if (strcmp(buttonLabel, ".") == 0) {
      handlePeriodPress();
      pressCount[idx] = 0;
      return;
    }
  } else {
    Serial.println(F("UNMAPPED"));
  }
  
  if (inCalibrate) {
    Serial.print(F("Enter new label for index "));
    Serial.print(idx);
    Serial.println(F(":"));
    while (!Serial.available()) delay(10);
    String lbl = Serial.readStringUntil('\n');
    lbl.trim();
    lbl.toUpperCase();
    
    if (lbl.length()) {
      addButtonMapping(idx, lbl.c_str());
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
      
      const char* buttonLabel = getButtonLabel(i);
      bool hasMapping = (strlen(buttonLabel) > 0);
      
      if (!inCalibrate && hasMapping) {
        playButtonAudio(buttonLabel, pressCount[i]);
      }
      pressCount[i] = 0;
    }
  }
}

// ===== AUDIO PLAYBACK FUNCTIONS =====

void playButtonAudio(const char* label, uint8_t pressCount) {
  AudioClip* clips[16];
  uint8_t clipCount = 0;
  
  for (uint16_t i = 0; i < playlistCount && clipCount < 16; i++) {
    if (strcmp(playlist[i].label, label) == 0) {
      clips[clipCount] = &playlist[i].clip;
      clipCount++;
    }
  }
  
  if (clipCount == 0) {
    Serial.print(F("[AUDIO] No clips found for label: "));
    Serial.println(label);
    return;
  }
  
  uint8_t clipIndex = (pressCount - 1) % clipCount;
  AudioClip* selectedClip = clips[clipIndex];
  
  // Apply priority mode for REC vs TTS
  if (currentMode == GENERATED_FIRST) {
    for (uint8_t i = 0; i < clipCount; i++) {
      uint8_t idx = (clipIndex + i) % clipCount;
      if (strcmp(clips[idx]->bank, "TTS") == 0) {
        selectedClip = clips[idx];
        break;
      }
    }
  } else {
    for (uint8_t i = 0; i < clipCount; i++) {
      uint8_t idx = (clipIndex + i) % clipCount;
      if (strcmp(clips[idx]->bank, "REC") == 0) {
        selectedClip = clips[idx];
        break;
      }
    }
  }
  
  if (SD.exists(selectedClip->path)) {
    Serial.print(F("[AUDIO] Playing: "));
    Serial.print(selectedClip->text);
    Serial.print(F(" ("));
    Serial.print(selectedClip->bank);
    Serial.print(F(") - "));
    Serial.println(selectedClip->path);
    
    musicPlayer.startPlayingFile(selectedClip->path);
    isPlaying = true;
    currentTrackPath = selectedClip->path;
  } else {
    Serial.print(F("[AUDIO] File not found: "));
    Serial.println(selectedClip->path);
  }
}

void checkAudioStatus() {
  if (isPlaying && musicPlayer.stopped()) {
    Serial.print(F("[AUDIO] Playback finished: "));
    Serial.println(currentTrackPath);
    isPlaying = false;
    currentTrackPath = "";
  }
}

// ===== HELPER FUNCTIONS =====

const char* getButtonLabel(uint8_t index) {
  for (uint8_t i = 0; i < buttonMappingCount; i++) {
    if (buttonMappings[i].index == index && buttonMappings[i].used) {
      return buttonMappings[i].label;
    }
  }
  return "";
}

void addButtonMapping(uint8_t index, const char* label) {
  for (uint8_t i = 0; i < buttonMappingCount; i++) {
    if (buttonMappings[i].index == index) {
      strncpy(buttonMappings[i].label, label, 3);
      buttonMappings[i].label[3] = '\0';
      buttonMappings[i].used = true;
      return;
    }
  }
  
  Serial.print(F("Would add new mapping: "));
  Serial.print(index);
  Serial.print(F(" → "));
  Serial.println(label);
}

void saveButtonMappings() {
  SD.remove("/config/buttons.csv");
  File file = SD.open("/config/buttons.csv", FILE_WRITE);
  if (!file) {
    Serial.println(F("Failed to create /config/buttons.csv"));
    return;
  }
  
  file.println("index,label");
  
  for (uint8_t i = 0; i < buttonMappingCount; i++) {
    if (buttonMappings[i].used) {
      file.print(buttonMappings[i].index);
      file.print(',');
      file.println(buttonMappings[i].label);
    }
  }
  
  file.close();
  Serial.println(F("Button mappings saved to /config/buttons.csv"));
}

void printCurrentMappings() {
  Serial.println(F("\n=== CURRENT BUTTON MAPPINGS ==="));
  for (uint8_t i = 0; i < buttonMappingCount; i++) {
    if (buttonMappings[i].used) {
      Serial.print(F("Index "));
      Serial.print(buttonMappings[i].index);
      Serial.print(F(" → "));
      Serial.println(buttonMappings[i].label);
    }
  }
  Serial.println(F("================================"));
}

void testAllButtons() {
  Serial.println(F("Testing all configured buttons..."));
  
  for (uint8_t i = 0; i < buttonMappingCount; i++) {
    if (buttonMappings[i].used) {
      Serial.print(F("Testing "));
      Serial.print(buttonMappings[i].label);
      Serial.println();
      
      playButtonAudio(buttonMappings[i].label, 1);
      delay(2000);
      musicPlayer.stopPlaying();
      delay(500);
    }
  }
  
  Serial.println(F("Test complete."));
}

void sanityCheckAudio() {
  Serial.println(F("[CHECK] Verifying playlist audio files..."));
  
  for (uint16_t i = 0; i < playlistCount; i++) {
    if (!SD.exists(playlist[i].clip.path)) {
      Serial.print(F("⚠ Missing: "));
      Serial.print(playlist[i].label);
      Serial.print(F(" press "));
      Serial.print(playlist[i].press);
      Serial.print(F(": "));
      Serial.println(playlist[i].clip.path);
    }
  }
  
  Serial.println(F("[CHECK] Complete."));
}

// ===== PRIORITY MODE FUNCTIONS =====

void loadPriorityMode() {
  uint8_t savedMode = EEPROM.read(EEPROM_ADDR_MODE);
  if (savedMode <= GENERATED_FIRST) {
    currentMode = (PriorityMode)savedMode;
  } else {
    currentMode = HUMAN_FIRST;
  }
  
  Serial.print(F("Priority mode: "));
  Serial.println(currentMode == HUMAN_FIRST ? F("HUMAN_FIRST") : F("GENERATED_FIRST"));
}

void savePriorityMode() {
  EEPROM.update(EEPROM_ADDR_MODE, (uint8_t)currentMode);
}

void togglePriorityMode() {
  currentMode = (currentMode == HUMAN_FIRST) ? GENERATED_FIRST : HUMAN_FIRST;
  savePriorityMode();
  announcePriorityMode(currentMode);
}

void announcePriorityMode(PriorityMode mode) {
  String audioFile = (mode == HUMAN_FIRST) ? "/33/004.mp3" : "/33/005.mp3";
  
  if (musicPlayer.playingMusic) {
    musicPlayer.stopPlaying();
    delay(100);
  }
  
  if (SD.exists(audioFile.c_str())) {
    musicPlayer.startPlayingFile(audioFile.c_str());
  }
}

void handlePeriodPress() {
  const unsigned long now = millis();
  
  if (periodPressCount == 0 || (now - periodWindowStart) > PERIOD_WINDOW_MS) {
    periodWindowStart = now;
    periodPressCount = 0;
  }
  
  periodPressCount++;
  
  if (periodPressCount == 3 && (now - periodWindowStart) <= PERIOD_WINDOW_MS) {
    togglePriorityMode();
    periodPressCount = 0;
    periodWindowStart = 0;
    return;
  }
}

void finalizePeriodWindow() {
  if (periodPressCount > 0 && (millis() - periodWindowStart) > PERIOD_WINDOW_MS) {
    if (periodPressCount < 3) {
      playButtonAudio(".", 1);
    }
    periodPressCount = 0;
    periodWindowStart = 0;
  }
}

void printCalibrationInstructions() {
  Serial.println(F("\n*** CALIBRATION MODE ON ***"));
  Serial.println(F("• Press any button to assign/update its label"));
  Serial.println(F("• After press, type label and hit Enter"));
  Serial.println(F("• Press 'E' to exit calibration"));
}

void printMenu() {
  Serial.println(F("\n=== TACTILE COMMUNICATOR COMMANDS ==="));
  Serial.println(F("C/c - Enter calibration mode"));
  Serial.println(F("E/e - Exit calibration mode"));
  Serial.println(F("L/l - Load config from SD"));
  Serial.println(F("S/s - Save button mappings"));
  Serial.println(F("P/p - Print current mappings"));
  Serial.println(F("H/h - Show this help menu"));
  Serial.println(F("M/m - Toggle priority mode"));
  Serial.println(F("T/t - Test all buttons"));
  Serial.println(F("U/u - Check audio file sanity"));
  Serial.println(F("X/x - Stop current audio"));
  Serial.println(F("+/- - Volume control"));
  Serial.println(F("========================================\n"));
}
