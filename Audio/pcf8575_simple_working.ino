#include <SPI.h>
#include <SD.h>
#include <Wire.h>
#include <Adafruit_PCF8575.h>

#define CARDCS     4    // SD card chip‐select

// List of "extra" Arduino pins and their map indices:
const uint8_t extraPins[]    = { 8,  7,  0 };
const uint8_t extraIndices[] = {32, 33, 34};
const uint8_t EXTRA_COUNT    = sizeof(extraPins) / sizeof(extraPins[0]);

Adafruit_PCF8575 pcf0, pcf1;

// mapTab size = 32 (PCF8575) + EXTRA_COUNT (Arduino extras)
struct MapEntry { bool used; char label[12]; };
MapEntry mapTab[32 + EXTRA_COUNT];

// State for edge‐detection
uint16_t last_s0, last_s1;
bool     lastExtra[EXTRA_COUNT];

// Calibration mode flag
bool inCalibrate = false;

// — forward declarations —
void printMenu();
void printCalibrationInstructions();
void loadConfig();
void saveConfig();
void printMap();
void handlePress(uint8_t idx);

void setup() {
  Serial.begin(115200);
  while (!Serial);

  // Load any existing mappings
  loadConfig();

  // Init I²C on STEMMA QT
  Wire1.begin();

  // Init both PCF8575 expanders (0x20, 0x21)
  if (!pcf0.begin(0x20, &Wire1)) while (1);
  if (!pcf1.begin(0x21, &Wire1)) while (1);
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

  // Show menu
  printMenu();
}

void loop() {
  // --- Handle Serial commands ---
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
      case 'L': case 'l': loadConfig();  break;
      case 'S': case 's': saveConfig();  break;
      case 'P': case 'p': printMap();    break;
      case 'H': case 'h': printMenu();   break;
    }
  }

  // --- Read current expander states ---
  uint16_t s0 = pcf0.digitalReadWord();   // GPIO 0–15
  uint16_t s1 = pcf1.digitalReadWord();   // GPIO 16–31

  // Edge‐detect PCF8575 #0 → indices 0–15
  for (uint8_t i = 0; i < 16; i++) {
    bool prev = bitRead(last_s0, i);
    bool cur  = bitRead(s0,    i);
    if (prev && !cur) handlePress(i);
  }
  // Edge‐detect PCF8575 #1 → indices 16–31
  for (uint8_t i = 0; i < 16; i++) {
    bool prev = bitRead(last_s1, i);
    bool cur  = bitRead(s1,    i);
    if (prev && !cur) handlePress(i + 16);
  }

  // Edge‐detect Arduino extras
  for (uint8_t x = 0; x < EXTRA_COUNT; x++) {
    bool cur = digitalRead(extraPins[x]);
    if (lastExtra[x] == HIGH && cur == LOW) {
      handlePress(extraIndices[x]);
    }
    lastExtra[x] = cur;
  }

  // Save last states
  last_s0 = s0;
  last_s1 = s1;

  delay(50);
}

// ——— Menus ——————————————————————————————————————————————

void printMenu() {
  Serial.println(F("\n--- MENU ---"));
  Serial.println(F("C → Enter Calibration mode"));
  Serial.println(F("E → Exit Calibration mode"));
  Serial.println(F("L → Load config from SD (config.csv)"));
  Serial.println(F("S → Save config to SD   (config.csv)"));
  Serial.println(F("P → Print current mappings"));
  Serial.println(F("H → Show this menu"));
  Serial.println(F("In calibration: press a button to map it."));
}

void printCalibrationInstructions() {
  Serial.println(F("\n*** CALIBRATION MODE ON ***"));
  Serial.println(F("• Press any GPIO (0–31 for PCF, 32–34 for Arduino pins)"));
  Serial.println(F("  to assign or update its label."));
  Serial.println(F("• After press, type label (max 11 chars) and hit Enter."));
  Serial.println(F("• Press 'E' to exit calibration.\n"));
  Serial.print(F("Valid GPIO indices: "));
  for (uint8_t i = 0; i < 32; i++) {
    Serial.print(i);
    if (i < 31) Serial.print(',');
  }
  for (uint8_t x = 0; x < EXTRA_COUNT; x++) {
    Serial.print(F(","));
    Serial.print(extraIndices[x]);
    Serial.print(F("(pin "));
    Serial.print(extraPins[x]);
    Serial.print(F(")"));
  }
  Serial.println();
}

// ——— Config I/O ————————————————————————————————————————————

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
  // Clear
  for (uint8_t i = 0; i < 32 + EXTRA_COUNT; i++) {
    mapTab[i].used = false;
  }
  // Parse
  while (cfg.available()) {
    String line = cfg.readStringUntil('\n');
    line.trim();
    int comma = line.indexOf(',');
    if (comma < 1) continue;
    uint8_t idx = (uint8_t)line.substring(0, comma).toInt();
    String lbl = line.substring(comma + 1);
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
  if (!SD.begin(CARDCS)) {
    Serial.println(F("SD init failed")); 
    return;
  }
  File cfg = SD.open("config.csv", FILE_WRITE);
  if (!cfg) {
    Serial.println(F("Failed to open config.csv")); 
    return;
  }
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
  Serial.println(F("\nCurrent mappings:"));
  for (uint8_t i = 0; i < 32 + EXTRA_COUNT; i++) {
    if (mapTab[i].used) {
      if (i < 32) {
        Serial.print(F("PCF8575 GPIO "));
        Serial.print(i);
      } else {
        // Arduino extras
        uint8_t xp = extraPins[i - 32];
        Serial.print(F("Arduino GPIO pin "));
        Serial.print(xp);
        Serial.print(F(" (idx "));
        Serial.print(i);
        Serial.print(')');
      }
      Serial.print(F(" → "));
      Serial.println(mapTab[i].label);
    }
  }
}

// ——— Button handling ——————————————————————————————————————

void handlePress(uint8_t idx) {
  // Print source & index
  if (idx < 32) {
    Serial.print(F("PCF8575 GPIO "));
    Serial.print(idx);
  } else {
    uint8_t xp = extraPins[idx - 32];
    Serial.print(F("Arduino GPIO pin "));
    Serial.print(xp);
    Serial.print(F(" (idx "));
    Serial.print(idx);
    Serial.print(')');
  }
  // Existing label
  if (mapTab[idx].used) {
    Serial.print(F(" ("));
    Serial.print(mapTab[idx].label);
    Serial.print(F(")"));
  }
  Serial.println(F(" pressed!"));

  // Calibration prompt
  if (inCalibrate) {
    Serial.println(F("Enter new label:"));
    while (!Serial.available()) delay(5);
    String lbl = Serial.readStringUntil('\n');
    lbl.trim(); lbl.toUpperCase();
    if (lbl.length()) {
      lbl.toCharArray(mapTab[idx].label, sizeof(mapTab[idx].label));
      mapTab[idx].used = true;
      Serial.print(F("Mapped "));
      Serial.print(idx);
      Serial.print(F(" → "));
      Serial.println(lbl);
    } else {
      Serial.println(F("(no label entered, skipped)"));
    }
  }
}
