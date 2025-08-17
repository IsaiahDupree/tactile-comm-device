//
// TACTILE COMMUNICATION DEVICE - EXTENSIONS
// Button Simulation and SD Card File Transfer
//

// ===== BUTTON SIMULATION SYSTEM =====

// Queue for simulated presses so they pass through handlePress()/handleMultiPress()
#define SIM_QUEUE_SIZE 16
struct SimEvent { 
  uint16_t idx;         // Input index to simulate
  unsigned long at;     // Time when to simulate the press
};
SimEvent simQ[SIM_QUEUE_SIZE];
uint8_t simHead = 0;
uint8_t simTail = 0;

/**
 * Enqueues a simulated button press to be processed through the normal button handling flow
 * 
 * @param idx The input index to simulate (button index)
 * @param count Number of presses to simulate
 * @param gap Time in ms between consecutive presses
 */
void enqueueSimPress(uint16_t idx, uint8_t count, uint16_t gap) {
  unsigned long t = millis();
  Serial.print(F("[SIM] Queueing "));
  Serial.print(count);
  Serial.print(F(" press(es) for idx="));
  Serial.println(idx);
  
  for (uint8_t i = 0; i < count; i++) {
    simQ[simTail].idx = idx;
    simQ[simTail].at = t + (i * gap);
    simTail = (simTail + 1) % SIM_QUEUE_SIZE;
    
    // Check if queue is full
    if (simHead == simTail) {
      Serial.println(F("[SIM] Queue full, discarding older events"));
      simHead = (simHead + 1) % SIM_QUEUE_SIZE; // Discard oldest
    }
  }
}

/**
 * Processes the simulation queue, should be called in each loop()
 */
void pumpSimQueue() {
  unsigned long now = millis();
  while (simHead != simTail && simQ[simHead].at <= now) {
    uint16_t idx = simQ[simHead].idx;
    Serial.print(F("[SIM] Triggering press for idx="));
    Serial.println(idx);
    handlePress(idx); // Use the real button handling path
    simHead = (simHead + 1) % SIM_QUEUE_SIZE;
  }
}

/**
 * Finds the index for a logical key name
 * 
 * @param key The key name (e.g., "A", "PERIOD", "WATER")
 * @return The button index or -1 if not found
 */
int16_t idxForKey(const String& key) {
  // Look through hardware mappings to find the first matching key
  for (uint16_t i = 0; i < TOTAL_BUTTONS; i++) {
    if (mapTab[i].valid && strcasecmp(mapTab[i].label, key.c_str()) == 0) {
      return i;
    }
  }
  return -1;
}

/**
 * Finds the index for a physical input ID
 * 
 * @param id The input ID (e.g., "pcf2:10", "gpio:8")
 * @return The button index or -1 if not found
 */
int16_t idxForInputId(const String& id) {
  String prefix;
  int pin;
  
  // Parse pcfN:pin format
  if (id.startsWith("pcf")) {
    int colonPos = id.indexOf(":");
    if (colonPos > 0) {
      int pcfIndex = id.substring(3, colonPos).toInt();
      pin = id.substring(colonPos + 1).toInt();
      
      // Look for matching PCF input
      if (pcfIndex >= 0 && pcfIndex < NUM_PCF && pin >= 0 && pin < 16) {
        return pcfIndex * 16 + pin;
      }
    }
  }
  // Parse gpio:pin format
  else if (id.startsWith("gpio:")) {
    pin = id.substring(5).toInt();
    
    // Check if this is a valid GPIO pin in our extras list
    for (uint8_t i = 0; i < EXTRA_COUNT; i++) {
      if (extraPins[i] == pin) {
        return TOTAL_EXPANDER_PINS + i;
      }
    }
  }
  
  return -1;
}

// ===== SAFE FILE SYSTEM OPERATIONS =====

// Atomic file transfer session (staging to actual destination)
bool fsSessionActive = false;
File fsCurrentFile;
String fsCurrentPath;
uint32_t fsCurrentCRC32 = 0;
uint32_t fsCurrentSize = 0;
uint32_t fsBytesReceived = 0;
const String FS_STAGING_DIR = "/_staging";
bool maintenanceMode = false;

/**
 * Initializes the file system session system
 */
void initFSSession() {
  // Create staging directory if it doesn't exist
  if (!SD.exists(FS_STAGING_DIR)) {
    SD.mkdir(FS_STAGING_DIR);
  }
}

/**
 * Calculate CRC32 checksum for a data buffer
 */
uint32_t calculate_crc32(const uint8_t* data, size_t length, uint32_t crc = 0) {
  crc = ~crc;
  for (size_t i = 0; i < length; i++) {
    crc ^= data[i];
    for (uint8_t j = 0; j < 8; j++) {
      crc = (crc >> 1) ^ (0xEDB88320 & -(crc & 1));
    }
  }
  return ~crc;
}

/**
 * Starts a file system session
 * 
 * @param count Number of files to transfer
 * @param maintenanceMode Whether to enter maintenance mode (pause audio, ignore buttons)
 */
void cmd_FS_BEGIN(uint16_t count, bool maintenance) {
  if (fsSessionActive) {
    Serial.println(F("ERR SESSION_ACTIVE"));
    return;
  }
  
  fsSessionActive = true;
  maintenanceMode = maintenance;
  
  // Clean up staging directory
  if (SD.exists(FS_STAGING_DIR)) {
    File dir = SD.open(FS_STAGING_DIR);
    File entry;
    while (entry = dir.openNextFile()) {
      String path = String(FS_STAGING_DIR) + "/" + entry.name();
      entry.close();
      SD.remove(path);
    }
    dir.close();
  } else {
    SD.mkdir(FS_STAGING_DIR);
  }
  
  Serial.println(F("OK"));
}

/**
 * Prepares to receive file data
 * 
 * @param path Destination path for the file
 * @param size Expected size in bytes
 * @param crc32 Expected CRC32 checksum
 */
void cmd_FS_PUT(const String& path, uint32_t size, uint32_t crc32) {
  if (!fsSessionActive) {
    Serial.println(F("ERR NO_SESSION"));
    return;
  }
  
  if (fsCurrentFile) {
    fsCurrentFile.close();
  }
  
  fsCurrentPath = path;
  fsCurrentSize = size;
  fsCurrentCRC32 = crc32;
  fsBytesReceived = 0;
  
  // Create staging path
  String stagingPath = FS_STAGING_DIR + "/" + String(random(1000000)); // Use random filename
  
  // Open file for writing
  fsCurrentFile = SD.open(stagingPath, FILE_WRITE);
  if (!fsCurrentFile) {
    Serial.println(F("ERR FILE_OPEN"));
    return;
  }
  
  Serial.println(F("OK"));
}

/**
 * Processes received file data chunk
 * 
 * @param length Length of the data chunk
 * @param data The data buffer
 */
void cmd_FS_DATA(uint16_t length, const uint8_t* data) {
  if (!fsSessionActive || !fsCurrentFile) {
    Serial.println(F("ERR NO_FILE"));
    return;
  }
  
  // Write data to file
  size_t written = fsCurrentFile.write(data, length);
  if (written != length) {
    Serial.println(F("ERR WRITE_FAILED"));
    fsCurrentFile.close();
    return;
  }
  
  fsBytesReceived += length;
  Serial.println(F("OK"));
}

/**
 * Finishes file transfer and verifies checksums
 */
void cmd_FS_DONE() {
  if (!fsSessionActive || !fsCurrentFile) {
    Serial.println(F("ERR NO_FILE"));
    return;
  }
  
  // Close the file
  fsCurrentFile.close();
  
  // Check file size
  if (fsBytesReceived != fsCurrentSize) {
    Serial.print(F("ERR SIZE_MISMATCH "));
    Serial.print(fsBytesReceived);
    Serial.print(F("/"));
    Serial.println(fsCurrentSize);
    return;
  }
  
  // Calculate CRC32 of the file
  File file = SD.open(FS_STAGING_DIR + "/" + fsCurrentFile.name(), FILE_READ);
  if (!file) {
    Serial.println(F("ERR VERIFICATION"));
    return;
  }
  
  uint32_t calculatedCRC = 0;
  uint8_t buffer[64];
  
  while (file.available()) {
    size_t bytesRead = file.read(buffer, sizeof(buffer));
    calculatedCRC = calculate_crc32(buffer, bytesRead, calculatedCRC);
  }
  
  file.close();
  
  // Verify CRC32
  if (calculatedCRC != fsCurrentCRC32) {
    Serial.print(F("ERR CRC32_MISMATCH "));
    Serial.print(calculatedCRC, HEX);
    Serial.print(F(" != "));
    Serial.println(fsCurrentCRC32, HEX);
    return;
  }
  
  Serial.println(F("OK"));
}

/**
 * Commits all staged files to their actual destinations
 */
void cmd_FS_COMMIT() {
  if (!fsSessionActive) {
    Serial.println(F("ERR NO_SESSION"));
    return;
  }
  
  // Move all files from staging to their destinations
  File dir = SD.open(FS_STAGING_DIR);
  File entry;
  bool success = true;
  
  while (entry = dir.openNextFile()) {
    String sourcePath = String(FS_STAGING_DIR) + "/" + entry.name();
    String destPath = fsCurrentPath; // Use the path from FS_PUT
    entry.close();
    
    // Create destination directory if needed
    int lastSlash = destPath.lastIndexOf('/');
    if (lastSlash > 0) {
      String dirPath = destPath.substring(0, lastSlash);
      if (!SD.exists(dirPath)) {
        SD.mkdir(dirPath);
      }
    }
    
    // Remove destination file if it exists
    if (SD.exists(destPath)) {
      SD.remove(destPath);
    }
    
    // Rename staging file to destination
    if (!SD.rename(sourcePath, destPath)) {
      Serial.print(F("ERR COMMIT_FAILED "));
      Serial.println(destPath);
      success = false;
      break;
    }
  }
  
  dir.close();
  fsSessionActive = false;
  maintenanceMode = false;
  
  if (success) {
    Serial.println(F("OK"));
  }
}

/**
 * Aborts the current file transfer session
 */
void cmd_FS_ABORT() {
  if (fsCurrentFile) {
    fsCurrentFile.close();
  }
  
  fsSessionActive = false;
  maintenanceMode = false;
  Serial.println(F("OK"));
}

/**
 * Reloads SD card configuration
 */
void cmd_CFG_RELOAD() {
  // Stop any current playback
  if (musicPlayer.playingMusic) {
    musicPlayer.stopPlaying();
  }
  
  // Reset configuration and reload
  sdConfigLoaded = false;
  
  // Re-initialize SD config (equivalent to calling initSDConfig())
  loadModeCfg();
  
  // Reload hardware mapping
  initializeHardwareMapping();
  
  Serial.println(F("OK"));
}

/**
 * Plays an audio file associated with a key
 * 
 * @param key The key name
 * @param bank Bank ID (0=auto based on priority, 1=human, 2=generated)
 */
void cmd_PLAY_KEY(const String& key, uint8_t bank) {
  // Find the button index for this key
  int16_t idx = idxForKey(key);
  if (idx < 0) {
    Serial.print(F("ERR UNKNOWN_KEY "));
    Serial.println(key);
    return;
  }
  
  // Handle as if it was a regular button press, but force the bank if specified
  playButtonAudioWithCount(mapTab[idx].label, 1);
  Serial.println(F("OK"));
}

/**
 * Stops the currently playing audio
 */
void cmd_STOP() {
  if (musicPlayer.playingMusic) {
    musicPlayer.stopPlaying();
    Serial.println(F("OK"));
  } else {
    Serial.println(F("ERR NOT_PLAYING"));
  }
}

/**
 * Helper to parse an integer from a string with specified token index
 * 
 * @param s The string to parse
 * @param idx Token index (0-based)
 * @param defaultVal Default value if parsing fails
 * @return The parsed integer or defaultVal if parsing fails
 */
int parseIntOr(const String& s, int idx, int defaultVal) {
  int startIdx = 0;
  int found = 0;
  
  // Find the nth space-delimited token
  while (found < idx) {
    startIdx = s.indexOf(' ', startIdx);
    if (startIdx < 0) return defaultVal;
    startIdx++; // Skip the space
    found++;
  }
  
  // Find the end of the token
  int endIdx = s.indexOf(' ', startIdx);
  if (endIdx < 0) endIdx = s.length();
  
  // Extract and parse the token
  String token = s.substring(startIdx, endIdx);
  if (token.length() == 0) return defaultVal;
  
  return token.toInt();
}

/**
 * Process binary data after FS_DATA command
 * 
 * @param length Length of data to read
 */
void processDataChunk(uint16_t length) {
  uint8_t buffer[64]; // Adjust size based on your Arduino's memory constraints
  uint16_t remaining = length;
  uint16_t position = 0;
  
  // Read requested bytes in chunks
  while (remaining > 0) {
    uint16_t chunkSize = min(sizeof(buffer), remaining);
    uint16_t bytesRead = 0;
    
    // Read chunk with timeout
    unsigned long startTime = millis();
    while (bytesRead < chunkSize && (millis() - startTime) < 5000) {
      if (Serial.available()) {
        buffer[bytesRead++] = Serial.read();
      }
    }
    
    // Process chunk
    if (bytesRead > 0) {
      cmd_FS_DATA(bytesRead, buffer);
      remaining -= bytesRead;
      position += bytesRead;
    } else {
      // Timeout occurred
      Serial.println(F("ERR TIMEOUT"));
      return;
    }
  }
}

/**
 * Handles extended serial commands from the desktop app
 * 
 * @param line Command line to parse
 * @return True if the command was handled
 */
bool handleExtendedSerialCommand(const String& line) {
  if (line.startsWith("SIM_KEY ")) {
    // SIM_KEY <KEY> [count=1] [gap_ms=100]
    String key = line.substring(8);
    key.trim();
    
    // Extract parameters
    int spaceIdx = key.indexOf(' ');
    if (spaceIdx > 0) {
      key = key.substring(0, spaceIdx);
    }
    
    int16_t idx = idxForKey(key);
    if (idx < 0) {
      Serial.print(F("ERR UNKNOWN_KEY "));
      Serial.println(key);
      return true;
    }
    
    uint8_t count = parseIntOr(line, 2, 1); // Default count: 1
    uint16_t gap = parseIntOr(line, 3, 100); // Default gap: 100ms
    
    enqueueSimPress(idx, count, gap);
    Serial.println(F("OK"));
    return true;
  }
  else if (line.startsWith("SIM_INPUT ")) {
    // SIM_INPUT <pcfN:pin> [count=1] [gap_ms=100]
    String id = line.substring(10);
    id.trim();
    
    // Extract parameters
    int spaceIdx = id.indexOf(' ');
    if (spaceIdx > 0) {
      id = id.substring(0, spaceIdx);
    }
    
    int16_t idx = idxForInputId(id);
    if (idx < 0) {
      Serial.print(F("ERR UNKNOWN_INPUT "));
      Serial.println(id);
      return true;
    }
    
    uint8_t count = parseIntOr(line, 2, 1); // Default count: 1
    uint16_t gap = parseIntOr(line, 3, 100); // Default gap: 100ms
    
    enqueueSimPress(idx, count, gap);
    Serial.println(F("OK"));
    return true;
  }
  else if (line.startsWith("PLAY_KEY ")) {
    // PLAY_KEY <KEY> [bank=0]
    String key = line.substring(9);
    key.trim();
    
    // Extract parameters
    int spaceIdx = key.indexOf(' ');
    if (spaceIdx > 0) {
      key = key.substring(0, spaceIdx);
    }
    
    uint8_t bank = parseIntOr(line, 2, 0); // Default bank: 0 (auto)
    cmd_PLAY_KEY(key, bank);
    return true;
  }
  else if (line.startsWith("STOP")) {
    cmd_STOP();
    return true;
  }
  else if (line.startsWith("FS_BEGIN")) {
    // FS_BEGIN <count> [maintenance_mode=0]
    uint16_t count = parseIntOr(line, 1, 0);
    bool maintenance = parseIntOr(line, 2, 0) > 0;
    cmd_FS_BEGIN(count, maintenance);
    return true;
  }
  else if (line.startsWith("FS_PUT ")) {
    // FS_PUT <path> <size> <crc32_hex>
    int firstSpace = line.indexOf(' ');
    int secondSpace = line.indexOf(' ', firstSpace + 1);
    int thirdSpace = line.indexOf(' ', secondSpace + 1);
    
    if (secondSpace < 0 || thirdSpace < 0) {
      Serial.println(F("ERR SYNTAX"));
      return true;
    }
    
    String path = line.substring(firstSpace + 1, secondSpace);
    String sizeStr = line.substring(secondSpace + 1, thirdSpace);
    String crcStr = line.substring(thirdSpace + 1);
    
    uint32_t size = sizeStr.toInt();
    uint32_t crc32 = strtoul(crcStr.c_str(), NULL, 16);
    
    cmd_FS_PUT(path, size, crc32);
    return true;
  }
  else if (line.startsWith("FS_DONE")) {
    cmd_FS_DONE();
    return true;
  }
  else if (line.startsWith("FS_COMMIT")) {
    cmd_FS_COMMIT();
    return true;
  }
  else if (line.startsWith("FS_ABORT")) {
    cmd_FS_ABORT();
    return true;
  }
  else if (line.startsWith("CFG_RELOAD")) {
    cmd_CFG_RELOAD();
    return true;
  }
  
  return false;
}
