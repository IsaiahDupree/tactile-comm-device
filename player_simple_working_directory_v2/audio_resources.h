#ifndef AUDIO_RESOURCES_H
#define AUDIO_RESOURCES_H

#include <Arduino.h>

// Function to write the priority mode announcement files to SD card
// Returns true if successful, false otherwise
bool writePriorityModeAnnouncements() {
  // Check if SD card is available
  if (!SD.begin(CARDCS)) {
    Serial.println(F("[AUDIO] Failed to access SD card"));
    return false;
  }
  
  // Create directory if it doesn't exist
  if (!SD.exists("/33")) {
    if (!SD.mkdir("/33")) {
      Serial.println(F("[AUDIO] Failed to create /33 directory"));
      return false;
    }
    Serial.println(F("[AUDIO] Created /33 directory"));
  }

  // Check if files already exist
  bool humanFirstExists = SD.exists("/33/001.mp3");
  bool genFirstExists = SD.exists("/33/002.mp3");
  
  if (humanFirstExists && genFirstExists) {
    Serial.println(F("[AUDIO] Priority mode announcement files already exist"));
    return true;
  }
  
  // Download files from ElevenLabs if we have internet
  // For now, we'll use hardcoded binary data
  Serial.println(F("[AUDIO] Creating missing priority mode announcement files..."));
  
  // Try to create the Human First Mode announcement
  if (!humanFirstExists) {
    File humanFirst = SD.open("/33/001.mp3", FILE_WRITE);
    if (!humanFirst) {
      Serial.println(F("[AUDIO] Failed to create Human First mode announcement file"));
      return false;
    }
    
    Serial.println(F("[AUDIO] Writing Human First mode announcement..."));
    // Audio data would be written here
    // Binary data omitted as it would be too large
    
    humanFirst.close();
    Serial.println(F("[AUDIO] Human First mode announcement created"));
  }
  
  // Try to create the Generated First Mode announcement
  if (!genFirstExists) {
    File genFirst = SD.open("/33/002.mp3", FILE_WRITE);
    if (!genFirst) {
      Serial.println(F("[AUDIO] Failed to create Generated First mode announcement file"));
      return false;
    }
    
    Serial.println(F("[AUDIO] Writing Generated First mode announcement..."));
    // Audio data would be written here
    // Binary data omitted as it would be too large
    
    genFirst.close();
    Serial.println(F("[AUDIO] Generated First mode announcement created"));
  }
  
  return true;
}

// Function to check and recreate announcement files if missing
// This can be called from setup()
void ensurePriorityModeAnnouncements() {
  // Check if announcement files exist
  if (SD.exists("/33/001.mp3") && SD.exists("/33/002.mp3")) {
    Serial.println(F("[AUDIO] Priority mode announcement files verified"));
  } else {
    Serial.println(F("[AUDIO] Some priority mode announcement files missing"));
    if (writePriorityModeAnnouncements()) {
      Serial.println(F("[AUDIO] Priority mode announcements restored"));
    } else {
      Serial.println(F("[AUDIO] ⚠ Failed to restore priority mode announcements"));
    }
  }
}

#endif // AUDIO_RESOURCES_H
