/*************************************************** 
  This is an example for the Adafruit VS1053 Codec Breakout

  Designed specifically to work with the Adafruit VS1053 Codec Breakout 
  ----> https://www.adafruit.com/products/1381

  Adafruit invests time and resources providing this open source code, 
  please support Adafruit and open-source hardware by purchasing 
  products from Adafruit!

  Written by Limor Fried/Ladyada for Adafruit Industries.  
  BSD license, all text above must be included in any redistribution
 ****************************************************/

// include SPI, MP3 and SD libraries
#include <SPI.h>
#include "Adafruit_VS1053.h"
#include <SD.h>

// define the pins used
//#define CLK 13       // SPI Clock, shared with SD card
//#define MISO 12      // Input data, from VS1053/SD card
//#define MOSI 11      // Output data, to VS1053/SD card
// Connect CLK, MISO and MOSI to hardware SPI pins. 
// See http://arduino.cc/en/Reference/SPI "Connections"

// --- SHIELD pin‑map (used on product 1788) ---------------------
#define SHIELD_RESET  -1   // reset is tied high on the shield
#define SHIELD_CS      7   // VS1053 xCS
#define SHIELD_DCS     6   // VS1053 xDCS   <-- was D8 in your code
#define CARDCS         4   // micro‑SD CS (fixed trace)
#define DREQ           3   // VS1053 DREQ (INT1 on Uno)

// instantiate **shield** object – NOT breakout object
Adafruit_VS1053_FilePlayer musicPlayer(
        SHIELD_RESET, SHIELD_CS, SHIELD_DCS, DREQ, CARDCS);


void setup() {
  Serial.begin(9600);
  while (!Serial) { ; }          // wait for Serial Monitor (Uno R4 USB)
  delay(2000);                   // give the USB port a moment



  // ── NEW: make sure the SD card is deselected so it can't
  // ── drive MISO while we probe the VS1053
  pinMode(CARDCS, OUTPUT);
  digitalWrite(CARDCS, HIGH);    // SD chip‑select held HIGH
  // ────────────────────────────────────────────────────────

  Serial.println("Adafruit VS1053 Simple Test");

  // ----- VS1053 init -----
  if (!musicPlayer.begin()) {
    Serial.println(F("Couldn't find VS1053, do you have the right pins defined?"));
    while (1);                   // halt here if codec not found
  }
  Serial.println(F("VS1053 found"));

  // ----- SD‑card init (safe to enable now) -----
  if (!SD.begin(CARDCS)) {
    Serial.println(F("SD failed, or not present"));
    while (1);                   // halt here if card missing
  }
  Serial.println(F("SD card initialized."));

  // List files on card
  Serial.println(F("Files on SD card:"));
  printDirectory(SD.open("/"), 0);

  // Set volume (0 = loudest, 100 = mute)
  musicPlayer.setVolume(0, 0);
  musicPlayer.sineTest(0x44, 500);  // ½-second 1 kHz tone

  Serial.println(F("Volume set."));

  // Use DREQ interrupt for background playback
  musicPlayer.useInterrupt(VS1053_FILEPLAYER_PIN_INT);
  Serial.println(F("VS1053 interrupt enabled."));

  // Play first track to completion
  Serial.println(F("Playing track001.mp3"));
  musicPlayer.playFullFile("/track001.mp3");

  // Start second track in background
  Serial.println(F("Starting track002.mp3 in background"));
  musicPlayer.startPlayingFile("/track002.mp3");
}


void loop() {
  musicPlayer.setVolume(0, 0);
  musicPlayer.sineTest(0x44, 10000000);  // ½-second 1 kHz tone
  // File is playing in the background
  if (musicPlayer.stopped()) {
    Serial.println("Done playing music");
    while (1) {
      delay(10);  // we're done! do nothing...
    }
  }
  if (Serial.available()) {
    char c = Serial.read();
    
    // if we get an 's' on the serial console, stop!
    if (c == 's') {
      musicPlayer.stopPlaying();
    }
    
    // if we get an 'p' on the serial console, pause/unpause!
    if (c == 'p') {
      if (! musicPlayer.paused()) {
        Serial.println("Paused");
        musicPlayer.pausePlaying(true);
      } else { 
        Serial.println("Resumed");
        musicPlayer.pausePlaying(false);
      }
    }
  }

  delay(100);
}


/// File listing helper
void printDirectory(File dir, int numTabs) {
   while(true) {
     
     File entry =  dir.openNextFile();
     if (! entry) {
       // no more files
       //Serial.println("**nomorefiles**");
       break;
     }
     for (uint8_t i=0; i<numTabs; i++) {
       Serial.print('\t');
     }
     Serial.print(entry.name());
     if (entry.isDirectory()) {
       Serial.println("/");
       printDirectory(entry, numTabs+1);
     } else {
       // files have sizes, directories do not
       Serial.print("\t\t");
       Serial.println(entry.size(), DEC);
     }
     entry.close();
   }
}
