/*
 * Simple VS1053 Test
 * 
 * This is a minimal test to check VS1053 hardware connections.
 * Upload this sketch to diagnose "VS1053 not found" issues.
 */

#include <SPI.h>
#include "Adafruit_VS1053.h"

// Pin definitions (same as main sketch)
#define BREAKOUT_RESET  9
#define BREAKOUT_CS     10
#define BREAKOUT_DCS    8
#define CARDCS          4
#define DREQ            3

// Create VS1053 object
Adafruit_VS1053_FilePlayer musicPlayer = 
  Adafruit_VS1053_FilePlayer(BREAKOUT_RESET, BREAKOUT_CS, BREAKOUT_DCS, DREQ, CARDCS);

void setup() {
  Serial.begin(115200);
  while (!Serial) delay(10);
  
  Serial.println(F("\n=== SIMPLE VS1053 TEST ==="));
  Serial.println(F("Testing hardware connections..."));
  
  // Check DREQ pin before initialization
  Serial.print(F("DREQ pin state: "));
  Serial.println(digitalRead(DREQ) ? F("HIGH") : F("LOW"));
  
  // Try to initialize VS1053
  Serial.println(F("Initializing VS1053..."));
  
  if (musicPlayer.begin()) {
    Serial.println(F("✅ VS1053 FOUND! Hardware is working."));
    
    // Set volume
    musicPlayer.setVolume(20, 20);
    Serial.println(F("✅ Volume set successfully."));
    
    // Test sine wave
    Serial.println(F("🔊 Playing test tone for 2 seconds..."));
    musicPlayer.sineTest(0x44, 2000);  // 1kHz for 2 seconds
    Serial.println(F("✅ Test tone complete."));
    
    Serial.println(F("\n🎉 ALL TESTS PASSED!"));
    Serial.println(F("Your VS1053 hardware is working correctly."));
    Serial.println(F("The issue might be in your main sketch or SD card."));
    
  } else {
    Serial.println(F("❌ VS1053 NOT FOUND!"));
    Serial.println(F("\n🔧 TROUBLESHOOTING STEPS:"));
    Serial.println(F("1. Check power connections:"));
    Serial.println(F("   VS1053 VCC → Arduino 5V"));
    Serial.println(F("   VS1053 GND → Arduino GND"));
    Serial.println(F("2. Check SPI connections:"));
    Serial.println(F("   VS1053 MOSI → Arduino Pin 11"));
    Serial.println(F("   VS1053 MISO → Arduino Pin 12"));
    Serial.println(F("   VS1053 SCK → Arduino Pin 13"));
    Serial.println(F("3. Check control pins:"));
    Serial.println(F("   VS1053 CS → Arduino Pin 10"));
    Serial.println(F("   VS1053 DCS → Arduino Pin 8"));
    Serial.println(F("   VS1053 DREQ → Arduino Pin 3"));
    Serial.println(F("   VS1053 RST → Arduino Pin 9"));
    Serial.println(F("4. Verify jumper wires are secure"));
    Serial.println(F("5. Check for short circuits"));
    Serial.println(F("6. Try a different VS1053 module if available"));
  }
}

void loop() {
  // Monitor DREQ pin
  static unsigned long lastCheck = 0;
  if (millis() - lastCheck > 3000) {
    lastCheck = millis();
    Serial.print(F("DREQ: "));
    Serial.println(digitalRead(DREQ) ? F("HIGH") : F("LOW"));
  }
  delay(100);
}
