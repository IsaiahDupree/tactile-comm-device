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
  for (uint16_t i = 0; i < MAX_INPUTS; i++) {
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
    
    // Look for matching GPIO input
    if (pin >= 0 && pin < NUM_GPIO) {
      return (NUM_PCF * 16) + pin; // GPIO pins come after PCF pins
    }
  }
  
  return -1;
}

/**
 * Helper function to get a token from a space-delimited string
 * 
 * @param str The input string
 * @param tokenIndex The zero-based index of the token to retrieve
 * @return The token string or empty string if not found
 */
String getToken(const String& str, uint8_t tokenIndex) {
  int startPos = 0;
  int spacePos = -1;
  
  for (uint8_t i = 0; i <= tokenIndex; i++) {
    startPos = spacePos + 1;
    spacePos = str.indexOf(' ', startPos);
    
    if (spacePos == -1) {
      // Last token or not enough tokens
      if (i == tokenIndex) {
        return str.substring(startPos);
      } else {
        return "";
      }
    }
  }
  
  return str.substring(startPos, spacePos);
}

/**
 * Parse an integer with default value if parsing fails
 * 
 * @param str The string to parse from
 * @param tokenIndex The token index to parse
 * @param defaultVal Default value if parsing fails
 * @return The parsed integer or default value
 */
int parseIntOr(const String& str, uint8_t tokenIndex, int defaultVal) {
  String token = getToken(str, tokenIndex);
  if (token.length() > 0) {
    return token.toInt();
  }
  return defaultVal;
}

// ===== SD CARD FILE TRANSFER SYSTEM =====

bool inUpdate = false;
File currentFile;
uint32_t crcAccumulator = 0;
uint32_t bytesReceived = 0;
uint32_t expectedSize = 0;
uint32_t expectedCrc = 0;
uint8_t expectedFiles = 0;
uint8_t filesProcessed = 0;
uint32_t totalBytes = 0;
bool inMaintenanceMode = false;

/**
 * Checks if a file path is allowed for file transfer operations
 * 
 * @param path The file path to check
 * @return true if path is allowed, false otherwise
 */
bool pathAllowed(const String& path) {
  // Only allow writes under specific directories
  if (path.startsWith("/audio/human/") || 
      path.startsWith("/audio/generated/") || 
      path.startsWith("/mappings/playlists/") || 
      path.startsWith("/config/") || 
      path.startsWith("/state/")) {
    return true;
  }
  return false;
}

/**
 * Creates all necessary parent directories for a file path
 * 
 * @param path The full file path
 * @return true if successful, false otherwise
 */
bool createDirForFile(const String& path) {
  int lastSlash = path.lastIndexOf('/');
  if (lastSlash <= 0) return true; // No directories to create
  
  String dirPath = path.substring(0, lastSlash);
  
  // Start from root and create each level
  String currentPath = "";
  for (int i = 0; i < dirPath.length(); i++) {
    char c = dirPath.charAt(i);
    currentPath += c;
    
    if (c == '/' && i > 0) {
      if (!SD.exists(currentPath.c_str())) {
        if (!SD.mkdir(currentPath.c_str())) {
          Serial.print(F("ERR DIR "));
          Serial.println(currentPath);
          return false;
        }
      }
    }
  }
  
  return true;
}

/**
 * Initiates a file transfer session
 * 
 * @param numFiles Number of files to be transferred
 * @param totalFileBytes Total bytes to be transferred
 * @param manifestCrc Expected CRC32 of the manifest (optional)
 */
void cmd_FS_BEGIN(uint8_t numFiles, uint32_t totalFileBytes, uint32_t manifestCrc) {
  if (inUpdate) {
    Serial.println(F("ERR BUSY"));
    return;
  }
  
  // Enter maintenance mode
  inMaintenanceMode = true;
  if (musicPlayer.playingMusic) {
    musicPlayer.stopPlaying();
    Serial.println(F("[FS] Stopped playback for file transfer"));
  }
  
  // Create staging directory if it doesn't exist
  if (!SD.exists("/_staging")) {
    if (!SD.mkdir("/_staging")) {
      Serial.println(F("ERR STAGING"));
      inMaintenanceMode = false;
      return;
    }
  }
  
  // Initialize transfer session
  inUpdate = true;
  expectedFiles = numFiles;
  filesProcessed = 0;
  totalBytes = totalFileBytes;
  
  Serial.println(F("OK"));
}

/**
 * Prepares to receive a file
 * 
 * @param path File path (relative to SD root)
 * @param size Expected file size in bytes
 * @param crc Expected CRC32 of the file
 */
void cmd_FS_PUT(const String& path, uint32_t size, uint32_t crc) {
  if (!inUpdate) {
    Serial.println(F("ERR STATE"));
    return;
  }
  
  if (!pathAllowed(path)) {
    Serial.println(F("ERR PATH"));
    return;
  }
  
  String stagingPath = String("/_staging") + path;
  
  // Create parent directories
  if (!createDirForFile(stagingPath)) {
    return;
  }
  
  // Open file for writing
  currentFile = SD.open(stagingPath.c_str(), FILE_WRITE);
  if (!currentFile) {
    Serial.println(F("ERR OPEN"));
    return;
  }
  
  // Initialize file reception
  crcAccumulator = 0;
  bytesReceived = 0;
  expectedSize = size;
  expectedCrc = crc;
  
  Serial.println(F("OK"));
}

/**
 * Updates CRC32 with a new chunk of data
 * 
 * @param crc Current CRC value
 * @param data Pointer to data buffer
 * @param length Length of data
 * @return Updated CRC value
 */
uint32_t crc32_update(uint32_t crc, const uint8_t *data, size_t length) {
  // Use the existing CRC32 calculation function
  return calculate_crc32(data, length, crc);
}

/**
 * Handles incoming file data chunks
 * 
 * @param length Number of bytes in the chunk
 * @param data Pointer to data buffer
 */
void cmd_FS_DATA(uint16_t length, uint8_t* data) {
  if (!inUpdate || !currentFile) {
    Serial.println(F("ERR STATE"));
    return;
  }
  
  // Write data to file
  size_t written = currentFile.write(data, length);
  if (written != length) {
    Serial.println(F("ERR WRITE"));
    currentFile.close();
    return;
  }
  
  // Update CRC and byte count
  crcAccumulator = crc32_update(crcAccumulator, data, length);
  bytesReceived += length;
  
  Serial.println(F("OK"));
}

/**
 * Finishes a file transfer and verifies the CRC
 */
void cmd_FS_DONE() {
  if (!inUpdate || !currentFile) {
    Serial.println(F("ERR STATE"));
    return;
  }
  
  // Close the file
  currentFile.flush();
  currentFile.close();
  
  // Verify size and CRC
  if (bytesReceived != expectedSize) {
    Serial.print(F("ERR SIZE "));
    Serial.print(bytesReceived);
    Serial.print(F("/"));
    Serial.println(expectedSize);
    return;
  }
  
  if (crcAccumulator != expectedCrc) {
    Serial.print(F("ERR CRC "));
    Serial.print(crcAccumulator, HEX);
    Serial.print(F("/"));
    Serial.println(expectedCrc, HEX);
    return;
  }
  
  // File processed successfully
  filesProcessed++;
  
  Serial.println(F("OK"));
}

/**
 * Commits all staged files to their final destinations
 */
void cmd_FS_COMMIT() {
  if (!inUpdate) {
    Serial.println(F("ERR STATE"));
    return;
  }
  
  // Check if all expected files were processed
  if (filesProcessed != expectedFiles) {
    Serial.print(F("ERR COUNT "));
    Serial.print(filesProcessed);
    Serial.print(F("/"));
    Serial.println(expectedFiles);
    return;
  }
  
  Serial.println(F("[FS] Moving files from staging to final locations..."));
  
  // Process audio files
  moveDirectory("/_staging/audio/human", "/audio/human");
  moveDirectory("/_staging/audio/generated", "/audio/generated");
  
  // Process playlists
  moveDirectory("/_staging/mappings/playlists", "/mappings/playlists");
  
  // Process config files
  moveDirectory("/_staging/config", "/config");
  
  // Process state files
  moveDirectory("/_staging/state", "/state");
  
  // Reset state
  inUpdate = false;
  inMaintenanceMode = false;
  
  Serial.println(F("OK"));
}

/**
 * Recursively moves files from source directory to destination directory
 * 
 * @param srcDir Source directory path
 * @param dstDir Destination directory path
 */
void moveDirectory(const String& srcDir, const String& dstDir) {
  // Create destination directory if it doesn't exist
  if (!SD.exists(dstDir.c_str())) {
    if (!SD.mkdir(dstDir.c_str())) {
      Serial.print(F("[FS] Failed to create directory: "));
      Serial.println(dstDir);
      return;
    }
  }
  
  // Open the source directory
  File dir = SD.open(srcDir.c_str());
  if (!dir) {
    // Source directory doesn't exist or can't be opened
    return;
  }
  
  if (!dir.isDirectory()) {
    dir.close();
    return;
  }
  
  // Process each entry in the directory
  while (true) {
    File entry = dir.openNextFile();
    if (!entry) break;
    
    String entryName = entry.name();
    String srcPath = srcDir + "/" + entryName;
    String dstPath = dstDir + "/" + entryName;
    
    if (entry.isDirectory()) {
      // Recursively process subdirectory
      entry.close();
      moveDirectory(srcPath, dstPath);
    } else {
      // Copy file from staging to destination
      entry.close();
      
      // Remove destination file if it exists
      if (SD.exists(dstPath.c_str())) {
        SD.remove(dstPath.c_str());
      }
      
      // Rename (move) the file
      if (SD.rename(srcPath.c_str(), dstPath.c_str())) {
        Serial.print(F("[FS] Moved: "));
        Serial.print(srcPath);
        Serial.print(F(" -> "));
        Serial.println(dstPath);
      } else {
        Serial.print(F("[FS] Failed to move: "));
        Serial.println(srcPath);
      }
    }
  }
  
  dir.close();
}

/**
 * Aborts the current file transfer session
 */
void cmd_FS_ABORT() {
  if (!inUpdate) {
    Serial.println(F("ERR STATE"));
    return;
  }
  
  // Close any open file
  if (currentFile) {
    currentFile.close();
  }
  
  // Reset state
  inUpdate = false;
  inMaintenanceMode = false;
  
  Serial.println(F("OK"));
}

/**
 * Reloads configuration and clears caches
 */
void cmd_CFG_RELOAD() {
  // Reload mode configuration
  loadGlobalConfiguration();
  
  // Reload button mappings
  loadButtonMappings();
  
  // Clear playlist cache
  clearPlaylistCache();
  
  Serial.println(F("OK"));
}

// ===== SERIAL COMMAND HANDLING =====

/**
 * Processes a line received from serial communication
 * 
 * @param line The command line to process
 */
void handleExtendedSerialCommand(const String& line) {
  // Button simulation commands
  if (line.startsWith("SIM_KEY ")) {
    String key = getToken(line, 1);
    int count = parseIntOr(line, 2, 1);
    int gap = parseIntOr(line, 3, 250);
    
    int16_t idx = idxForKey(key);
    if (idx >= 0) {
      enqueueSimPress(idx, count, gap);
      Serial.println(F("OK"));
    } else {
      Serial.print(F("ERR KEY "));
      Serial.println(key);
    }
  }
  else if (line.startsWith("SIM_INPUT ")) {
    String id = getToken(line, 1);
    int count = parseIntOr(line, 2, 1);
    int gap = parseIntOr(line, 3, 250);
    
    int16_t idx = idxForInputId(id);
    if (idx >= 0) {
      enqueueSimPress(idx, count, gap);
      Serial.println(F("OK"));
    } else {
      Serial.print(F("ERR INPUT "));
      Serial.println(id);
    }
  }
  else if (line.startsWith("PLAY_KEY ")) {
    String key = getToken(line, 1);
    String bank = getToken(line, 2);
    
    // Find the key's label
    int16_t idx = idxForKey(key);
    if (idx >= 0) {
      if (bank.equalsIgnoreCase("HUMAN")) {
        // Force human bank
        playButtonAudioForBank(mapTab[idx].label, true);
      } 
      else if (bank.equalsIgnoreCase("GENERATED")) {
        // Force generated bank
        playButtonAudioForBank(mapTab[idx].label, false);
      } 
      else {
        // Use default priority logic
        playButtonAudioWithCount(mapTab[idx].label, 1);
      }
      Serial.println(F("OK"));
    } else {
      Serial.print(F("ERR KEY "));
      Serial.println(key);
    }
  }
  else if (line == "STOP") {
    musicPlayer.stopPlaying();
    Serial.println(F("OK"));
  }
  // File transfer commands
  else if (line.startsWith("FS_BEGIN ")) {
    uint8_t numFiles = parseIntOr(line, 1, 0);
    uint32_t totalBytes = parseIntOr(line, 2, 0);
    uint32_t manifestCrc = strtoul(getToken(line, 3).c_str(), NULL, 16);
    cmd_FS_BEGIN(numFiles, totalBytes, manifestCrc);
  }
  else if (line.startsWith("FS_PUT ")) {
    String path = getToken(line, 1);
    uint32_t size = strtoul(getToken(line, 2).c_str(), NULL, 10);
    uint32_t crc = strtoul(getToken(line, 3).c_str(), NULL, 16);
    cmd_FS_PUT(path, size, crc);
  }
  else if (line == "FS_DONE") {
    cmd_FS_DONE();
  }
  else if (line == "FS_COMMIT") {
    cmd_FS_COMMIT();
  }
  else if (line == "FS_ABORT") {
    cmd_FS_ABORT();
  }
  else if (line == "CFG_RELOAD") {
    cmd_CFG_RELOAD();
  }
  else {
    // Not an extended command, handle as a regular command
    return;
  }
}

// ===== INTEGRATION HELPERS =====

/**
 * Helper function to play audio for a specific bank (human or generated)
 * 
 * @param key The key label
 * @param isHuman True for human audio, false for generated
 */
void playButtonAudioForBank(const char* key, bool isHuman) {
  // This needs to be implemented according to your existing audio system
  // It should play audio from the selected bank without using priority logic
  
  const char* trackPath = getNextTrack(key, isHuman);
  if (trackPath != nullptr) {
    playTrack(trackPath);
  } else {
    Serial.print(F("[PLAY] No track available for key '"));
    Serial.print(key);
    Serial.print(F("' in "));
    Serial.print(isHuman ? "HUMAN" : "GENERATED");
    Serial.println(F(" bank"));
  }
}
