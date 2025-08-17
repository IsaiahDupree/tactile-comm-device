/*
 * Tactile Communication Device - Arduino Code
 * 
 * This code manages a tactile communication device with letter buttons
 * that play corresponding audio files from an SD card using the DFPlayer Mini.
 * 
 * Hardware Components:
 * - Arduino Uno/Nano
 * - DFPlayer Mini MP3 module
 * - MicroSD card (formatted as FAT32)
 * - 30+ tactile buttons (letters + special buttons)
 * - Speaker (3W, 4-8 ohms)
 * - Rechargeable battery pack
 * - Button matrix or individual digital pins
 * 
 * Button Layout:
 * Top Row: YES, NO, WATER, AUX (Hello How are You)
 * Letters: A-Z (26 buttons)
 * Bottom: SPACE, PERIOD
 * Total: 32 buttons
 */

#include <SoftwareSerial.h>
#include <DFRobotDFPlayerMini.h>

// DFPlayer Serial Communication
SoftwareSerial mySoftwareSerial(10, 11); // RX, TX
DFRobotDFPlayerMini myDFPlayer;

// Button Configuration
const int NUM_BUTTONS = 32;
const int BUTTON_DEBOUNCE_DELAY = 50;
const int DOUBLE_PRESS_WINDOW = 500; // milliseconds

// Button pin assignments (adjust based on your wiring)
const int BUTTON_PINS[NUM_BUTTONS] = {
  2, 3, 4, 5, 6, 7, 8, 9,     // Row 1: YES, NO, WATER, AUX + A-D
  12, 13, A0, A1, A2, A3, A4, A5, // Row 2: E-L
  22, 23, 24, 25, 26, 27, 28, 29, // Row 3: M-T (if using Mega)
  30, 31, 32, 33, 34, 35, 36, 37  // Row 4: U-Z + SPACE + PERIOD
};

// Button states
bool buttonStates[NUM_BUTTONS];
bool lastButtonStates[NUM_BUTTONS];
unsigned long lastDebounceTime[NUM_BUTTONS];
unsigned long lastPressTime[NUM_BUTTONS];
int pressCount[NUM_BUTTONS];

// Audio file mapping - corresponds to folder structure on SD card
// Folder 01: Special buttons, Folder 02-27: Letters A-Z, Folder 28: Punctuation
const int FOLDER_SPECIAL = 1;
const int FOLDER_LETTERS_START = 2; // A=2, B=3, ..., Z=27
const int FOLDER_PUNCTUATION = 28;

// Button to folder/track mapping
struct ButtonMapping {
  int folder;
  int maxTracks;
  char label[20];
};

ButtonMapping buttonMap[NUM_BUTTONS] = {
  // Special buttons (folder 1)
  {1, 1, "YES"},     // Track 1
  {1, 1, "NO"},      // Track 2  
  {1, 1, "WATER"},   // Track 3
  {1, 1, "AUX"},     // Track 4
  
  // Letters A-Z (folders 2-27)
  {2, 4, "A"}, {3, 5, "B"}, {4, 3, "C"}, {5, 4, "D"}, {6, 0, "E"},
  {7, 2, "F"}, {8, 2, "G"}, {9, 2, "H"}, {10, 1, "I"}, {11, 0, "J"},
  {12, 4, "K"}, {13, 4, "L"}, {14, 3, "M"}, {15, 3, "N"}, {16, 1, "O"},
  {17, 2, "P"}, {18, 0, "Q"}, {19, 1, "R"}, {20, 3, "S"}, {21, 1, "T"},
  {22, 1, "U"}, {23, 0, "V"}, {24, 4, "W"}, {25, 0, "X"}, {26, 0, "Y"}, {27, 0, "Z"},
  
  // Punctuation (folder 28)
  {28, 1, "SPACE"},
  {28, 1, "PERIOD"}
};

void setup() {
  Serial.begin(9600);
  mySoftwareSerial.begin(9600);
  
  Serial.println("Initializing Tactile Communication Device...");
  
  // Initialize button pins
  for (int i = 0; i < NUM_BUTTONS; i++) {
    pinMode(BUTTON_PINS[i], INPUT_PULLUP);
    buttonStates[i] = HIGH;
    lastButtonStates[i] = HIGH;
    lastDebounceTime[i] = 0;
    lastPressTime[i] = 0;
    pressCount[i] = 0;
  }
  
  // Initialize DFPlayer
  if (!myDFPlayer.begin(mySoftwareSerial)) {
    Serial.println("Unable to begin DFPlayer!");
    Serial.println("Please check connections and SD card");
    while(true) {
      delay(1000);
    }
  }
  
  Serial.println("DFPlayer Mini online.");
  
  // Configure DFPlayer settings
  myDFPlayer.volume(25);  // Set volume (0-30)
  myDFPlayer.outputDevice(DFPLAYER_DEVICE_SD);
  
  delay(1000);
  
  // Play startup sound (optional)
  playStartupMessage();
  
  Serial.println("Tactile Communication Device Ready!");
  Serial.println("Press buttons to hear words and phrases.");
}

void loop() {
  // Check all buttons
  for (int i = 0; i < NUM_BUTTONS; i++) {
    checkButton(i);
  }
  
  // Handle double-press timeout
  handleDoublePressTimeout();
  
  delay(10); // Small delay for stability
}

void checkButton(int buttonIndex) {
  int reading = digitalRead(BUTTON_PINS[buttonIndex]);
  
  // Check if button state changed (with debouncing)
  if (reading != lastButtonStates[buttonIndex]) {
    lastDebounceTime[buttonIndex] = millis();
  }
  
  if ((millis() - lastDebounceTime[buttonIndex]) > BUTTON_DEBOUNCE_DELAY) {
    if (reading != buttonStates[buttonIndex]) {
      buttonStates[buttonIndex] = reading;
      
      // Button pressed (LOW due to INPUT_PULLUP)
      if (buttonStates[buttonIndex] == LOW) {
        handleButtonPress(buttonIndex);
      }
    }
  }
  
  lastButtonStates[buttonIndex] = reading;
}

void handleButtonPress(int buttonIndex) {
  unsigned long currentTime = millis();
  
  // Check if this is a potential double press
  if (currentTime - lastPressTime[buttonIndex] < DOUBLE_PRESS_WINDOW) {
    pressCount[buttonIndex]++;
  } else {
    pressCount[buttonIndex] = 1;
  }
  
  lastPressTime[buttonIndex] = currentTime;
  
  Serial.print("Button pressed: ");
  Serial.print(buttonMap[buttonIndex].label);
  Serial.print(" (Press #");
  Serial.print(pressCount[buttonIndex]);
  Serial.println(")");
  
  // Don't play immediately - wait for potential double press
  // Audio will be played in handleDoublePressTimeout()
}

void handleDoublePressTimeout() {
  unsigned long currentTime = millis();
  
  for (int i = 0; i < NUM_BUTTONS; i++) {
    if (pressCount[i] > 0 && 
        (currentTime - lastPressTime[i]) > DOUBLE_PRESS_WINDOW) {
      
      // Time to play the audio
      playButtonAudio(i, pressCount[i]);
      pressCount[i] = 0; // Reset press count
    }
  }
}

void playButtonAudio(int buttonIndex, int pressNumber) {
  ButtonMapping mapping = buttonMap[buttonIndex];
  
  // Skip if no audio files for this button
  if (mapping.maxTracks == 0) {
    Serial.print("No audio for button: ");
    Serial.println(mapping.label);
    return;
  }
  
  // Calculate track number (cycle through available tracks)
  int trackNumber = ((pressNumber - 1) % mapping.maxTracks) + 1;
  
  Serial.print("Playing: ");
  Serial.print(mapping.label);
  Serial.print(" - Folder ");
  Serial.print(mapping.folder);
  Serial.print(", Track ");
  Serial.println(trackNumber);
  
  // Play the audio file
  myDFPlayer.playFolder(mapping.folder, trackNumber);
  
  // Wait for playback to start
  delay(100);
}

void playStartupMessage() {
  Serial.println("Playing startup message...");
  // You can create a startup audio file in folder 99, track 1
  // myDFPlayer.playFolder(99, 1);
  delay(2000);
}

// Utility functions for debugging
void printButtonStatus() {
  Serial.println("=== Button Status ===");
  for (int i = 0; i < NUM_BUTTONS; i++) {
    Serial.print(buttonMap[i].label);
    Serial.print(": ");
    Serial.print(buttonStates[i] == LOW ? "PRESSED" : "RELEASED");
    Serial.print(" (Pin ");
    Serial.print(BUTTON_PINS[i]);
    Serial.println(")");
  }
  Serial.println("====================");
}

void testAllButtons() {
  Serial.println("Testing all buttons...");
  for (int i = 0; i < NUM_BUTTONS; i++) {
    if (buttonMap[i].maxTracks > 0) {
      Serial.print("Testing: ");
      Serial.println(buttonMap[i].label);
      playButtonAudio(i, 1);
      delay(3000); // Wait between tests
    }
  }
  Serial.println("Button test complete.");
}
