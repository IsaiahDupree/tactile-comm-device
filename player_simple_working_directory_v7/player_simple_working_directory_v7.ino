/*
 * Tactile Communication Device - Updated for New SD Card Structure
 * 
 * This version works strictly with the new SD card structure:
 * - config/keys.csv for button definitions
 * - mappings/index.csv for playlist mappings
 * - audio/human/[KEY]/ and audio/generated/[KEY]/ for audio files
 * - playlist.m3u files in each audio directory
 * 
 * Hardware Components:
 * - Arduino UNO R4 WiFi
 * - Adafruit VS1053 Codec Breakout or Shield
 * - 3x PCF8575 I2C port expanders (0x20, 0x21, 0x22)
 * - MicroSD card (formatted as FAT32)
 * - 32+ tactile buttons
 * - Quality speaker/headphones
 * - Rechargeable battery pack
 * 
 * IMPORTANT: Install SdFat library v2.2.3+ from Library Manager
 * Tools > Manage Libraries > Search "SdFat" > Install
 */

#include <SPI.h>
#include <Wire.h>
#include <EEPROM.h>
#include "Adafruit_PCF8575.h"
#include "Adafruit_VS1053.h"
#include <string.h>
#include <ctype.h>

// ==== WIFI MODES ==================================================
#define ENABLE_WIFI_DATA_MODE 1        // keep your TCP data server
#define ENABLE_SOFTAP_MODE     1        // turn on SoftAP ability
#define ENABLE_HTTP_BROWSER   1         // built-in website
#define DATA_TCP_PORT          3333
#define HTTP_PORT             80
// Do not autostart WiFi; enable via PERIOD x5 toggle
#ifndef WIFI_START_ON_BOOT
#define WIFI_START_ON_BOOT 0
#endif

#if ENABLE_WIFI_DATA_MODE
  #include <WiFiS3.h>
  WiFiServer dataSrv(DATA_TCP_PORT);
  WiFiClient dataCli;
#if ENABLE_HTTP_BROWSER
  WiFiServer httpSrv(HTTP_PORT);
#endif
#endif

// Optional: require AUTH token before PUT/DEL when on Wi-Fi
#ifndef DATA_WIFI_REQUIRE_AUTH
#define DATA_WIFI_REQUIRE_AUTH 0     // 0 = disable auth for testing
#endif
static bool dm_authed = (DATA_WIFI_REQUIRE_AUTH == 0);

// Loaded from SD (/CONFIG/WIFI.CFG); if SSID is empty → start SoftAP
static char WIFI_SSID[33] = "";
static char WIFI_PASS[65] = "";
static char WIFI_TOKEN[64] = "";

// Runtime WiFi state and inactivity timer
static bool wifiEnabled = false;
static unsigned long wifi_last_activity_ms = 0;
static const unsigned long WIFI_AUTO_OFF_MS = 3600000UL; // 1 hour

// Generic stream for Data Mode (Serial by default)
static Stream* DM = &Serial;

// Convenience macros so you don't have to refactor everything
#define DM_AVAILABLE()    (DM->available())
#define DM_READ()         (DM->read())
#define DM_WRITE(b, n)    (DM->write((const uint8_t*)(b), (n)))
#define DM_PRINTLN(s)     (DM->println(F(s)))
#define DM_PRINT(s)       (DM->print(F(s)))
#define DM_PRINTF(...)    (DM->printf(__VA_ARGS__))
#define DM_FLUSH()        (DM->flush())

// ==== SEGMENT 1: DATA MODE GLOBALS & CONSTANTS ====

/* ---- user-tunable knobs ---- */
#define DATA_BAUD_HZ                115200   // Standard baud rate
#define DATA_IDLE_TIMEOUT_MS        30000    // auto-exit after 30s idle
#define DATA_WRITE_ENABLE_FLAG_PATH "/CONFIG/WRITES.FLG"  // require this file to allow PUT/DEL
#define DATA_USE_CRC32              0        // 0=disable for speed (avoid double SD reads)

// ---- progress logging knobs ----
#define LOG_PROGRESS            1          // 0=off, 1=on
#define PROG_STEP_BYTES         (16*1024)  // log every 16KB
static inline void logProgress(const char* tag, uint32_t done, uint32_t total, unsigned long t0_ms) {
  if (!LOG_PROGRESS) return;
  float secs = (millis() - t0_ms) / 1000.0f;
  float kBps = secs > 0 ? (done / 1024.0f) / secs : 0.0f;
  Serial.print(tag); Serial.print(" ");
  Serial.print(done); Serial.print("/"); Serial.print(total); Serial.print(" (");
  if (total) Serial.print(100.0f * done / total, 1); else Serial.print(0,1);
  Serial.print("%) @ "); Serial.print(kBps, 1); Serial.println(" kB/s");
}

// Flow control settings
#ifndef DM_FLOW_BLOCK
#define DM_FLOW_BLOCK 512     // bytes per credit
#endif

// === WRITE FLAG BEHAVIOR ===============================
// Set to 0 → writes always allowed (no /CONFIG/WRITES.FLG check)
// Set to 1 → require /CONFIG/WRITES.FLG (original behavior)
#ifndef DATA_REQUIRE_WRITE_FLAG
#define DATA_REQUIRE_WRITE_FLAG 0   // <-- disable write-lock entirely
#endif
// =======================================================

/* ---- device mode ---- */
enum class DeviceMode : uint8_t { NORMAL, DATA_MODE };
DeviceMode deviceMode = DeviceMode::NORMAL;

/* ---- serial line collector (line framed commands) ---- */
static const size_t DM_LINE_MAX = 128;
static char dm_line[DM_LINE_MAX];
static size_t dm_line_len = 0;

// Handshake collection state (NORMAL mode)
static bool dm_hs_active = false;
static const unsigned long DM_HS_TIMEOUT_MS = 1500;
static unsigned long dm_hs_last_ms = 0;

/* ---- data mode state ---- */
enum class DataCmdState : uint8_t { LINE, PUT_PAYLOAD, GET_STREAM };
DataCmdState dm_state = DataCmdState::LINE;

unsigned long dm_last_activity_ms = 0;

/* ---- PUT state ---- */
File dm_put_file;
char dm_put_tmp_path[128];
char dm_put_final_path[128];
size_t dm_bytes_since_ack = 0;
uint32_t dm_put_remaining = 0;
#if DATA_USE_CRC32
uint32_t dm_put_crc_host = 0;
uint32_t dm_put_crc_calc = 0;
#endif
// small write buffer for efficiency
static const size_t DM_IOBUF_SZ = 512;
uint8_t dm_wbuf[DM_IOBUF_SZ];
size_t dm_wbuf_len = 0;

/* ---- GET state ---- */
File dm_get_file;
uint8_t dm_rbuf[DM_IOBUF_SZ];

/* ---- helpers forward decls ---- */
static inline void dm_line_reset();
void enterDataMode();
void exitDataMode();
void dm_feedByte(char c);
void dm_handleLine(const char* line);
bool isWriteEnabled();
bool mkdir_p(const char* path);
bool atomicRename(const char* srcTmp, const char* dstFinal);
void path_audio(char* out, size_t outsz, const char* bank, const char* key, const char* fname);
static void wifiLoadCfg();
static bool startSTA();
static bool startAP();
static void listPath(const char* path);
static void treeWalk(const char* base, uint8_t depth, uint8_t maxDepth);
#if ENABLE_HTTP_BROWSER
struct HttpReq {
  String method, path, query, auth;
  int contentLen = 0;
};
static void handleHttpClient(WiFiClient& cli);
static String urlDecode(const String& s);
static bool parseRequest(WiFiClient &cli, HttpReq &r);
static bool authOK(const String& query, const String& auth);
static void api_put(WiFiClient& c, WiFiClient& src, const HttpReq& r, const String& rawPath);
#endif
#if DATA_USE_CRC32
void crc32_reset(uint32_t &crc);
void crc32_update(uint32_t &crc, const uint8_t* data, size_t len);
#endif

// Compile-time logging control
#ifndef VERBOSE_LOGS
#define VERBOSE_LOGS 0
#endif

// Control whether to read .txt captions before playback (SD I/O)
#ifndef CAPTION_READS
#define CAPTION_READS 1
#endif

// VS1053 pins - using shield pin mapping
#define VS1053_RESET   -1     // VS1053 reset pin (tied high on shield)
#define VS1053_CS       7     // VS1053 xCS (shield pin mapping)
#define VS1053_DCS      6     // VS1053 xDCS (shield pin mapping)
#define CARDCS          4     // micro-SD CS (fixed trace on shield)
#define VS1053_DREQ     3     // VS1053 DREQ (INT1 on Uno)

Adafruit_VS1053_FilePlayer musicPlayer = 
  Adafruit_VS1053_FilePlayer(VS1053_RESET, VS1053_CS, VS1053_DCS, VS1053_DREQ, CARDCS);

// SD objects
File file;


// ===== PCF8575 Expander Configuration =====
// Planned expander addresses (expandable design)
static const uint8_t PCF_ADDR[] = { 0x20, 0x21, 0x22 };
static const uint8_t NUM_PCF = sizeof(PCF_ADDR) / sizeof(PCF_ADDR[0]);
static const uint16_t EXPANDER_BUTTONS = (uint16_t)NUM_PCF * 16;

// Computed total button constants
static const uint8_t EXTRA_COUNT = 4;
static const uint16_t TOTAL_EXPANDER_PINS = NUM_PCF * 16;
static const uint16_t TOTAL_BUTTONS = TOTAL_EXPANDER_PINS + EXTRA_COUNT;

// Configuration constants (reduced to save RAM on UNO R4)
#define MAX_KEYS 36            // was 50; A-Z + specials fit comfortably
#define MAX_FILENAME_LEN 48    // was 64
// Tight path buffer for /audio/{bank}/{KEY}/NNN.mp3
#define MAX_PATH_LEN 64

// PCF8575 I2C port expanders (supporting up to 32+ buttons)
Adafruit_PCF8575 pcf[NUM_PCF];

// Extra Arduino pins for additional controls (avoid pins 0,1 for Serial)
const uint8_t extraPins[] = { 8, 9, 2, 5 };   // Safe pins: VS1053 uses pins 3,4,6,7
// Compile-time validation
static_assert(sizeof(extraPins) / sizeof(extraPins[0]) == EXTRA_COUNT, "EXTRA_COUNT mismatch with extraPins array");

// Priority mode enumeration
enum class PriorityMode : uint8_t {
  HUMAN_FIRST,
  GENERATED_FIRST
};

// Key configuration structure
struct KeyConfig {
  char key[24];           // Key name (HELLO_HOW_ARE_YOU fits; reduces RAM)
  char description[24];   // Truncated description is acceptable for logging
  bool hasHuman;          // Whether human audio exists
  bool hasGenerated;      // Whether generated audio exists
};

// Button mapping structure (use key index instead of duplicating key strings)
struct ButtonMapping {
  bool used;
  int16_t keyIndex;       // index into keys[] (-1 if unset)
  uint8_t buttonIndex;    // Physical button index
  char source[12];        // e.g., "keys.csv"
  char input[12];         // e.g., "pcf0:2" or "gpio:8"
};

// ===== NEW AUDIO SOURCING ARCHITECTURE =====
// Completely reworked to handle flexible audio file sourcing
// Supports both numbered files (001.mp3, 002.mp3) and named files
// Works with current SD card structure on D: drive

static inline bool endsWithIgnoreCase(const char *s, const char *suffix) {
  size_t ls = strlen(s), lt = strlen(suffix);
  if (lt > ls) return false;
  const char *a = s + (ls - lt);
  for (size_t i = 0; i < lt; i++) {
    char c1 = a[i];
    char c2 = suffix[i];
    if (c1 >= 'A' && c1 <= 'Z') c1 = (char)(c1 - 'A' + 'a');
    if (c2 >= 'A' && c2 <= 'Z') c2 = (char)(c2 - 'A' + 'a');
    if (c1 != c2) return false;
  }
  return true;
}

static inline bool hasAudioExt(const char *name) {
  return endsWithIgnoreCase(name, ".MP3") || endsWithIgnoreCase(name, ".WAV") || endsWithIgnoreCase(name, ".OGG");
}

// Audio source type enumeration
enum class AudioSource : uint8_t {
  HUMAN,
  GENERATED,
  AUTO  // Use current mode preference
};

// Audio file discovery structure
struct AudioFileInfo {
  char path[MAX_PATH_LEN];
  char description[64];
  bool exists;
  AudioSource source;
};

// New flexible audio sourcing system
class AudioSourceManager {
public:
  // Find audio file for a key and press count with cross-bank support
  static bool findAudioFile(const char* key, uint8_t pressCount, AudioSource preferredSource, AudioFileInfo* result) {
    result->exists = false;
    result->path[0] = '\0';
    result->description[0] = '\0';

    const char* humanDir = "HUMAN";
    const char* genDir   = generatedDir();

    // Count both banks first
    uint8_t humanCount = countAudioFilesInDir(humanDir, key);
    uint8_t genCount   = countAudioFilesInDir(genDir,   key);

    const bool prefIsHuman = (preferredSource == AudioSource::HUMAN);
    const char* prefDir = prefIsHuman ? humanDir : genDir;
    const char* altDir  = prefIsHuman ? genDir   : humanDir;
    uint8_t prefCount   = prefIsHuman ? humanCount : genCount;
    uint8_t altCount    = prefIsHuman ? genCount   : humanCount;

    Serial.print(F("[AUDIO_SEARCH] Looking for key '"));
    Serial.print(key);
    Serial.print(F("', press #"));
    Serial.print(pressCount);
    Serial.print(F(", preferred source: "));
    Serial.println(prefIsHuman ? F("HUMAN") : F("GENERATED"));

    // 1) Exact index in preferred bank
    if (pressCount >= 1 && pressCount <= prefCount) {
      if (tryIndexInDir(prefDir, key, pressCount, result)) {
        result->source = prefIsHuman ? AudioSource::HUMAN : AudioSource::GENERATED;
        return true;
      }
    }

    // 2) Exact index in the other bank (so press #4 can hit GENERATED/004 if HUMAN has only 3)
    if (pressCount >= 1 && pressCount <= altCount) {
      if (tryIndexInDir(altDir, key, pressCount, result)) {
        result->source = prefIsHuman ? AudioSource::GENERATED : AudioSource::HUMAN;
        return true;
      }
    }

    // 3) Wrap across the combined total (preferred bank comes first in the ordering)
    uint16_t total = (uint16_t)prefCount + (uint16_t)altCount;
    if (total == 0) {
      Serial.println(F("[AUDIO_SEARCH] ✗ No audio files in either bank"));
      return false;
    }

    uint16_t wrapped = ((pressCount - 1) % total) + 1;
    if (wrapped <= prefCount) {
      if (tryIndexInDir(prefDir, key, (uint8_t)wrapped, result)) {
        result->source = prefIsHuman ? AudioSource::HUMAN : AudioSource::GENERATED;
        return true;
      }
    } else {
      uint8_t altIdx = (uint8_t)(wrapped - prefCount);
      if (altIdx >= 1 && altIdx <= altCount) {
        if (tryIndexInDir(altDir, key, altIdx, result)) {
          result->source = prefIsHuman ? AudioSource::GENERATED : AudioSource::HUMAN;
          return true;
        }
      }
    }

    Serial.println(F("[AUDIO_SEARCH] ✗ No audio file found for this key/index"));
    return false;
  }
  
  // Keep your existing rules (SHIFT: 1=HUMAN, >=2=GENERATED, PERIOD >=2=GENERATED, else current mode)
  static AudioSource getPreferredSource(const char* key, uint8_t pressCount, PriorityMode currentMode) {
    if (strcmp(key, "SHIFT") == 0) {
      if (pressCount == 1) return AudioSource::HUMAN;
      if (pressCount >= 2) return AudioSource::GENERATED;
    }
    if (strcmp(key, "PERIOD") == 0) {
      if (pressCount >= 2) return AudioSource::GENERATED;
    }
    return (currentMode == PriorityMode::HUMAN_FIRST) ? AudioSource::HUMAN : AudioSource::GENERATED;
  }
  
private:
  static const char* generatedDir() {
    // Prefer long name if it exists; fallback to 8.3 alias
    static bool checked = false;
    static const char* dir = "GENERA~1";
    if (!checked) {
      if (SD.exists("/AUDIO/GENERATED")) dir = "GENERATED";
      checked = true;
    }
    return dir;
  }

  static bool tryIndexInDir(const char* sourceDir, const char* key, uint8_t index, AudioFileInfo* result) {
    // Try numbered NNN.MP3 first
    char numberedPath[MAX_PATH_LEN];
    snprintf(numberedPath, sizeof(numberedPath), "/AUDIO/%s/%s/%03u.MP3", sourceDir, key, index);

    Serial.print(F("[AUDIO_SEARCH] Checking path: "));
    Serial.println(numberedPath);

    if (SD.exists(numberedPath)) {
      Serial.println(F("[AUDIO_SEARCH] ✓ Found numbered file!"));
      strncpy(result->path, numberedPath, sizeof(result->path) - 1);
      result->path[sizeof(result->path) - 1] = '\0';
      result->exists = true;
      loadDescription(result);
      return true;
    }

    // Otherwise, pick the Nth audio file present (creation order)
    if (findNthAudioInDir(sourceDir, key, index, result)) {
      Serial.println(F("[AUDIO_SEARCH] ✓ Found via directory scan!"));
      return true;
    }
    Serial.println(F("[AUDIO_SEARCH] ✗ Not found in this source/index"));
    return false;
  }

  // Count total audio files in a directory for looping support
  static uint8_t countAudioFilesInDir(const char* sourceDir, const char* key) {
    char dirPath[MAX_PATH_LEN];
    snprintf(dirPath, sizeof(dirPath), "/AUDIO/%s/%s", sourceDir, key);
    
    File dir = SD.open(dirPath);
    if (!dir) {
      return 0;
    }
    
    uint8_t count = 0;
    while (true) {
      File f = dir.openNextFile();
      if (!f) break;
      
      if (!f.isDirectory() && hasAudioExt(f.name())) {
        count++;
      }
      f.close();
    }
    
    dir.close();
    return count;
  }

  // Load description from corresponding .txt file
  static void loadDescription(AudioFileInfo* info) {
    char txtPath[MAX_PATH_LEN];
    strncpy(txtPath, info->path, sizeof(txtPath) - 1);
    txtPath[sizeof(txtPath) - 1] = '\0';
    
    // Replace .mp3 with .txt
    char* ext = strrchr(txtPath, '.');
    if (ext) {
      strncpy(ext, ".txt", sizeof(txtPath) - (ext - txtPath));
      
      File txtFile = SD.open(txtPath);
      if (txtFile) {
        String content = txtFile.readString();
        content.trim();
        
        // Remove comment prefix if present
        if (content.startsWith("#")) {
          int colonPos = content.indexOf(": ");
          if (colonPos >= 0) {
            content = content.substring(colonPos + 2);
          }
        }
        
        strncpy(info->description, content.c_str(), sizeof(info->description) - 1);
        info->description[sizeof(info->description) - 1] = '\0';
        txtFile.close();
      }
    }
  }
  
  // Find the Nth audio file in a directory
  static bool findNthAudioInDir(const char* sourceDir, const char* key, uint8_t n, AudioFileInfo* result) {
    char dirPath[MAX_PATH_LEN];
    snprintf(dirPath, sizeof(dirPath), "/AUDIO/%s/%s", sourceDir, key);
    
    Serial.print(F("[DIR_SCAN] Opening directory: "));
    Serial.println(dirPath);
    
    File dir = SD.open(dirPath);
    if (!dir) {
      Serial.println(F("[DIR_SCAN] ✗ Directory does not exist"));
      return false;
    }
    
    uint16_t count = 0;
    bool found = false;
    
    Serial.print(F("[DIR_SCAN] Looking for file #"));
    Serial.print(n);
    Serial.println(F(" in directory:"));
    
    while (true) {
      File f = dir.openNextFile();
      if (!f) break;
      
      if (!f.isDirectory() && hasAudioExt(f.name())) {
        count++;
        Serial.print(F("[DIR_SCAN] Found audio file #"));
        Serial.print(count);
        Serial.print(F(": "));
        Serial.println(f.name());
        
        if (count == n) {
          snprintf(result->path, sizeof(result->path), "%s/%s", dirPath, f.name());
          result->exists = true;
          found = true;
          Serial.print(F("[DIR_SCAN] ✓ Selected: "));
          Serial.println(result->path);
          f.close();
          break;
        }
      }
      f.close();
    }
    
    dir.close();
    
    if (!found) {
      Serial.print(F("[DIR_SCAN] ✗ Could not find file #"));
      Serial.print(n);
      Serial.print(F(" (found "));
      Serial.print(count);
      Serial.println(F(" total audio files)"));
    }
    
    return found;
  }
};

// Global variables
KeyConfig keys[MAX_KEYS];
uint8_t numKeys = 0;
ButtonMapping buttonMap[TOTAL_BUTTONS];
PriorityMode currentMode = PriorityMode::HUMAN_FIRST;

// Simplified audio availability tracking
bool keyHasHuman[MAX_KEYS] = {false};
bool keyHasGenerated[MAX_KEYS] = {false};

int keyIndexByName(const char *k) {
  for (uint8_t i = 0; i < numKeys; i++) if (strcmp(keys[i].key, k) == 0) return i;
  return -1;
}

// Audio playback state
bool isPlaying = false;
char currentTrackPath[MAX_PATH_LEN] = {0};
unsigned long audioStartTime = 0;

// State for edge-detection
uint16_t last_s[NUM_PCF];
bool lastExtra[EXTRA_COUNT];

// Button press timing for multi-press detection
unsigned long lastPressTime[TOTAL_BUTTONS];
uint8_t pressCount[TOTAL_BUTTONS];
const unsigned long MULTI_PRESS_WINDOW = 1000; // milliseconds (increased for better multi-press detection)

// Calibration mode
bool inCalibrate = false;
bool waitingForMapping = false;
uint8_t pendingButtonIndex = 0;
String inputBuffer = "";

// Forward declarations
void loadConfiguration();
void loadKeys();
void parseKeyLine(String line);
void parseInputMapping(String inputStr, int keyIndex);
void initializeButtonMappings();
void handleButtonPress(uint8_t buttonIndex);
void playAudioForKey(const char* key, uint8_t pressCount);
void checkButtons();
void handleMultiPress();
void handleShiftButtonPress(uint8_t pressCount);
void handlePeriodButtonPress(uint8_t pressCount);
void printStatus();
void printMenu();
void playSineTest();
void printWordMap();
bool findAudioForKey(const char* key, uint8_t pressCount, AudioFileInfo* result);
void saveCalibrationToSD();
// WiFi toggle helpers
void wifiEnableAP();
void wifiDisable();
void wifiToggle();
static inline void wifiTouchActivity() { wifi_last_activity_ms = millis(); }

void setup() {
  Serial.begin(DATA_BAUD_HZ);
  while (!Serial) delay(10);
  
  Serial.println(F("=== Tactile Communication Device - New SD Structure ==="));
  
  // Initialize PCF8575 expanders on Wire1 (QT Py connector)
  Wire1.begin();
  for (uint8_t i = 0; i < NUM_PCF; i++) {
    if (!pcf[i].begin(PCF_ADDR[i], &Wire1)) {
      Serial.print(F("[ERROR] PCF8575 #"));
      Serial.print(i);
      Serial.print(F(" at 0x"));
      Serial.print(PCF_ADDR[i], HEX);
      Serial.println(F(" not found!"));
      while (1) delay(10);
    }
    Serial.print(F("[OK] PCF8575 #"));
    Serial.print(i);
    Serial.print(F(" at 0x"));
    Serial.print(PCF_ADDR[i], HEX);
    Serial.println(F(" initialized"));
    
    // Set all pins as inputs with pullups
    for (uint8_t pin = 0; pin < 16; pin++) {
      pcf[i].pinMode(pin, INPUT_PULLUP);
      // Read initial state of all pins (batch read)
      last_s[i] = pcf[i].digitalReadWord();
    }
  }
  
  // Initialize extra pins
  for (uint8_t i = 0; i < EXTRA_COUNT; i++) {
    pinMode(extraPins[i], INPUT_PULLUP);
    lastExtra[i] = digitalRead(extraPins[i]);
  }
  
  // Initialize VS1053
  if (!musicPlayer.begin()) {
    Serial.println(F("[ERROR] VS1053 not found!"));
    while (1) delay(10);
  }
  Serial.println(F("[OK] VS1053 initialized"));
  
  // Initialize SD card (handled by VS1053)
  if (!SD.begin(CARDCS)) {
    Serial.println(F("[ERROR] SD card not found!"));
    while (1) delay(10);
  }
  Serial.println(F("[INIT] VS1053 initialized successfully"));
  
  // Set volume permanently to 0 (loudest setting)
  musicPlayer.setVolume(0, 0);
  Serial.println(F("[INIT] Volume permanently set to 0 (loudest)"));
  
  // Enable background playback via DREQ pin interrupt
  musicPlayer.useInterrupt(VS1053_FILEPLAYER_PIN_INT);
  Serial.println(F("[INIT] Background playback enabled via interrupt"));
  
#if ENABLE_WIFI_DATA_MODE
  wifiLoadCfg();
  if (WIFI_START_ON_BOOT) {
    // Optional: start AP on boot (AP-only per toggle design)
    wifiEnableAP();
  } else {
    Serial.println(F("[NET] Wi-Fi disabled at boot; use PERIOD×5 to toggle"));
  }
#endif

  // Load configuration from SD card
  loadConfiguration();
  
  // Skip loadMappings() - we use directory discovery instead
  
  // Initialize button state arrays
  for (uint8_t i = 0; i < TOTAL_BUTTONS; i++) {
    lastPressTime[i] = 0;
    pressCount[i] = 0;
  }
  
  Serial.println(F("[READY] Device initialized successfully"));
  
  // Play startup sine test (250ms) instead of sample MP3s
  Serial.println(F("[STARTUP] Playing built-in 250ms sine test..."));
  playSineTest();
  
  printMenu();
}

void loop() {
  // --- Accept Wi-Fi client and run Data Mode over TCP ---
#if ENABLE_WIFI_DATA_MODE
  if (wifiEnabled) {
    // Accept one client at a time
    if ((!dataCli) || !dataCli.connected()) {
      WiFiClient c = dataSrv.available();
      if (c && c.connected()) {
        dataCli.stop();
        dataCli = c;
        Serial.println(F("[NET] Client connected → DATA_MODE"));
        DM = &dataCli;
        enterDataMode();
        DM_PRINTLN("DATA:OK v1");    // same handshake banner
        wifiTouchActivity();
      }
    }
  }
#endif

#if ENABLE_HTTP_BROWSER
  // --- HTTP website ---
  if (wifiEnabled) {
    WiFiClient hc = httpSrv.available();
    if (hc) { handleHttpClient(hc); }
  }
#endif

  // If we're in DATA_MODE, consume from the active DM stream (Serial or Wi-Fi)
  if (deviceMode == DeviceMode::DATA_MODE) {
    while (DM_AVAILABLE()) { dm_feedByte((char)DM_READ()); if (wifiEnabled) wifiTouchActivity(); }
    // idle timeout already handled; when exit, restore DM to Serial
    if (deviceMode == DeviceMode::NORMAL) {
#if ENABLE_WIFI_DATA_MODE
      if (dataCli && dataCli.connected()) dataCli.stop();
#endif
      DM = &Serial;
    }
    return; // pause normal UI while in data mode
  }

  // ---- HANDSHAKE SNIFFER (NORMAL mode only) ----
  if (deviceMode == DeviceMode::NORMAL) {
    // If not already collecting, only start when we see '^'
    if (!dm_hs_active && Serial.available() && Serial.peek() == '^') {
      dm_hs_active = true;
      dm_line_reset();
      dm_hs_last_ms = millis();
    }

    // If collecting, consume every incoming byte until '\n' or timeout
    while (dm_hs_active && Serial.available()) {
      char c = Serial.read();
      dm_hs_last_ms = millis();
      if (c == '\r') continue;
      if (c != '\n') {
        if (dm_line_len + 1 < DM_LINE_MAX) {
          dm_line[dm_line_len++] = c;
          dm_line[dm_line_len] = 0;
        } else {
          // too long → abort collection
          dm_line_reset();
          dm_hs_active = false;
        }
      } else {
        // Got full line that started with '^'
        bool ok =
          (!strcmp(dm_line, "^DATA? v1")) ||
          (!strncasecmp(dm_line, "^DATA? v", 8));   // accept ^DATA? vX
        dm_line_reset();
        dm_hs_active = false;

        if (ok) {
          Serial.println("DATA:OK v1");
          enterDataMode();
          Serial.println("[DATA] mode=ENTER");  // informational; host should ignore
        }
      }
    }

    // Timeout: abandon partial handshake and let menu resume
    if (dm_hs_active && (millis() - dm_hs_last_ms > DM_HS_TIMEOUT_MS)) {
      dm_line_reset();
      dm_hs_active = false;
    }
  }

  // If we entered DATA_MODE, process protocol and pause normal UI
  if (deviceMode == DeviceMode::DATA_MODE) {
    while (Serial.available()) dm_feedByte(Serial.read());
    if (millis() - dm_last_activity_ms > DATA_IDLE_TIMEOUT_MS) {
      Serial.println("DATA:IDLE");
      exitDataMode();
    }
    return;  // do NOT fall through to menu/keyboard
  }

  // Normal mode logic continues below
  checkButtons();
  handleMultiPress();
  
  // Auto-disable WiFi after inactivity
#if ENABLE_WIFI_DATA_MODE
  if (wifiEnabled && (millis() - wifi_last_activity_ms > WIFI_AUTO_OFF_MS)) {
    Serial.println(F("[NET] Auto-off Wi-Fi due to inactivity"));
    wifiDisable();
  }
#endif
  
  // Monitor audio completion with timestamps
  if (isPlaying && !musicPlayer.playingMusic) {
    unsigned long elapsed = millis() - audioStartTime;
    Serial.print(F("[AUDIO] Track completed after "));
    Serial.print(elapsed);
    Serial.print(F("ms - File: "));
    Serial.println(currentTrackPath);
    isPlaying = false;
    currentTrackPath[0] = '\0';
  }
  
  // Handle calibration input (only in NORMAL mode, data mode already handled above)
  if (deviceMode == DeviceMode::NORMAL && Serial.available() && waitingForMapping) {
    char cmd = Serial.read();
      if (cmd == '\n' || cmd == '\r') {
        // Process the mapping
        if (inputBuffer.length() > 0) {
          inputBuffer.trim();
          inputBuffer.toUpperCase();
          
          // Validate input
          bool validKey = false;
          if (inputBuffer.length() == 1 && inputBuffer[0] >= 'A' && inputBuffer[0] <= 'Z') {
            validKey = true;
          } else if (inputBuffer == "SHIFT" || inputBuffer == "PERIOD" || inputBuffer == "SPACE" || 
                     inputBuffer == "YES" || inputBuffer == "NO" || inputBuffer == "WATER") {
            validKey = true;
          }
          
          if (validKey) {
            // Update button mapping
            int ki = keyIndexByName(inputBuffer.c_str());
            if (ki >= 0) {
              buttonMap[pendingButtonIndex].used = true;
              buttonMap[pendingButtonIndex].keyIndex = (int16_t)ki;
            } else {
              Serial.print(F("\n[ERROR] Unknown key name: "));
              Serial.println(inputBuffer);
            }
            
            Serial.print(F("\n[MAPPED] Button #"));
            Serial.print(pendingButtonIndex);
            Serial.print(F(" -> "));
            if (buttonMap[pendingButtonIndex].keyIndex >= 0) Serial.println(keys[buttonMap[pendingButtonIndex].keyIndex].key);
            else Serial.println(F("UNSET"));
            Serial.println(F("Press another button to map, or 'E' to exit calibration"));
          } else {
            Serial.print(F("\nInvalid key: "));
            Serial.print(inputBuffer);
            Serial.println(F(". Use A-Z, SHIFT, PERIOD, SPACE, YES, NO, or WATER"));
            Serial.print(F("Enter key mapping: "));
          }
        }
        
        waitingForMapping = false;
        inputBuffer = "";
      } else if (cmd == 8 || cmd == 127) { // Backspace
        if (inputBuffer.length() > 0) {
          inputBuffer.remove(inputBuffer.length() - 1);
          Serial.print(F("\b \b")); // Erase character on screen
        }
      } else if (cmd >= 32 && cmd <= 126) { // Printable characters
        inputBuffer += cmd;
        Serial.print(cmd); // Echo character
      }
      return;
  }
  
  // Normal command processing (only if not in calibration mode)
  if (Serial.available()) {
    char cmd = Serial.read();
    switch (cmd) {
      case 'C': case 'c':
        inCalibrate = !inCalibrate;
        waitingForMapping = false;
        inputBuffer = "";
        Serial.print(F("\nCalibration mode: "));
        if (inCalibrate) {
          Serial.println(F("ON"));
          Serial.println(F("Press any button to map it, or 'E' to exit"));
        } else {
          Serial.println(F("OFF"));
        }
        break;
      case 'M': case 'm':
        currentMode = (currentMode == PriorityMode::HUMAN_FIRST) ? 
                      PriorityMode::GENERATED_FIRST : PriorityMode::HUMAN_FIRST;
        Serial.print(F("Priority mode: "));
        Serial.println((currentMode == PriorityMode::HUMAN_FIRST) ? F("HUMAN_FIRST") : F("GENERATED_FIRST"));
        break;
      case 'H': case 'h':
        printMenu();
        break;
      case 'R': case 'r':
        loadConfiguration();
        Serial.println(F("Configuration reloaded"));
        break;
      case 'L': case 'l':
        Serial.println(F("\n=== SD Card Directory Listing ==="));
        listSDContents("/");
        listSDContents("/AUDIO");
        listSDContents("/AUDIO/GENERA~1");
        listSDContents("/AUDIO/GENERA~1/SHIFT");
        listSDContents("/AUDIO/HUMAN");
        listSDContents("/AUDIO/HUMAN/SHIFT");
        break;
      case 'E': case 'e':
        inCalibrate = false;
        waitingForMapping = false;
        inputBuffer = "";
        Serial.println(F("Calibration mode: OFF"));
        break;
      case 'S': case 's':
        if (inCalibrate) {
          saveCalibrationToSD();
        } else {
          printStatus();
        }
        break;
      case 'T': case 't':
        playSineTest();
        break;
    }
  }
  
  delay(10);
}

void loadConfiguration() {
  Serial.println(F("[CONFIG] Loading SD card configuration..."));
  
  // Clear existing configuration
  numKeys = 0;
  for (uint8_t i = 0; i < TOTAL_BUTTONS; i++) {
    buttonMap[i].used = false;
    buttonMap[i].keyIndex = -1;
    buttonMap[i].buttonIndex = i;
    buttonMap[i].source[0] = '\0';
    buttonMap[i].input[0] = '\0';
  }
  
  // Ensure button mappings are cleared BEFORE loading keys
  initializeButtonMappings();

  Serial.println(F("[CONFIG] Using /CONFIG/KEYS.CSV for button mappings (sd_strict_mode/buttons.csv is ignored in this build)"));
  loadKeys();
  // Skip loadMappings() - using directory-based discovery instead
  
  Serial.print(F("[CONFIG] Loaded "));
  Serial.print(numKeys);
  Serial.println(F(" keys"));
}

void loadKeys() {
  file = SD.open("/CONFIG/KEYS.CSV");
  if (!file) {
    Serial.println(F("[ERROR] Cannot open /CONFIG/KEYS.CSV"));
    return;
  }
    Serial.println(F("[CONFIG] Loading KEYS.CSV..."));
  
  // Skip header and comment lines
  String line;
  do {
    line = file.readStringUntil('\n');
    line.trim();
  } while (file.available() && (line.startsWith("#") || line.startsWith("KEY,")));
  
  // Process the first data line if we have it
  if (line.length() > 0 && !line.startsWith("#") && !line.startsWith("KEY,")) {
    parseKeyLine(line);
  }
  
  // Continue with remaining lines
  while (file.available() && numKeys < MAX_KEYS) {
    line = file.readStringUntil('\n');
    line.trim();
    
    if (line.length() == 0 || line.startsWith("#")) continue;
    
    parseKeyLine(line);
  }
  
  file.close();

  // Simplified audio availability discovery
  for (uint8_t i = 0; i < numKeys; i++) {
    String k = String(keys[i].key);
    String humanDir = "/AUDIO/HUMAN/" + k;
    String genDir   = "/AUDIO/GENERA~1/" + k;

    keyHasHuman[i] = SD.exists(humanDir.c_str());
    keyHasGenerated[i] = SD.exists(genDir.c_str());
    
    // Update legacy fields for compatibility
    keys[i].hasHuman = keyHasHuman[i];
    keys[i].hasGenerated = keyHasGenerated[i];

#if VERBOSE_LOGS
    Serial.print(F("[DISCOVER] ")); Serial.print(keys[i].key);
    Serial.print(F(" human=")); Serial.print(keyHasHuman[i] ? F("YES") : F("NO"));
    Serial.print(F(" gen="));   Serial.println(keyHasGenerated[i] ? F("YES") : F("NO"));
#endif
  }
  
#if VERBOSE_LOGS
  // Print complete word map detected on startup
  printWordMap();
#endif
}

void printWordMap() {
  Serial.println(F("\n=== DETECTED WORD MAP ==="));
  
  for (uint8_t i = 0; i < numKeys; i++) {
    if (keyHasHuman[i] || keyHasGenerated[i]) {
      Serial.print(keys[i].key);
      Serial.print(F(" → "));
      
      // Show available sources
      if (keyHasHuman[i]) {
        Serial.print(F("HUMAN"));
      }
      if (keyHasHuman[i] && keyHasGenerated[i]) {
        Serial.print(F(", "));
      }
      if (keyHasGenerated[i]) {
        Serial.print(F("GENERATED"));
      }
      
      Serial.println();
    }
  }
  
  Serial.print(F("\nTotal mapped keys: "));
  uint8_t mappedKeys = 0;
  for (uint8_t i = 0; i < numKeys; i++) {
    if (keyHasHuman[i] || keyHasGenerated[i]) mappedKeys++;
  }
  Serial.print(mappedKeys);
  Serial.print(F(" of "));
  Serial.println(numKeys);
  Serial.println(F("========================\n"));
}

void parseKeyLine(String line) {
  // Parse CSV: KEY,DESCRIPTION,INPUT
  int firstComma = line.indexOf(',');
  if (firstComma == -1) return;
  
  int secondComma = line.indexOf(',', firstComma + 1);
  if (secondComma == -1) return;
  
  String keyStr = line.substring(0, firstComma);
  String descStr = line.substring(firstComma + 1, secondComma);
  String inputStr = line.substring(secondComma + 1);
  
  keyStr.trim();
  descStr.trim();
  inputStr.trim();
  
  // Store key configuration
  keyStr.toCharArray(keys[numKeys].key, sizeof(keys[numKeys].key));
  descStr.toCharArray(keys[numKeys].description, sizeof(keys[numKeys].description));
  keys[numKeys].hasHuman = false;
  keys[numKeys].hasGenerated = false;
  
  // Parse INPUT to get button mapping
  parseInputMapping(inputStr, (int)numKeys);
  
  Serial.print(F("[KEY] "));
  Serial.print(keys[numKeys].key);
  Serial.print(F(" - "));
  Serial.print(keys[numKeys].description);
  Serial.print(F(" ("));
  Serial.print(inputStr);
  Serial.println(F(")"));
  
  numKeys++;
}

void parseInputMapping(String inputStr, int keyIndex) {
  // Parse input format: pcf<N>:<P> or gpio:<PIN>
  if (inputStr.startsWith("pcf")) {
    // Extract chip number and pin
    int colonIndex = inputStr.indexOf(':');
    if (colonIndex == -1) return;
    
    int chipNum = inputStr.substring(3, colonIndex).toInt();
    int pinNum = inputStr.substring(colonIndex + 1).toInt();
    
    // Calculate button index: chip * 16 + pin
    uint8_t buttonIndex = chipNum * 16 + pinNum;
    
    if (buttonIndex < TOTAL_BUTTONS) {
      buttonMap[buttonIndex].used = true;
      buttonMap[buttonIndex].keyIndex = keyIndex;
      strncpy(buttonMap[buttonIndex].source, "keys.csv", sizeof(buttonMap[buttonIndex].source) - 1);
      buttonMap[buttonIndex].source[sizeof(buttonMap[buttonIndex].source) - 1] = '\0';
      inputStr.toCharArray(buttonMap[buttonIndex].input, sizeof(buttonMap[buttonIndex].input));
    }
  } else if (inputStr.startsWith("gpio:")) {
    // Handle GPIO pins (extra pins)
    int gpioPin = inputStr.substring(5).toInt();
    
    // Find matching extra pin
    for (uint8_t i = 0; i < EXTRA_COUNT; i++) {
      if (extraPins[i] == gpioPin) {
        uint8_t buttonIndex = TOTAL_EXPANDER_PINS + i;
        buttonMap[buttonIndex].used = true;
        buttonMap[buttonIndex].keyIndex = keyIndex;
        strncpy(buttonMap[buttonIndex].source, "KEYS.CSV", sizeof(buttonMap[buttonIndex].source) - 1);
        buttonMap[buttonIndex].source[sizeof(buttonMap[buttonIndex].source) - 1] = '\0';
        inputStr.toCharArray(buttonMap[buttonIndex].input, sizeof(buttonMap[buttonIndex].input));
        break;
      }
    }
  }
}


void initializeButtonMappings() {
  // Clear all button mappings - they will be loaded from keys.csv
  for (uint8_t i = 0; i < TOTAL_BUTTONS; i++) {
    buttonMap[i].used = false;
    buttonMap[i].keyIndex = -1;
    buttonMap[i].source[0] = '\0';
    buttonMap[i].input[0] = '\0';
  }
  
  Serial.println(F("[CONFIG] Button mappings cleared - will load from KEYS.CSV"));
}

void checkButtons() {
  // Check PCF8575 expanders
  for (uint8_t chipIndex = 0; chipIndex < NUM_PCF; chipIndex++) {
    // Batch-read 16 GPIO bits in one I2C transaction
    uint16_t currentState = pcf[chipIndex].digitalReadWord();
    
    uint16_t changed = currentState ^ last_s[chipIndex];
    
    if (changed) {
      for (uint8_t pin = 0; pin < 16; pin++) {
        if (changed & (1 << pin)) {
          bool pressed = !(currentState & (1 << pin)); // Active low
          if (pressed) {
            uint8_t buttonIndex = chipIndex * 16 + pin;
            handleButtonPress(buttonIndex);
          }
        }
      }
      last_s[chipIndex] = currentState;
    }
  }
  
  // Check extra pins
  for (uint8_t i = 0; i < EXTRA_COUNT; i++) {
    bool currentState = digitalRead(extraPins[i]);
    if (currentState != lastExtra[i]) {
      if (!currentState) { // Active low
        uint8_t buttonIndex = TOTAL_EXPANDER_PINS + i;
        handleButtonPress(buttonIndex);
      }
      lastExtra[i] = currentState;
    }
  }
}

void handleButtonPress(uint8_t buttonIndex) {
  if (buttonIndex >= TOTAL_BUTTONS) return;
  
  unsigned long currentTime = millis();
  
  if (inCalibrate) {
    Serial.print(F("\n[CALIBRATE] Button #"));
    Serial.print(buttonIndex);
    
    // Add GPIO information
    Serial.print(F(" GPIO:"));
    if (buttonIndex < TOTAL_EXPANDER_PINS) {
      uint8_t chipIndex = buttonIndex / 16;
      uint8_t pin = buttonIndex % 16;
      Serial.print(F("PCF"));
      Serial.print(chipIndex);
      Serial.print(F("-P"));
      Serial.print(pin);
    } else {
      Serial.print(F("D"));
      Serial.print(extraPins[buttonIndex - TOTAL_EXPANDER_PINS]);
    }
    
    if (buttonMap[buttonIndex].used) {
      Serial.print(F(" (currently: "));
      if (buttonMap[buttonIndex].keyIndex >= 0 && buttonMap[buttonIndex].keyIndex < numKeys) {
        Serial.print(keys[buttonMap[buttonIndex].keyIndex].key);
      } else {
        Serial.print(F("UNSET"));
      }
      Serial.print(F(")"));
    }
    Serial.println(F(" pressed"));
    Serial.print(F("Enter key mapping (A-Z, SHIFT, PERIOD, SPACE, YES, NO, WATER): "));
    
    waitingForMapping = true;
    pendingButtonIndex = buttonIndex;
    inputBuffer = "";
    return;
  }
  
  // Multi-press detection
  if (currentTime - lastPressTime[buttonIndex] < MULTI_PRESS_WINDOW) {
    pressCount[buttonIndex]++;
  } else {
    pressCount[buttonIndex] = 1;
  }
  
  lastPressTime[buttonIndex] = currentTime;
  
  // Enhanced button press logging like v2
  Serial.print(F("[BUTTON] "));
  if (buttonIndex < 16) {
    Serial.print(F("PCF8575 #0 GPIO "));
    Serial.print(buttonIndex);
  } else if (buttonIndex < 32) {
    Serial.print(F("PCF8575 #1 GPIO "));
    Serial.print(buttonIndex - 16);
    Serial.print(F(" (idx "));
    Serial.print(buttonIndex);
    Serial.print(F(")"));
  } else if (buttonIndex < 48) {
    Serial.print(F("PCF8575 #2 GPIO "));
    Serial.print(buttonIndex - 32);
    Serial.print(F(" (idx "));
    Serial.print(buttonIndex);
    Serial.print(F(")"));
  } else {
    uint8_t xp = extraPins[buttonIndex - 48];
    Serial.print(F("Arduino Pin "));
    Serial.print(xp);
    Serial.print(F(" (idx "));
    Serial.print(buttonIndex);
    Serial.print(F(")"));
  }
  
  if (buttonMap[buttonIndex].used) {
    Serial.print(F(" → "));
    if (buttonMap[buttonIndex].keyIndex >= 0 && buttonMap[buttonIndex].keyIndex < numKeys) {
      Serial.print(keys[buttonMap[buttonIndex].keyIndex].key);
    } else {
      Serial.print(F("UNSET"));
    }
    if (buttonMap[buttonIndex].source[0] != '\0') {
      Serial.print(F(" [src:"));
      Serial.print(buttonMap[buttonIndex].source);
      Serial.print(F(" input:"));
      Serial.print(buttonMap[buttonIndex].input);
      Serial.print(F("]"));
    }
    
    // Show audio availability info
    if (buttonMap[buttonIndex].keyIndex >= 0 && buttonMap[buttonIndex].keyIndex < numKeys) {
      KeyConfig* keyConfig = &keys[buttonMap[buttonIndex].keyIndex];
      Serial.print(F(" [Human:"));
      Serial.print(keyConfig->hasHuman ? F("YES") : F("NO"));
      Serial.print(F("|Generated:"));
      Serial.print(keyConfig->hasGenerated ? F("YES") : F("NO"));
      Serial.print(F("]"));
    }
  } else {
    Serial.print(F(" → UNMAPPED"));
    // Helpful hint to trace back to CSV mapping
    Serial.print(F(" | Hint: add INPUT mapping for this button in /CONFIG/KEYS.CSV as pcf"));
    if (buttonIndex < TOTAL_EXPANDER_PINS) {
      uint8_t chipIndex = buttonIndex / 16;
      uint8_t pin = buttonIndex % 16;
      Serial.print(chipIndex);
      Serial.print(F(":"));
      Serial.print(pin);
    } else {
      Serial.print(F("gpio:"));
      Serial.print(extraPins[buttonIndex - TOTAL_EXPANDER_PINS]);
    }
  }
  
  Serial.print(F(" | Press #"));
  Serial.print(pressCount[buttonIndex]);
  Serial.print(F(" @ "));
  Serial.print(currentTime);
  Serial.println(F("ms"));
}

void handleMultiPress() {
  unsigned long currentTime = millis();
  
  for (uint8_t i = 0; i < TOTAL_BUTTONS; i++) {
    if (pressCount[i] > 0 && 
        (currentTime - lastPressTime[i]) >= MULTI_PRESS_WINDOW) {
      
      // Time to process the multi-press
      if (buttonMap[i].used) {
        const char* mappedKey = (buttonMap[i].keyIndex >= 0 && buttonMap[i].keyIndex < numKeys) ? keys[buttonMap[i].keyIndex].key : "";
        
        // Special handling for SHIFT button custom sounds
        if (strcmp(mappedKey, "SHIFT") == 0) {
          handleShiftButtonPress(pressCount[i]);
        }
        // Special handling for PERIOD button mode switching
        else if (strcmp(mappedKey, "PERIOD") == 0) {
          handlePeriodButtonPress(pressCount[i]);
        }
        else {
          // Normal audio playback for other keys
          playAudioForKey(mappedKey, pressCount[i]);
        }
      }
      
      pressCount[i] = 0; // Reset press count
    }
  }
}

void playAudioForKey(const char* key, uint8_t pressCount) {
  // Alias: treat HELLO_HOW_ARE_YOU as SHIFT press #1
  if (strcmp(key, "HELLO_HOW_ARE_YOU") == 0) {
    Serial.println(F("[ALIAS] HELLO_HOW_ARE_YOU → SHIFT (press #1)"));
    playAudioForKey("SHIFT", 1);
    return;
  }
  
  // Audio interrupt: stop current playback if something is already playing
  if (isPlaying) {
    Serial.println(F("[AUDIO] Interrupting current playback for new request"));
    musicPlayer.stopPlaying();
    isPlaying = false;
  }
  
  // Find key configuration
  int keyIndex = keyIndexByName(key);
  if (keyIndex < 0) {
    Serial.print(F("[ERROR] Key not found: "));
    Serial.println(key);
    return;
  }
  
  // Enhanced logging
  Serial.print(F("[AUDIO] Playing audio for key '"));
  Serial.print(key);
  Serial.print(F("' [Human:"));
  Serial.print(keyHasHuman[keyIndex] ? F("YES") : F("NO"));
  Serial.print(F("|Generated:"));
  Serial.print(keyHasGenerated[keyIndex] ? F("YES") : F("NO"));
  Serial.print(F("], press #"));
  Serial.print(pressCount);
  Serial.print(F(", mode: "));
  Serial.println((currentMode == PriorityMode::HUMAN_FIRST) ? F("HUMAN_FIRST") : F("GENERATED_FIRST"));
  
  // Use new audio sourcing system
  AudioFileInfo audioInfo;
  if (!findAudioForKey(key, pressCount, &audioInfo)) {
    Serial.print(F("[AUDIO] No audio available for key: "));
    Serial.print(key);
    Serial.print(F(", press #"));
    Serial.println(pressCount);
    return;
  }
  
  // Stop any current playback for clean interruption
  if (musicPlayer.playingMusic) {
    musicPlayer.stopPlaying();
    Serial.println(F("[AUDIO] Stopped previous track"));
  }
  
  // Extract filename from full path for cleaner logging
  const char *filename = audioInfo.path;
  const char *slash = strrchr(audioInfo.path, '/');
  if (slash && *(slash + 1)) filename = slash + 1;
  
  // Show what audio content will be played
  Serial.print(F("[CONTENT] About to say: "));
  if (audioInfo.description[0] != '\0') {
    Serial.println(audioInfo.description);
  } else {
    Serial.println(F("[No description available]"));
  }
  
  Serial.print(F("[AUDIO] Starting: "));
  Serial.print(filename);
  Serial.print(F(" ("));
  Serial.print(audioInfo.path);
  Serial.print(F(") from "));
  Serial.println((audioInfo.source == AudioSource::HUMAN) ? F("HUMAN") : F("GENERATED"));
  
  if (musicPlayer.startPlayingFile(audioInfo.path)) {
    snprintf(currentTrackPath, sizeof(currentTrackPath), "%s", audioInfo.path);
    isPlaying = true;
    audioStartTime = millis();
    Serial.print(F("[AUDIO] ✓ Playing "));
    Serial.print(filename);
    Serial.print(F(" started at "));
    Serial.print(millis());
    Serial.println(F("ms"));
  } else {
    Serial.print(F("[ERROR] ✗ Failed to start "));
    Serial.println(filename);
  }
}

// New streamlined audio file picker using the AudioSourceManager
bool findAudioForKey(const char* key, uint8_t pressCount, AudioFileInfo* result) {
  // Determine preferred source based on current mode and special key rules
  AudioSource preferredSource = AudioSourceManager::getPreferredSource(key, pressCount, currentMode);
  
  // Find the audio file
  return AudioSourceManager::findAudioFile(key, pressCount, preferredSource, result);
}

void printStatus() {
  Serial.println(F("\n=== Device Status ==="));
  Serial.print(F("Priority Mode: "));
  Serial.println((currentMode == PriorityMode::HUMAN_FIRST) ? F("HUMAN_FIRST") : F("GENERATED_FIRST"));
  Serial.print(F("Calibration: "));
  Serial.println(inCalibrate ? F("ON") : F("OFF"));
  Serial.print(F("Keys Loaded: "));
  Serial.println(numKeys);
  Serial.print(F("Audio Playing: "));
  Serial.println(isPlaying ? F("YES") : F("NO"));
  if (isPlaying) {
    Serial.print(F("Current Track: "));
    Serial.println(currentTrackPath);
  }
  Serial.println();
}

void listSDContents(const char* path) {
  Serial.print(F("[SD_LIST] Contents of: "));
  Serial.println(path);
  
  File dir = SD.open(path);
  if (!dir) {
    Serial.println(F("[SD_LIST] ✗ Directory does not exist or cannot be opened"));
    return;
  }
  
  if (!dir.isDirectory()) {
    Serial.println(F("[SD_LIST] ✗ Path is not a directory"));
    dir.close();
    return;
  }
  
  File entry;
  int count = 0;
  while ((entry = dir.openNextFile())) {
    Serial.print(F("[SD_LIST]   "));
    Serial.print(entry.name());
    if (entry.isDirectory()) {
      Serial.println(F("/"));
    } else {
      Serial.print(F(" ("));
      Serial.print(entry.size());
      Serial.println(F(" bytes)"));
    }
    entry.close();
    count++;
  }
  
  Serial.print(F("[SD_LIST] Total items: "));
  Serial.println(count);
  dir.close();
}

void printMenu() {
  Serial.println(F("\n=== Tactile Communication Device ==="));
  Serial.println(F("Commands:"));
  Serial.println(F("  C - Interactive calibration mode (press button, type mapping)"));
  Serial.println(F("  E - Exit calibration mode"));
  Serial.println(F("  L - List SD card contents for debugging"));
  Serial.println(F("  M - Toggle priority mode (Human/Generated first)"));
  Serial.println(F("  S - Show status (or Save calibration if in calibration mode)"));
  Serial.println(F("  R - Reload configuration"));
  Serial.println(F("  T - Play sine test tone"));
  Serial.println(F("  H - Show this menu"));
  Serial.println();
}

// Handle SHIFT button custom sounds based on press count
void handleShiftButtonPress(uint8_t pressCount) {
  Serial.print(F("[SHIFT] Processing press count: "));
  Serial.println(pressCount);

  if (pressCount == 1) {
    Serial.println(F("[SHIFT] Press 1: Playing human greeting"));
  } else {
    Serial.print(F("[SHIFT] Press "));
    Serial.print(pressCount);
    Serial.println(F(": Using generated bank if available"));
  }

  // Let the unified AudioSourceManager logic pick the correct bank and index:
  playAudioForKey("SHIFT", pressCount);
}

// ==== SEGMENT 6: PERIOD×4 + CONFIRM ====

void handlePeriodButtonPress(uint8_t pressCount) {
  Serial.print(F("[PERIOD] Processing press count: "));
  Serial.println(pressCount);
  
  // New: PERIOD ×5 toggles Wi-Fi AP on/off
  if (pressCount == 5) {
    wifiToggle();
    return;
  }

  if (pressCount == 4) {
    // Guard accidental entry: require quick confirm within 3s.
    Serial.println(F("[PERIOD] Requesting Data Mode (confirm needed)"));
    // Optional spoken prompt:
    // playAudioForKey("PERIOD", 4); // record a short "entering data mode—confirm" clip

    unsigned long deadline = millis() + 3000;
    bool confirmed = false;

    // Confirmation method A: tap SHIFT once within 3s
    // (Assumes you have a button mapped to "SHIFT" in keys.csv)
    while (millis() < deadline && !confirmed) {
      // quick, low-cost peek at serial too: if host sends '!' it's a confirm
      if (Serial.available()) {
        char c = Serial.read();
        if (c == '!') confirmed = true;
      }
      // If you have a "SHIFT" mapped, you likely also have multi-press state.
      // Easiest: reuse your existing press detection once it fires.
      // Here we just poll a small slice of time:
      delay(10);
    }

    if (!confirmed) {
      Serial.println(F("[PERIOD] Data Mode not confirmed"));
      return;
    }

    // Enter data mode and emit the standard handshake response so a host can attach seamlessly
    enterDataMode();
    Serial.println("DATA:OK v1");
    return;
  }

  // Existing 1–3 behavior unchanged
  switch (pressCount) {
    case 1:
      Serial.println(F("[PERIOD] Press 1: Playing period sound"));
      playAudioForKey("PERIOD", 1);
      break;

    case 2:
      Serial.println(F("[PERIOD] Press 2: Switching to Human First mode"));
      currentMode = PriorityMode::HUMAN_FIRST;
      Serial.println(F("[MODE] Switched to: HUMAN_FIRST"));
      playAudioForKey("PERIOD", 2);
      break;

    case 3:
      Serial.println(F("[PERIOD] Press 3: Switching to Generated First mode"));
      currentMode = PriorityMode::GENERATED_FIRST;
      Serial.println(F("[MODE] Switched to: GENERATED_FIRST"));
      playAudioForKey("PERIOD", 3);
      break;

    default: {
      uint8_t cycledPress = ((pressCount - 1) % 3) + 1;
      handlePeriodButtonPress(cycledPress);
      break;
    }
  }
}

// ==== SEGMENT 2: UTILS (paths, mkdir_p, atomic rename, CRC) ====

bool isWriteEnabled() {
#if DATA_REQUIRE_WRITE_FLAG
  return SD.exists(DATA_WRITE_ENABLE_FLAG_PATH);
#else
  // Open mode: allow writes unconditionally
  return true;
#endif
}

// Build /audio/<bank>/<KEY>/<fname>
void path_audio(char* out, size_t outsz, const char* bank, const char* key, const char* fname) {
  if (fname && fname[0]) {
    snprintf(out, outsz, "/AUDIO/%s/%s/%s", bank, key, fname);
  } else {
    snprintf(out, outsz, "/AUDIO/%s/%s", bank, key);
  }
}

bool ensureConfigDir() { return mkdir_p("/CONFIG"); }

bool sd_stats(uint64_t* total, uint64_t* free) {
  // Standard Arduino SD library doesn't provide volume stats
  // Return dummy values to keep the interface working
  *total = 32ULL * 1024 * 1024 * 1024; // 32GB default
  *free = 16ULL * 1024 * 1024 * 1024;  // 16GB free default
  return true; // Always return true so STAT command works
}

// mkdir -p for SD (create intermediate directories step-by-step)
bool mkdir_p(const char* path) {
  if (!path || path[0] != '/') return false;
  char buf[128];
  size_t n = strlen(path);
  if (n >= sizeof(buf)) return false;
  strcpy(buf, path);

  // Iterate through slashes and create progressively
  for (size_t i = 1; i < n; i++) {
    if (buf[i] == '/') {
      buf[i] = '\0';
      if (!SD.exists(buf)) {
        if (!SD.mkdir(buf)) return false;
      }
      buf[i] = '/';
    }
  }
  if (!SD.exists(buf)) {
    if (!SD.mkdir(buf)) return false;
  }
  return true;
}

// Copy+remove implementation (Arduino SD library doesn't have rename)
bool atomicRename(const char* srcTmp, const char* dstFinal) {
  // Copy then remove (not strictly atomic but safer than leaving .part)
  File inF = SD.open(srcTmp, FILE_READ);
  if (!inF) return false;
  File outF = SD.open(dstFinal, FILE_WRITE);
  if (!outF) { inF.close(); return false; }

  uint8_t buf[512];
  int r;
  while ((r = inF.read(buf, sizeof(buf))) > 0) {
    if (outF.write(buf, (size_t)r) != (size_t)r) { inF.close(); outF.close(); return false; }
  }
  outF.flush(); outF.close(); inF.close();
  SD.remove(srcTmp);
  return true;
}

#if DATA_USE_CRC32
// Standard CRC32 (poly 0xEDB88320)
void crc32_reset(uint32_t &crc) { crc = 0xFFFFFFFFUL; }
void crc32_update(uint32_t &crc, const uint8_t* data, size_t len) {
  for (size_t i = 0; i < len; ++i) {
    uint32_t c = (crc ^ data[i]) & 0xFFU;
    for (uint8_t k = 0; k < 8; ++k) c = (c & 1U) ? (0xEDB88320UL ^ (c >> 1)) : (c >> 1);
    crc = (crc >> 8) ^ c;
  }
}
#endif

// ==== SEGMENT 3: PARSER & COMMAND HANDLERS (PUT/GET/DEL/LS/EXIT) ====

static inline void dm_touch() { dm_last_activity_ms = millis(); }

static inline void dm_line_reset() { dm_line_len = 0; dm_line[0] = 0; }

void dm_feedByte(char c) {
  dm_touch();
  if (dm_state == DataCmdState::LINE) {
    // accept CR/LF; end on '\n'
    if (c == '\r') return;
    if (c != '\n') {
      if (dm_line_len + 1 < DM_LINE_MAX) {
        dm_line[dm_line_len++] = c;
        dm_line[dm_line_len] = 0;
      } else {
        // line too long
        DM_PRINTLN("ERR:LINETOOLONG");
        dm_line_reset();
      }
      return;
    }
    // full line
    dm_handleLine(dm_line);
    dm_line_reset();
    return;
  }

  if (dm_state == DataCmdState::PUT_PAYLOAD) {
    // buffer incoming bytes, write in chunks
    dm_wbuf[dm_wbuf_len++] = (uint8_t)c;
    if (dm_wbuf_len == DM_IOBUF_SZ || dm_wbuf_len == dm_put_remaining) {
      size_t toWrite = dm_wbuf_len;
      if (dm_put_file.write(dm_wbuf, toWrite) != (int)toWrite) {
        DM_PRINTLN("ERR:WRITE");
        dm_put_file.close();
        SD.remove(dm_put_tmp_path);
        dm_state = DataCmdState::LINE;
        dm_bytes_since_ack = 0;
        return;
      }
      yield();
      
      // Flow control: send ACK after each block
      dm_bytes_since_ack += toWrite;
      while (dm_bytes_since_ack >= DM_FLOW_BLOCK) {
        DM->write('>');
        DM_FLUSH();
        dm_bytes_since_ack -= DM_FLOW_BLOCK;
      }
      #if DATA_USE_CRC32
      crc32_update(dm_put_crc_calc, dm_wbuf, toWrite);
      #endif
      dm_put_remaining -= (uint32_t)toWrite;
      dm_wbuf_len = 0;
    }
    if (dm_put_remaining == 0) {
      dm_put_file.flush();
      dm_put_file.close();

      // finalize: CRC check if provided
      #if DATA_USE_CRC32
      if (dm_put_crc_host != 0 && (dm_put_crc_calc ^ 0xFFFFFFFFUL) != dm_put_crc_host) {
        DM_PRINTLN("ERR:CRC");
        SD.remove(dm_put_tmp_path);
        dm_state = DataCmdState::LINE;
        return;
      }
      #endif

      if (atomicRename(dm_put_tmp_path, dm_put_final_path)) {
        DM_PRINTLN("PUT:DONE");
        delay(2);  // brief delay so final line isn't coalesced
      } else {
        DM_PRINTLN("ERR:RENAME");
        SD.remove(dm_put_tmp_path);
      }
      dm_bytes_since_ack = 0;
      dm_state = DataCmdState::LINE;
    }
    return;
  }

  if (dm_state == DataCmdState::GET_STREAM) {
    // nothing to do; GET is push-only from device side
    return;
  }
}

// Parse one complete command line
void dm_handleLine(const char* line) {
  // AUTH <token>
#if DATA_WIFI_REQUIRE_AUTH
  if (!strncmp(line, "AUTH ", 5)) {
    const char* tok = line + 5;
    if (WIFI_TOKEN[0] && (strcmp(tok, WIFI_TOKEN) == 0)) { dm_authed = true; DM_PRINTLN("AUTH:OK"); }
    else { dm_authed = false; DM_PRINTLN("AUTH:NOK"); }
    return;
  }
#else
  if (!strncmp(line, "AUTH ", 5)) {
    DM_PRINTLN("AUTH:IGNORED");
    return;
  }
#endif

  // EXIT
  if (!strcmp(line, "EXIT")) { DM_PRINTLN("DATA:BYE"); exitDataMode(); return; }

  // FLAG ON  | FLAG OFF  -> create/remove /config/allow_writes.flag
  if (!strncmp(line, "FLAG ", 5)) {
#if !DATA_REQUIRE_WRITE_FLAG
    // Open mode: accept but ignore to keep host tools happy
    const char* arg = line + 5;
    if (!strcmp(arg, "ON") || !strcmp(arg, "OFF")) {
      DM_PRINTLN("FLAG:IGNORED(OPEN)");
    } else {
      DM_PRINTLN("FLAG:ERR:ARGS");
    }
    return;
#else
    // (original FLAG handler stays as-is under FLAG mode)
    const char* arg = line + 5;
    if (!strcmp(arg, "ON")) {
      if (!ensureConfigDir()) { Serial.println("FLAG:ERR:MKDIR"); return; }
      // Try to create the flag file with explicit close
      File f = SD.open(DATA_WRITE_ENABLE_FLAG_PATH, FILE_WRITE);
      if (f) { 
        f.print("1"); // Write some content to ensure file creation
        f.flush();
        f.close(); 
        DM_PRINTLN("FLAG:ON"); 
      } else { 
        DM_PRINT("FLAG:ERR:OPEN "); DM_PRINTLN(DATA_WRITE_ENABLE_FLAG_PATH);
      }
    } else if (!strcmp(arg, "OFF")) {
      if (SD.exists(DATA_WRITE_ENABLE_FLAG_PATH)) {
        if (SD.remove(DATA_WRITE_ENABLE_FLAG_PATH)) DM_PRINTLN("FLAG:OFF");
        else DM_PRINTLN("FLAG:ERR:RM");
      } else {
        DM_PRINTLN("FLAG:OFF"); // already off
      }
    } else {
      DM_PRINTLN("FLAG:ERR:ARGS");
    }
    return;
#endif
  }

  if (!strcmp(line, "STAT")) {
    uint64_t tot=0, fre=0;
    if (sd_stats(&tot, &fre)) { 
      DM_PRINT("STAT "); 
      DM->print(tot); 
      DM_PRINT(" "); 
      DM->println(fre); 
      DM_FLUSH();
    } else {
      DM_PRINTLN("STAT:NOK");
      DM_FLUSH();
    }
    return;
  }

  if (!strcmp(line, "STATUS")) {
    bool writes = isWriteEnabled();
    DM_PRINT("STATUS WRITES=");
    DM_PRINT(writes ? "ON" : "OFF");
    DM_PRINT(" MODE=");
    DM_PRINTLN(DATA_REQUIRE_WRITE_FLAG ? "FLAG" : "OPEN");
    DM_FLUSH();
    return;
  }

  // LSP <abs_path>
  if (!strncmp(line, "LSP ", 4)) {
    char path[96];
    if (sscanf(line + 4, "%95s", path) == 1) listPath(path);
    else DM_PRINTLN("ERR:ARGS");
    return;
  }

  // TREE <abs_path> [maxDepth]
  if (!strncmp(line, "TREE ", 5)) {
    char path[96]; int md=3;
    int n = sscanf(line + 5, "%95s %d", path, &md);
    if (n >= 1) { if (md < 0) md = 0; if (md > 10) md = 10; treeWalk(path, 0, (uint8_t)md); DM_PRINTLN("TREE:DONE"); }
    else DM_PRINTLN("ERR:ARGS");
    return;
  }

  // LS <bank> <KEY>
  if (!strncmp(line, "LS ", 3)) {
    char bank[16], key[24];
    if (sscanf(line + 3, "%15s %23s", bank, key) == 2) {
      char dirPath[96];
      path_audio(dirPath, sizeof(dirPath), bank, key, "");
      File d = SD.open(dirPath);
      if (!d || !d.isDirectory()) { DM_PRINTLN("LS:NODIR"); if (d) d.close(); return; }
      File f;
      while ((f = d.openNextFile())) {
        if (!f.isDirectory()) {
          DM_PRINT("LS:");
          DM_PRINT(f.name()); 
          DM_PRINT(" ");
          DM->println(f.size());
          DM_FLUSH(); // Ensure data is sent before continuing
          delay(10);      // Small delay to prevent buffer overflow
        }
        f.close();
      }
      d.close();
      DM_PRINTLN("LS:DONE");
    } else {
      DM_PRINTLN("ERR:ARGS");
    }
    return;
  }

  // DEL <bank> <KEY> <filename>
  if (!strncmp(line, "DEL ", 4)) {
#if DATA_WIFI_REQUIRE_AUTH
    if (!dm_authed) { DM_PRINTLN("ERR:AUTH"); return; }
#endif
#if DATA_REQUIRE_WRITE_FLAG
    if (!isWriteEnabled()) { DM_PRINTLN("ERR:WRITELOCK"); return; }
#endif
    char bank[16], key[24], fname[48];
    if (sscanf(line + 4, "%15s %23s %47s", bank, key, fname) == 3) {
      char full[128];
      path_audio(full, sizeof(full), bank, key, fname);
      if (SD.exists(full) && SD.remove(full)) DM_PRINTLN("DEL:OK"); else DM_PRINTLN("DEL:NOK");
    } else {
      DM_PRINTLN("ERR:ARGS");
    }
    return;
  }

  // GET <bank> <KEY> <filename>
  if (!strncmp(line, "GET ", 4)) {
    char bank[16], key[24], fname[48];
    if (sscanf(line + 4, "%15s %23s %47s", bank, key, fname) == 3) {
      char full[128];
      path_audio(full, sizeof(full), bank, key, fname);
      File f = SD.open(full, FILE_READ);
      if (!f) { DM_PRINTLN("GET:NOK"); return; }
      uint32_t size = f.size();

      #if DATA_USE_CRC32
      // compute CRC32 in a first pass (small files typical)
      uint32_t crc; crc32_reset(crc);
      int r;
      while ((r = f.read(dm_rbuf, sizeof(dm_rbuf))) > 0) crc32_update(crc, dm_rbuf, (size_t)r);
      f.seek(0);
      DM_PRINT("GET:SIZE "); DM->print(size); DM_PRINT(" ");
      DM->println(crc ^ 0xFFFFFFFFUL);
      #else
      DM_PRINT("GET:SIZE "); DM->println(size);
      #endif

      // stream file
      int r2;
      while ((r2 = f.read(dm_rbuf, sizeof(dm_rbuf))) > 0) {
        DM_WRITE(dm_rbuf, (size_t)r2);
      }
      f.close();
      DM_FLUSH();   // guarantee all bytes are out
      return;
    } else {
      DM_PRINTLN("ERR:ARGS");
    }
    return;
  }

  // PUT <bank> <KEY> <filename> <bytes> [crc32]
  if (!strncmp(line, "PUT ", 4)) {
#if DATA_WIFI_REQUIRE_AUTH
    if (!dm_authed) { DM_PRINTLN("ERR:AUTH"); return; }
#endif
#if DATA_REQUIRE_WRITE_FLAG
    if (!isWriteEnabled()) { DM_PRINTLN("ERR:WRITELOCK"); return; }
#endif

    char bank[16], key[24], fname[48];
    unsigned long bytes = 0; unsigned long crcHost = 0;
    int n = sscanf(line + 4, "%15s %23s %47s %lu %lu", bank, key, fname, &bytes, &crcHost);
    if (n < 4) { DM_PRINTLN("ERR:ARGS"); return; }

    // ensure directory exists
    char dirPath[96];
    path_audio(dirPath, sizeof(dirPath), bank, key, "");
    if (!mkdir_p(dirPath)) { DM_PRINTLN("ERR:MKDIR"); return; }

    // final destination
    path_audio(dm_put_final_path, sizeof(dm_put_final_path), bank, key, fname);

    // 8.3-safe temp name UPLD000.TMP..UPLD999.TMP
    for (int i = 0; i < 1000; ++i) {
      snprintf(dm_put_tmp_path, sizeof(dm_put_tmp_path), "%s/UPLD%03d.TMP", dirPath, i);
      if (!SD.exists(dm_put_tmp_path)) break;
    }
    if (SD.exists(dm_put_tmp_path)) { DM_PRINTLN("ERR:OPEN"); return; } // all taken (unlikely)

    // open temp for write
    dm_put_file = SD.open(dm_put_tmp_path, FILE_WRITE);
    if (!dm_put_file) { DM_PRINTLN("ERR:OPEN"); return; }

    dm_put_remaining = (uint32_t)bytes;
    dm_wbuf_len = 0;
    #if DATA_USE_CRC32
    dm_put_crc_host = (n >= 5) ? (uint32_t)crcHost : 0;
    crc32_reset(dm_put_crc_calc);
    #endif

    DM_PRINT("PUT:READY ");
    DM->println(DM_FLOW_BLOCK);
    DM_FLUSH();
    delay(2);
    dm_bytes_since_ack = 0;
    dm_state = DataCmdState::PUT_PAYLOAD;
    return;
  }

  // Unknown
  DM_PRINTLN("ERR:UNKNOWN");
}

// ==== SEGMENT 4: ENTER / EXIT DATA MODE ====

void enterDataMode() {
  if (deviceMode == DeviceMode::DATA_MODE) return;
  // stop any audio
  if (musicPlayer.playingMusic) musicPlayer.stopPlaying();
  isPlaying = false;

  deviceMode = DeviceMode::DATA_MODE;
  dm_state = DataCmdState::LINE;
  dm_line_reset();
  dm_last_activity_ms = millis();

  Serial.println("[DATA] mode=ENTER");
  // Optional: short audio cue if you want (ensure file exists):
  // playAudioForKey("SHIFT", 2);
}

void exitDataMode() {
  if (deviceMode == DeviceMode::NORMAL) return;

  // close any half-done PUT
  if (dm_state == DataCmdState::PUT_PAYLOAD) {
    if (dm_put_file) dm_put_file.close();
    if (strlen(dm_put_tmp_path)) SD.remove(dm_put_tmp_path);
    dm_bytes_since_ack = 0;
    dm_state = DataCmdState::LINE;
  }

  if (dm_get_file) { dm_get_file.close(); }

  deviceMode = DeviceMode::NORMAL;
  Serial.println("[DATA] mode=EXIT");
  // Optional: audio cue
  // playAudioForKey("SHIFT", 3);
}

// ==== WIFI CONFIGURATION LOADING ====

// /CONFIG/WIFI.CFG format (lines, no quotes):
// SSID=your_network
// PASS=your_password
// TOKEN=optionalWriteToken     (if DATA_WIFI_REQUIRE_AUTH=1)
static void wifiLoadCfg() {
  File f = SD.open("/CONFIG/WIFI.CFG", FILE_READ);
  if (!f) { Serial.println(F("[WIFI] WIFI.CFG not found; will use SoftAP")); return; }
  while (f.available()) {
    String ln = f.readStringUntil('\n'); ln.trim();
    if (!ln.length() || ln.startsWith("#")) continue;
    int eq = ln.indexOf('='); if (eq < 0) continue;
    String k = ln.substring(0,eq); k.trim(); k.toUpperCase();
    String v = ln.substring(eq+1); v.trim();
    if (k=="SSID")  v.toCharArray(WIFI_SSID, sizeof(WIFI_SSID));
    if (k=="PASS")  v.toCharArray(WIFI_PASS, sizeof(WIFI_PASS));
    if (k=="TOKEN") v.toCharArray(WIFI_TOKEN, sizeof(WIFI_TOKEN));
  }
  f.close();
  Serial.println(F("[WIFI] WIFI.CFG loaded"));
}

static bool startSTA() {
  if (WIFI_SSID[0] == '\0') return false;
  Serial.print(F("[WIFI] STA connect → ")); Serial.println(WIFI_SSID);
  WiFi.begin(WIFI_SSID, WIFI_PASS);
  unsigned long t0 = millis();
  while (WiFi.status() != WL_CONNECTED && millis() - t0 < 15000) { delay(250); Serial.print("."); }
  Serial.println();
  if (WiFi.status() == WL_CONNECTED) {
    Serial.print(F("[WIFI] STA OK, IP: ")); Serial.println(WiFi.localIP());
    return true;
  }
  Serial.println(F("[WIFI] STA failed; fallback to SoftAP"));
  return false;
}

static bool startAP() {
  // SSID fallback if none in WIFI.CFG
  const char* apSsid = (WIFI_SSID[0] ? WIFI_SSID : "TCD-Device");
  const char* apPass = (WIFI_PASS[0] ? WIFI_PASS : "tcd12345"); // 8+ chars for WPA2
  Serial.print(F("[AP] Starting SoftAP '")); Serial.print(apSsid); Serial.println(F("'"));
  // Channel 6 by default; WPA2 by default
  if (WiFi.beginAP(apSsid, apPass) != WL_AP_LISTENING) {
    Serial.println(F("[AP] Begin failed"));
    return false;
  }
  // Typical default AP LAN: 192.168.4.1
  delay(1000);
  IPAddress apIP = WiFi.localIP();
  Serial.print(F("[AP] Ready. Connect to ")); Serial.print(apSsid);
  Serial.print(F(" → IP ")); Serial.println(apIP);
  return true;
}

// ==== WiFi Toggle Helpers (AP-only) ====
void wifiEnableAP() {
#if ENABLE_WIFI_DATA_MODE
  if (wifiEnabled) { Serial.println(F("[NET] Wi-Fi already ON")); return; }
  if (!startAP()) { Serial.println(F("[NET] Wi-Fi enable failed")); return; }
  // Start servers
  dataSrv.begin();
  Serial.print(F("[NET] DataMode TCP server on port ")); Serial.println(DATA_TCP_PORT);
#if ENABLE_HTTP_BROWSER
  httpSrv.begin();
  Serial.print(F("[HTTP] Web UI on http://")); Serial.print(WiFi.localIP()); Serial.println(F("/"));
#endif
  wifiEnabled = true;
  wifiTouchActivity();
  // Play "WiFi on" announcement
  if (musicPlayer.startPlayingFile("/ANNOUNCE/WIFI_ON.MP3")) {
    Serial.println(F("[AUDIO] Playing WiFi ON announcement"));
  } else {
    Serial.println(F("[AUDIO] WiFi ON file not found, using sine tone"));
    musicPlayer.sineTest(0x44, 120);
  }
#endif
}

void wifiDisable() {
#if ENABLE_WIFI_DATA_MODE
  if (!wifiEnabled) { Serial.println(F("[NET] Wi-Fi already OFF")); return; }
  // Stop any active client
  if (dataCli && dataCli.connected()) dataCli.stop();
  // There is no WiFiServer::end(); we simply stop accepting and turn off radio
  WiFi.end();
  wifiEnabled = false;
  Serial.println(F("[NET] Wi-Fi disabled"));
  // Play "WiFi off" announcement
  if (musicPlayer.startPlayingFile("/ANNOUNCE/WIFI_OFF.MP3")) {
    Serial.println(F("[AUDIO] Playing WiFi OFF announcement"));
  } else {
    Serial.println(F("[AUDIO] WiFi OFF file not found, using sine tone"));
    musicPlayer.sineTest(0x32, 150);
  }
#endif
}

void wifiToggle() {
#if ENABLE_WIFI_DATA_MODE
  if (wifiEnabled) wifiDisable(); else wifiEnableAP();
#endif
}

// ==== NEW LSP AND TREE COMMANDS ====

// List arbitrary directory (non-recursive)
static void listPath(const char* path) {
  File dir = SD.open(path);
  if (!dir || !dir.isDirectory()) { DM_PRINTLN("LS:NODIR"); if (dir) dir.close(); return; }
  File e;
  while ((e = dir.openNextFile())) {
    if (e.isDirectory()) {
      DM_PRINT("LS:"); DM_PRINT(e.name()); DM_PRINTLN("/");
    } else {
      DM_PRINT("LS:"); DM_PRINT(e.name()); DM_PRINT(" "); DM->println(e.size());
    }
    e.close();
  }
  dir.close();
  DM_PRINTLN("LS:DONE");
}

// Recursive tree (depth-limited)
static void treeWalk(const char* base, uint8_t depth, uint8_t maxDepth) {
  if (depth > maxDepth) return;
  File dir = SD.open(base);
  if (!dir || !dir.isDirectory()) { if (dir) dir.close(); return; }
  File e;
  while ((e = dir.openNextFile())) {
    String name = String(e.name());
    DM_PRINT("TREE:"); DM->print(depth); DM_PRINT(" "); DM_PRINT(base); DM_PRINT("/");
    DM_PRINTLN(name.c_str());
    if (e.isDirectory()) {
      String next = String(base) + "/" + name;
      e.close();
      treeWalk(next.c_str(), depth+1, maxDepth);
    } else {
      e.close();
    }
  }
  dir.close();
}

// Built-in sine wave test (no SD card required)
void saveCalibrationToSD() {
  Serial.println(F("[SAVE] Saving calibration to SD card..."));
  
  // Ensure CONFIG directory exists
  if (!SD.exists("/CONFIG")) {
    if (!SD.mkdir("/CONFIG")) {
      Serial.println(F("[SAVE] ERROR: Could not create /CONFIG directory"));
      return;
    }
  }
  
  // Open file for writing
  File csvFile = SD.open("/CONFIG/KEYS.CSV", FILE_WRITE | O_TRUNC);
  if (!csvFile) {
    Serial.println(F("[SAVE] ERROR: Could not open /CONFIG/KEYS.CSV for writing"));
    return;
  }
  
  // Write CSV header
  csvFile.println(F("# Button mapping configuration from calibration session"));
  csvFile.println(F("# Maps logical keys to their descriptions and hardware assignments"));
  csvFile.println(F("KEY,DESCRIPTION,INPUT"));
  
  // Write mapped buttons
  uint16_t savedMappings = 0;
  for (uint8_t i = 0; i < TOTAL_BUTTONS; i++) {
    if (buttonMap[i].used && buttonMap[i].keyIndex >= 0) {
      const char* keyName = keys[buttonMap[i].keyIndex].key;
      
      // Generate hardware input string (pcfX:Y format)
      char inputStr[16];
      if (i < TOTAL_EXPANDER_PINS) {
        uint8_t chipIndex = i / 16;
        uint8_t pin = i % 16;
        snprintf(inputStr, sizeof(inputStr), "pcf%d:%d", chipIndex, pin);
      } else {
        // Extra pins
        uint8_t extraIndex = i - TOTAL_EXPANDER_PINS;
        snprintf(inputStr, sizeof(inputStr), "extra:%d", extraIndex);
      }
      
      // Write CSV line: KEY,DESCRIPTION,INPUT
      csvFile.print(keyName);
      csvFile.print(F(","));
      csvFile.print(F("Letter ")); // Simple description
      csvFile.print(keyName);
      csvFile.print(F(","));
      csvFile.println(inputStr);
      
      savedMappings++;
    }
  }
  
  csvFile.close();
  
  Serial.print(F("[SAVE] SUCCESS: Saved "));
  Serial.print(savedMappings);
  Serial.println(F(" button mappings to /CONFIG/KEYS.CSV"));
  Serial.println(F("[SAVE] Restart device to load new configuration"));
}

void playSineTest() {
  Serial.println(F("[SINE] Starting built-in sine test (250ms)..."));
  
  // Use VS1053's built-in sine test mode
  // This sends the magic byte sequence to trigger internal sine generation
  musicPlayer.sineTest(0x44, 250);  // 1000 Hz tone for 250ms
  
  Serial.println(F("[SINE] Sine test complete - VS1053 audio verified"));
}

#if ENABLE_HTTP_BROWSER
// ============================================================================
// HTTP WEB INTERFACE IMPLEMENTATION
// ============================================================================

static String urlDecode(const String& s) {
  String out; out.reserve(s.length());
  for (uint16_t i=0;i<s.length();++i){
    char c=s[i];
    if (c=='%' && i+2<s.length()) {
      char h1=s[++i], h2=s[++i];
      auto hex=[&](char h){ if(h>='0'&&h<='9')return h-'0'; h|=32; return 10+(h-'a');};
      out += (char)((hex(h1)<<4)|hex(h2));
    } else if (c=='+') out+=' ';
    else out+=c;
  }
  return out;
}

static String dirName(const String& full) {
  int s = full.lastIndexOf('/'); return (s > 0) ? full.substring(0, s) : String("/");
}
static String baseName(const String& full) {
  int s = full.lastIndexOf('/'); return (s >= 0) ? full.substring(s + 1) : full;
}
static String pathJoin(const String& a, const String& b) {
  return a.endsWith("/") ? (a + b) : (a + "/" + b);
}
static bool isDirPath(const String& p) {
  File d = SD.open(p.c_str()); bool ok = d && d.isDirectory(); if (d) d.close(); return ok;
}

// crude 8.3 guesser to help match long names to short names (UPLOAD~1.MP3)
static String to83(const String& name) {
  auto clean = [](String s, int maxLen) {
    String o; o.reserve(maxLen);
    for (uint16_t i=0;i<s.length() && (int)o.length()<maxLen;i++){
      char c=s[i]; if (c==' ') c='_';
      if ((c>='a'&&c<='z')) c-=32; // upper
      if ((c>='A'&&c<='Z')||(c>='0'&&c<='9')||c=='_') o+=c;
    }
    while ((int)o.length()<maxLen) o+='_';
    return o;
  };
  int dot=name.lastIndexOf('.');
  String n = (dot>=0)? name.substring(0,dot): name;
  String e = (dot>=0)? name.substring(dot+1): "";
  String ext = clean(e,3);
  String base;
  if ((int)n.length()<=8) base = clean(n, (int)min(8,(int)n.length()));
  else                    base = clean(n,6) + "~1";
  return ext.length()? (base + "." + ext) : base;
}

static bool sd_remove_relaxed(const String& path) {
  // free SD if playing
  if (musicPlayer.playingMusic) { musicPlayer.stopPlaying(); isPlaying=false; }

  // direct try
  if (SD.exists(path.c_str())) {
    File f = SD.open(path.c_str());
    if (f) {
      if (!f.isDirectory()) { f.close(); return SD.remove(path.c_str()); }
      f.close();
      // (optional) implement recursive dir delete here if you want
      return false; // directory delete not supported in this minimal helper
    }
  }

  // try matching by scanning parent directory (case-insensitive and 8.3 guess)
  String dir  = dirName(path);
  String want = baseName(path);
  File d = SD.open(dir.c_str());
  if (!d || !d.isDirectory()) { if (d) d.close(); return false; }

  File e; bool ok=false;
  while ((e = d.openNextFile())) {
    String onDisk = e.name();   // typically 8.3 upper on FAT
    bool match = onDisk.equalsIgnoreCase(want) || onDisk.equalsIgnoreCase(to83(want));
    if (match && !e.isDirectory()) {
      String real = pathJoin(dir, onDisk);
      e.close(); d.close();
      return SD.remove(real.c_str());
    }
    e.close();
  }
  d.close();
  // final brute guess: remove using guessed 8.3
  String guess = pathJoin(dir, to83(want));
  return SD.exists(guess.c_str()) ? SD.remove(guess.c_str()) : false;
}

static bool parseRequest(WiFiClient &cli, HttpReq &r) {
  unsigned long dead=millis()+8000;
  String line;
  while (cli.connected() && millis()<dead) {
    if (!cli.available()) { delay(1); continue; }
    line = cli.readStringUntil('\n'); line.trim();
    if (r.method.length()==0) {
      // "GET /path?x=y HTTP/1.1"
      int sp1=line.indexOf(' '), sp2=line.indexOf(' ', sp1+1);
      if (sp1<0||sp2<0) return false;
      r.method = line.substring(0, sp1);
      String full = line.substring(sp1+1, sp2);
      int q = full.indexOf('?');
      r.path  = (q>=0) ? full.substring(0,q) : full;
      r.query = (q>=0) ? full.substring(q+1) : "";
    } else if (line.length()==0) {
      // end headers
      return true;
    } else {
      String L=line; L.toLowerCase();
      if (L.startsWith("content-length:")) r.contentLen = line.substring(15).toInt();
      if (L.startsWith("authorization:"))  r.auth = line.substring(line.indexOf(' ')+1);
    }
  }
  return false;
}

static bool authOK(const String& query, const String& auth) {
#if DATA_WIFI_REQUIRE_AUTH
  if (WIFI_TOKEN[0]=='\0') return false;
  // Expect "Bearer <token>" OR token=... in query
  if (auth.startsWith("Bearer ")) {
    String tok = auth.substring(7); tok.trim();
    return (tok == WIFI_TOKEN);
  }
  int pos = query.indexOf("token=");
  if (pos>=0) {
    String tok = query.substring(pos+6);
    int amp = tok.indexOf('&'); if (amp>=0) tok = tok.substring(0,amp);
    tok = urlDecode(tok);
    return (tok == WIFI_TOKEN);
  }
  return false;
#else
  (void)query; (void)auth; return true;
#endif
}

static void httpHead(WiFiClient& c, int code, const char* mime="text/plain") {
  c.print(F("HTTP/1.1 ")); c.print(code); c.println(code==200?" OK":"");
  c.println(F("Connection: close"));
  c.print  (F("Content-Type: ")); c.println(mime);
}

static void httpJson(WiFiClient& c, int code, const String& body) {
  httpHead(c, code, "application/json; charset=utf-8");
  c.print  (F("Content-Length: ")); c.println(body.length());
  c.println(); c.print(body);
}

static void httpText(WiFiClient& c, int code, const String& body) {
  httpHead(c, code, "text/plain; charset=utf-8");
  c.print  (F("Content-Length: ")); c.println(body.length());
  c.println(); c.print(body);
}

static bool queryParam(const String& q, const char* key, String& out) {
  String k = String(key) + "=";
  int i=q.indexOf(k); if(i<0) return false;
  int j=q.indexOf('&', i+k.length());
  out = urlDecode(q.substring(i+k.length(), j<0? q.length(): j));
  return true;
}

static void api_ls(WiFiClient& c, const String& path) {
  File d = SD.open(path.c_str());
  if (!d || !d.isDirectory()) { if(d) d.close(); return httpJson(c,404,"{\"err\":\"not_dir\"}"); }
  String out = "["; bool first=true;
  for (;;) {
    File e = d.openNextFile();
    if (!e) break;
    if (!first) out += ",";
    first=false;
    out += "{\"n\":\""; out += e.name(); out += "\",\"t\":\"";
    out += e.isDirectory()? "D":"F"; out += "\"";
    if (!e.isDirectory()) { out += ",\"s\":"; out += String(e.size()); }
    out += "}";
    e.close();
    if (out.length()>1800) { /* simple guard */ }
  }
  d.close();
  out += "]";
  httpJson(c,200,out);
}

static void api_get(WiFiClient& c, const String& path) {
  File f = SD.open(path.c_str(), FILE_READ);
  if (!f) return httpJson(c,404,"{\"err\":\"no_file\"}");

  // (Optional) stop audio so SD/SPI is free
  if (musicPlayer.playingMusic) { musicPlayer.stopPlaying(); isPlaying=false; }

  httpHead(c,200,"application/octet-stream");
  String fname = path; int slash=fname.lastIndexOf('/'); if(slash>=0) fname=fname.substring(slash+1);
  c.print(F("Content-Disposition: attachment; filename=\"")); c.print(fname); c.println(F("\""));
  c.println(F("Cache-Control: no-store"));
  c.print(F("Content-Length: ")); c.println(f.size());
  c.println();

  // Use a larger I/O buffer to match Wi-Fi MTU-ish sizes
  static uint8_t buf[1460];
  int r; uint32_t sent=0, total=f.size(), last=0;
  unsigned long t0=millis();

  while ((r=f.read(buf,sizeof(buf)))>0) {
    c.write(buf,(size_t)r);
    sent += (uint32_t)r;
    if (sent - last >= PROG_STEP_BYTES) { logProgress("[HTTP GET]", sent, total, t0); last = sent; }
  }
  f.close();
  logProgress("[HTTP GET]", sent, total, t0);
}

static void api_del(WiFiClient& c, const String& rawPath) {
  String p = rawPath; // already urlDecoded by caller
  Serial.print(F("[HTTP DEL] ")); Serial.println(p);
  if (sd_remove_relaxed(p)) return httpJson(c,200,"{\"ok\":true}");
  httpJson(c,404,"{\"err\":\"del_failed\"}");
}

static void api_put(WiFiClient& c, WiFiClient& src, const HttpReq& r, const String& rawPath) {
  if (r.contentLen <= 0) return httpJson(c,400,"{\"err\":\"no_content\"}");

  String finalPath = rawPath;   // already urlDecoded by caller
  String nameParam;
  bool haveName = queryParam(r.query, "name", nameParam);

  // Stop audio so SD/SPI is free
  if (musicPlayer.playingMusic) { musicPlayer.stopPlaying(); isPlaying=false; }

  // Allow "upload to directory": if path ends with '/' OR is an existing dir, require ?name=
  if (finalPath.endsWith("/") || isDirPath(finalPath)) {
    if (!haveName || nameParam.length()==0) return httpJson(c,400,"{\"err\":\"need_name\"}");
    finalPath = pathJoin(finalPath, nameParam);
  }

  // Console logging for diagnostics
  Serial.print(F("[HTTP PUT] path=")); Serial.print(finalPath);
  Serial.print(F(" len=")); Serial.println(r.contentLen);

  // Ensure parent directory exists
  String parent = dirName(finalPath);
  if (!mkdir_p(parent.c_str())) return httpJson(c,500,"{\"err\":\"mkdir_p\"}");

  // 8.3-safe temp file in the parent folder
  String tmp;
  for (int i = 0; i < 1000; ++i) {
    char buf[64];
    snprintf(buf, sizeof(buf), "%s/UPLD%03d.TMP", parent.c_str(), i);
    if (!SD.exists(buf)) { tmp = buf; break; }
  }
  if (!tmp.length()) return httpJson(c,500,"{\"err\":\"open_failed\"}");
  File f = SD.open(tmp.c_str(), FILE_WRITE);
  if (!f) return httpJson(c,500,"{\"err\":\"open_failed\"}");

  // Stream request body → temp
  uint8_t buf[1460];
  int left = r.contentLen;
  uint32_t got=0, last=0; unsigned long t0=millis();
  while (left > 0) {
    while (!src.available()) { delay(1); }
    int chunk = src.read(buf, (left > (int)sizeof(buf) ? (int)sizeof(buf) : left));
    if (chunk <= 0) { f.close(); SD.remove(tmp.c_str()); return httpJson(c,500,"{\"err\":\"read_timeout\"}"); }
    if (f.write(buf, (size_t)chunk) != (size_t)chunk) { f.close(); SD.remove(tmp.c_str()); return httpJson(c,500,"{\"err\":\"sd_write\"}"); }
    left -= chunk; got += (uint32_t)chunk;
    if (got - last >= PROG_STEP_BYTES) { logProgress("[HTTP PUT ]", got, (uint32_t)r.contentLen, t0); last = got; }
  }
  logProgress("[HTTP PUT ]", got, (uint32_t)r.contentLen, t0);
  f.flush(); f.close();

  // Finalize: copy temp → final (Sd lib lacks atomic rename)
  if (SD.exists(finalPath.c_str())) SD.remove(finalPath.c_str());
  File srcFile = SD.open(tmp.c_str(), FILE_READ);
  if (!srcFile) { SD.remove(tmp.c_str()); return httpJson(c,500,"{\"err\":\"rename_src\"}"); }
  File dst = SD.open(finalPath.c_str(), FILE_WRITE);
  if (!dst) { srcFile.close(); SD.remove(tmp.c_str()); return httpJson(c,500,"{\"err\":\"rename_dst\"}"); }
  uint8_t rbuf[256]; int rr;
  while ((rr = srcFile.read(rbuf, sizeof(rbuf))) > 0) dst.write(rbuf, (size_t)rr);
  srcFile.close(); dst.close();
  SD.remove(tmp.c_str());

  httpJson(c,200,"{\"ok\":true}");
}

// Minimal built-in page (use /WWW/index.html on SD to override)
static const char INDEX_HTML[] PROGMEM =
"<!doctype html><meta name=viewport content='width=device-width,initial-scale=1'>"
"<title>TCD SD Browser</title><style>body{font:14px system-ui;margin:16px}table{border-collapse:collapse;width:100%}"
"td,th{border:1px solid #ccc;padding:6px}input,button{padding:6px;margin:4px}</style>"
"<h1>SD Browser</h1><div><input id=p value='/' size=40>"
"<button onclick='ls()'>List</button></div>"
"<table id=t><tr><th>Name</th><th>Type</th><th>Size</th><th>Actions</th></tr></table>"
"<h3>Upload</h3><input type=file id=f><button onclick='up()'>Upload to current path</button>"
"<script>"
"let tok=''; try{tok=new URL(location).searchParams.get('token')||'';}catch(e){}"
"function esc(s){return s.replace(/&/g,'&amp;').replace(/</g,'&lt;')}"
"function ls(){"
"  fetch('/api/ls?path='+encodeURIComponent(p.value)+(tok?'&token='+tok:''))"
"  .then(r=>r.json()).then(js=>{"
"    let h='<tr><th>Name</th><th>Type</th><th>Size</th><th>Actions</th></tr>';"
"    js.forEach(o=>{"
"      let full=p.value.replace(/\\/$/,'')+'/'+o.n;"
"      h+=`<tr>"
"        <td>${esc(o.n)}</td>"
"        <td>${o.t}</td>"
"        <td>${o.s||''}</td>"
"        <td>"
"          ${o.t==='F'"
"            ? `<button onclick=\"download('${full}')\">Download</button> <a href='#' onclick=\"delFile('${full}')\">Delete</a>`"
"            : `<button onclick=\"openDir('${full}')\">Open</button>`}"
"        </td>"
"      </tr>`;"
"    });"
"    t.innerHTML=h;"
"  });"
"}"
"function openDir(d){ p.value=d; ls(); }"
"async function download(full){"
"  const url = `/api/get?path=${encodeURIComponent(full)}${tok?`&token=${tok}`:''}`;"
"  console.log('[GET] starting', full);"
"  const res = await fetch(url);"
"  if (!res.ok) { console.error('[GET] HTTP', res.status); return; }"
"  const total = +res.headers.get('Content-Length') || 0;"
"  const reader = res.body.getReader();"
"  let received = 0; const chunks = [];"
"  const t0 = performance.now();"
"  for(;;){"
"    const {value, done} = await reader.read();"
"    if (done) break;"
"    chunks.push(value);"
"    received += value.length;"
"    const secs = (performance.now()-t0)/1000;"
"    const mbps = secs>0 ? (received/1024/1024)/secs : 0;"
"    if (total) console.log(`[GET] ${full} ${received}/${total} ${(100*received/total).toFixed(1)}% @ ${mbps.toFixed(2)} MB/s`);"
"    else       console.log(`[GET] ${full} ${received} bytes @ ${mbps.toFixed(2)} MB/s`);"
"  }"
"  const blob = new Blob(chunks, {type:'application/octet-stream'});"
"  const a = document.createElement('a');"
"  a.href = URL.createObjectURL(blob);"
"  a.download = full.split('/').pop();"
"  a.click();"
"  URL.revokeObjectURL(a.href);"
"  console.log('[GET] done', full);"
"}"
"function delFile(full){"
"  if(!confirm('Delete '+full+'?')) return;"
"  fetch('/api/del?path='+encodeURIComponent(full)+(tok?'&token='+tok:''))"
"    .then(_=>ls());"
"}"
"function up(){"
"  const file=f.files[0];"
"  if(!file){ alert('Pick a file'); return; }"
"  const full=p.value.replace(/\\/$/,'')+'/'+file.name;"
"  const url = `/api/put?path=${encodeURIComponent(full)}${tok?`&token=${tok}`:''}`;"
"  console.log('[PUT] starting', full, file.size, 'bytes');"
"  const xhr = new XMLHttpRequest();"
"  xhr.open('POST', url);"
"  xhr.upload.onprogress = (e)=>{"
"    if(e.lengthComputable){"
"      const pct = (100*e.loaded/e.total).toFixed(1);"
"      const secs = e.timeStamp/1000;"
"      const mbps = secs>0 ? (e.loaded/1024/1024)/secs : 0;"
"      console.log(`[PUT] ${e.loaded}/${e.total} ${pct}% @ ${mbps.toFixed(2)} MB/s`);"
"    } else {"
"      console.log(`[PUT] ${e.loaded} bytes`);"
"    }"
"  };"
"  xhr.onload = ()=>{ console.log('[PUT] done', xhr.status, xhr.responseText); ls(); };"
"  xhr.onerror = ()=>{ console.error('[PUT] error'); };"
"  xhr.send(file);"
"}"
"ls();"
"</script>";

static void serve_index(WiFiClient& c) {
  // If /WWW/index.html exists on SD, serve that; else built-in
  File idx = SD.open("/WWW/index.html");
  if (idx) {
    httpHead(c,200,"text/html; charset=utf-8");
    c.print(F("Cache-Control: no-store\r\n\r\n"));
    uint8_t buf[512]; int r;
    while ((r=idx.read(buf,sizeof(buf)))>0) c.write(buf,(size_t)r);
    idx.close();
  } else {
    String body((__FlashStringHelper*)INDEX_HTML);
    httpHead(c,200,"text/html; charset=utf-8");
    c.print(F("Cache-Control: no-store\r\nContent-Length: "));
    c.println(body.length());
    c.println(); c.print(body);
  }
}

static void handleHttpClient(WiFiClient& cli) {
  wifiTouchActivity();
  HttpReq r; if (!parseRequest(cli, r)) { cli.stop(); return; }
  // Routing
  if (r.method=="GET" && (r.path=="/" || r.path=="/index.html")) { serve_index(cli); cli.stop(); return; }

  // API requires auth for mutations; listing/download can be read-only if you prefer
  if (r.path=="/api/ls" && r.method=="GET") {
    String path="/"; queryParam(r.query,"path",path); path = urlDecode(path);
    api_ls(cli, path); cli.stop(); return;
  }

  if (r.path=="/api/get" && r.method=="GET") {
    String path=""; if(!queryParam(r.query,"path",path)) { httpJson(cli,400,"{\"err\":\"args\"}"); cli.stop(); return; }
    api_get(cli, urlDecode(path)); cli.stop(); return;
  }

  if (r.path=="/api/del" && r.method=="GET") { // (GET for simplicity; could be DELETE)
    if (!authOK(r.query, r.auth)) { httpJson(cli,401,"{\"err\":\"auth\"}"); cli.stop(); return; }
    String path=""; if(!queryParam(r.query,"path",path)) { httpJson(cli,400,"{\"err\":\"args\"}"); cli.stop(); return; }
    api_del(cli, urlDecode(path)); cli.stop(); return;
  }

  if (r.path=="/api/put" && r.method=="POST") {
    if (!authOK(r.query, r.auth)) { httpJson(cli,401,"{\"err\":\"auth\"}"); cli.stop(); return; }
    String path=""; if(!queryParam(r.query,"path",path)) { httpJson(cli,400,"{\"err\":\"args\"}"); cli.stop(); return; }
    api_put(cli, cli, r, urlDecode(path)); cli.stop(); return;
  }

  httpText(cli,404,"not found"); cli.stop();
}

#endif // ENABLE_HTTP_BROWSER
