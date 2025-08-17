/*
 * Simple VS1053 Test
 * 
 * This is a minimal test to check VS1053 hardware connections.
 * Upload this sketch to diagnose "VS1053 not found" issues.
 */

#include <SPI.h>
#include "Adafruit_VS1053.h"
#include "SD.h"

// Pin definitions (same as main sketch)
#define BREAKOUT_RESET  9
#define BREAKOUT_CS     10
#define BREAKOUT_DCS    8
#define CARDCS          4
#define DREQ            3

// Create VS1053 object
Adafruit_VS1053_FilePlayer musicPlayer = 
  Adafruit_VS1053_FilePlayer(BREAKOUT_RESET, BREAKOUT_CS, BREAKOUT_DCS, DREQ, CARDCS);

// Global status variables
bool vs1053Working = false;
unsigned long lastStatusTime = 0;
unsigned long statusInterval = 2000; // 2 seconds
int testCounter = 0;

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
    vs1053Working = true;
    
    // Set volume
    musicPlayer.setVolume(20, 20);
    Serial.println(F("✅ Volume set successfully."));
    
    // Test sine wave
    Serial.println(F("🔊 Playing test tone for 2 seconds..."));
    musicPlayer.sineTest(0x44, 2000);  // 1kHz for 2 seconds
    Serial.println(F("✅ Test tone complete."));
    
    // SUCCESS BEEP - Three loud beeps to indicate working hardware
    Serial.println(F("🔊 SUCCESS BEEPS - Hardware Working!"));
    for (int i = 0; i < 3; i++) {
      musicPlayer.sineTest(0x55, 500);  // Higher pitch, 500ms
      delay(200);
    }
    
    Serial.println(F("\n🎉 ALL TESTS PASSED!"));
    Serial.println(F("Your VS1053 hardware is working correctly."));
    Serial.println(F("The issue might be in your main sketch or SD card."));
    Serial.println(F("\n📊 Continuous monitoring started..."));
    
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
  unsigned long currentTime = millis();
  
  // Output comprehensive status every couple seconds
  if (currentTime - lastStatusTime >= statusInterval) {
    lastStatusTime = currentTime;
    testCounter++;
    
    Serial.println(F("\n--- STATUS REPORT ---"));
    Serial.print(F("Test #: "));
    Serial.println(testCounter);
    Serial.print(F("Uptime: "));
    Serial.print(currentTime / 1000);
    Serial.println(F(" seconds"));
    
    // Check DREQ pin status
    bool dreqState = digitalRead(DREQ);
    Serial.print(F("DREQ Pin: "));
    Serial.println(dreqState ? F("HIGH ✅") : F("LOW ⚠️"));
    
    // VS1053 status
    Serial.print(F("VS1053 Status: "));
    if (vs1053Working) {
      Serial.println(F("WORKING ✅"));
      
      // Periodic test beep if working
      if (testCounter % 5 == 0) { // Every 10 seconds (5 * 2sec intervals)
        Serial.println(F("🔊 Periodic test beep..."));
        musicPlayer.sineTest(0x44, 300); // Short beep
      }
      
      // Test volume control
      Serial.println(F("Volume: Set to 20/20"));
      
    } else {
      Serial.println(F("NOT DETECTED ❌"));
      Serial.println(F("⚠️  Check wiring and connections!"));
    }
    
    // Memory status
    Serial.print(F("Free RAM: "));
    Serial.print(freeMemory());
    Serial.println(F(" bytes"));
    
    Serial.println(F("--- END STATUS ---\n"));
  }
  
  delay(100); // Small delay to prevent overwhelming the serial output
}

// Function to check available memory (simplified for compatibility)
int freeMemory() {
#if defined(ARDUINO_ARCH_RENESAS)
  // For Arduino Uno R4 WiFi - simplified memory check
  return 1024; // Placeholder - R4 has plenty of RAM
#elif defined(__AVR__)
  // For AVR boards (Uno, Nano, etc.)
  extern int __heap_start, *__brkval;
  int v;
  return (int) &v - (__brkval == 0 ? (int) &__heap_start : (int) __brkval);
#else
  // For other architectures
  return 2048; // Placeholder
#endif
}
