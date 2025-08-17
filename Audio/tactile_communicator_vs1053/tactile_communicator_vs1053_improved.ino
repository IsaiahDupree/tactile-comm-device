/*
 * Tactile Communication Device - Improved SD-Defined System
 * 
 * FEATURES:
 * - Complete hardware-software decoupling via SD card configuration
 * - Strict human/generated audio separation with playlist-enforced ordering
 * - Support for up to 3 PCF8575 expanders (48 buttons + 4 GPIO = 52 total)
 * - Desktop app compatible with versioned manifest system
 * - Zero code changes needed for hardware modifications or content updates
 * - Arduino-compatible (no STL containers that cause compilation issues)
 * 
 * SD CARD LAYOUT (STRICT):
 * /config/
 *   mode.cfg                # Global priority settings
 *   buttons.csv             # Physical input → logical key mapping
 * /mappings/
 *   playlists/
 *     {KEY}_human.m3u       # REQUIRED: Human recording playlists
 *     {KEY}_generated.m3u   # REQUIRED: Generated audio playlists
 * /audio/
 *   human/{KEY}/001.mp3     # Human recordings by key
 *   generated/{KEY}/001.mp3 # Generated audio by key
 * /state/cursors.json       # Optional: playback position persistence
 * /manifest.json            # Optional: desktop app contract
 */

#include <SPI.h>
#include <SD.h>
#include <Wire.h>
#include <EEPROM.h>
#include "Adafruit_PCF8575.h"
#include "Adafruit_VS1053.h"

// ---- helpers/macros & forward declarations ----
#ifndef STRINGIFY
#define STRINGIFY_HELPER(x) #x
#define STRINGIFY(x) STRINGIFY_HELPER(x)
#endif

// Forward declarations for functions referenced before definition
bool stringEquals(const char* a, const char* b);
bool loadPlaylistsForKey(const char* key);
const char* nextTrackForKey(const char* key);
void saveCursors();
void loadCursors();

// ===== HARDWARE CONFIGURATION =====
#define FIRMWARE_VERSION    "1.0.0"
#define MANIFEST_SCHEMA_VER 1
#define VS1053_RESET   -1
#define VS1053_CS       7
#define VS1053_DCS      6
#define CARDCS          4
#define VS1053_DREQ     3

Adafruit_VS1053_FilePlayer musicPlayer = 
  Adafruit_VS1053_FilePlayer(VS1053_RESET, VS1053_CS, VS1053_DCS, VS1053_DREQ, CARDCS);

// PCF8575 I2C port expanders (up to 3 supported)
#define NUM_PCF 3
#define MAX_BUTTONS 52
Adafruit_PCF8575 pcf[NUM_PCF];
const uint8_t PCF_ADDR[NUM_PCF] = {0x20, 0x21, 0x22};
uint16_t last_state[NUM_PCF];

// Extra Arduino pins
const uint8_t extraPins[] = {8, 9, 2, 5};
const uint8_t EXTRA_COUNT = sizeof(extraPins) / sizeof(extraPins[0]);
bool lastExtra[EXTRA_COUNT];

// ===== PRIORITY SYSTEM =====
enum Priority : uint8_t {
  HUMAN_FIRST = 0,
  GENERATED_FIRST = 1
};

Priority globalPriority = HUMAN_FIRST;
bool strictPlaylists = true;
const char* FALLBACK_CLIP = "/audio/generated/SYSTEM/missing.mp3"; // optional fallback announcement

// ===== DATA STRUCTURES (Arduino-compatible) =====
struct ButtonMap {
  char inputId[16];     // "pcf0:15", "gpio:8"
  char key[16];         // "A", ".", "Water"
  bool used;
};

struct PlaylistEntry {
  char path[64];
};

struct Playlists {
  PlaylistEntry human[16];
  PlaylistEntry generated[16];
  uint8_t humanCount;
  uint8_t generatedCount;
};

struct PlayCursor {
  uint8_t humanIdx;
  uint8_t generatedIdx;
};

// ===== GLOBAL STATE =====
ButtonMap buttons[MAX_BUTTONS];
uint8_t buttonCount = 0;

#define MAX_KEYS 24
// Lightweight per-key cursor table (no large playlist storage per key)
struct KeyCursorEntry {
  char key[16];
  PlayCursor cursor;
  bool used;
};
KeyCursorEntry keyCursors[MAX_KEYS];
uint8_t keyCursorCount = 0;

// Single active playlist cache for the currently accessed key
Playlists activePlaylists;
char activeKey[16] = "";
bool activeLoaded = false;

// Period triple-press for priority toggle
uint8_t periodPressCount = 0;
unsigned long periodWindowStart = 0;
const unsigned long PERIOD_WINDOW_MS = 1200;

// Audio state
bool isPlaying = false;
char currentTrackPath[64] = "";
const int EEPROM_ADDR_MODE = 0;
// Cursor save debounce
unsigned long lastCursorSaveMs = 0;
const unsigned long CURSOR_SAVE_INTERVAL_MS = 750;
bool cursorDirty = false;
// Special select key label (used for future behaviors if needed)
const char* SPECIAL_SELECT_KEY = "hello_how_are_you"; // filename-safe label; front panel can read "hello how are you?"

// Phase 4: Multi-press selection (per-key aggregation window)
char pendingKey[16] = "";
uint8_t pendingCount = 0;
unsigned long pendingWindowStart = 0;
bool hasPending = false;
const unsigned long PRESS_WINDOW_MS = 350; // tune as needed

// ===== UTILITY FUNCTIONS =====
void copyString(char* dest, const char* src, size_t maxLen) {
  strncpy(dest, src, maxLen - 1);
  dest[maxLen - 1] = '\0';
}

// ===== PLAYBACK HELPERS =====
static void playTrackForKey(const char* key, const char* inPath, bool allowFallback) {
  if (!inPath) return;
  const char* track = inPath;
  if (!SD.exists(track)) {
    Serial.print(F("[MISSING] ")); Serial.println(track);
    if (allowFallback && SD.exists(FALLBACK_CLIP)) {
      track = FALLBACK_CLIP;
      Serial.println(F("[FALLBACK] Playing system clip"));
    } else {
      return;
    }
  }
  Serial.print(F("[PLAY] ")); Serial.print(key); Serial.print(F(": ")); Serial.println(track);
  if (isPlaying) { musicPlayer.stopPlaying(); isPlaying = false; }
  if (musicPlayer.startPlayingFile(track)) { isPlaying = true; copyString(currentTrackPath, track, sizeof(currentTrackPath)); }
}

// Select Nth (0-based index) item from current priority playlist without touching cursors
static const char* selectTrackByIndexForKey(const char* key, uint8_t index) {
  if (!loadPlaylistsForKey(key)) return nullptr;
  Playlists &pl = activePlaylists;
  // Try priority playlist first, then fallback to the other if index fits there
  if (globalPriority == HUMAN_FIRST) {
    if (index < pl.humanCount) return pl.human[index].path;
    if (index < pl.generatedCount) return pl.generated[index].path;
  } else {
    if (index < pl.generatedCount) return pl.generated[index].path;
    if (index < pl.humanCount) return pl.human[index].path;
  }
  return nullptr;
}

// Finalize any pending multi-press selection (called from loop or when switching keys)
static void finalizePendingSelection() {
  if (!hasPending) return;
  const char* key = pendingKey;
  uint8_t count = pendingCount;
  hasPending = false;
  pendingKey[0] = '\0';
  pendingCount = 0;
  // Single press: legacy behavior advances cursor
  if (count <= 1) {
    const char* track = nextTrackForKey(key);
    playTrackForKey(key, track, /*allowFallback=*/true);
    return;
  }
  // Multi-press: select by count without advancing cursor
  uint8_t selIdx = (count - 1);
  const char* track = selectTrackByIndexForKey(key, selIdx);
  if (!track) {
    // Out of range -> fallback if available
    if (SD.exists(FALLBACK_CLIP)) {
      playTrackForKey(key, FALLBACK_CLIP, /*allowFallback=*/false);
    }
    return;
  }
  playTrackForKey(key, track, /*allowFallback=*/true);
}

// Emit a single JSON validation report with integrity checks
void emitValidationReport() {
  bool hasManifest = SD.exists("/manifest.json");
  bool schemaOk = false;
  if (hasManifest) {
    File f = SD.open("/manifest.json", FILE_READ);
    if (f) {
      String content; while (f.available()) content += (char)f.read(); f.close();
      // Prefer direct string match using STRINGIFY, with a safe numeric fallback
      String want = String("\"schemaVersion\":") + STRINGIFY(MANIFEST_SCHEMA_VER);
      if (content.indexOf(want) >= 0) {
        schemaOk = true;
      } else {
        // naive schema check: look for the integer literal
        char buf[8];
        itoa(MANIFEST_SCHEMA_VER, buf, 10);
        schemaOk = (content.indexOf(String("\"schemaVersion\":") + buf) >= 0);
      }
    }
  }
  bool hasButtons = SD.exists("/config/buttons.csv");
  bool hasFallback = SD.exists(FALLBACK_CLIP);

  // Begin JSON
  Serial.print(F("{\"schema\":")); Serial.print(MANIFEST_SCHEMA_VER); Serial.print(F(","));
  Serial.print(F("\"manifest\":{\"present\":")); Serial.print(hasManifest?F("true"):F("false"));
  Serial.print(F(",\"schemaOk\":")); Serial.print(schemaOk?F("true"):F("false")); Serial.print('}');
  Serial.print(',');
  Serial.print(F("\"required\":{\"buttonsCsv\":")); Serial.print(hasButtons?F("true"):F("false"));
  Serial.print(F(",\"fallbackClip\":")); Serial.print(hasFallback?F("true"):F("false")); Serial.print('}');
  Serial.print(',');
  Serial.print(F("\"keys\":["));
  bool first = true;
  for (uint8_t i = 0; i < buttonCount; i++) {
    if (!buttons[i].used) continue;
    // ensure unique logical key
    bool seen = false;
    for (uint8_t j = 0; j < i; j++) if (buttons[j].used && stringEquals(buttons[j].key, buttons[i].key)) { seen = true; break; }
    if (seen) continue;
    if (!first) Serial.print(','); first = false;
    const char* key = buttons[i].key;
    String human = String("/mappings/playlists/") + key + "_human.m3u";
    String gen   = String("/mappings/playlists/") + key + "_generated.m3u";
    Serial.print(F("{\"key\":\"")); Serial.print(key); Serial.print(F("\","));
    Serial.print(F("\"hasHuman\":")); Serial.print(SD.exists(human.c_str())?F("true"):F("false")); Serial.print(',');
    Serial.print(F("\"hasGenerated\":")); Serial.print(SD.exists(gen.c_str())?F("true"):F("false"));
    Serial.print('}');
  }
  Serial.print(']');
  Serial.print(',');
  // overall ok
  bool ok = hasButtons && hasManifest && schemaOk && hasFallback;
  Serial.print(F("\"ok\":")); Serial.print(ok?F("true"):F("false"));
  Serial.println('}');
}

bool stringEquals(const char* a, const char* b) {
  return strcmp(a, b) == 0;
}

// ===== MANIFEST AND VALIDATION =====
static void writeManifestIfMissing() {
  if (!SD.exists("/manifest.json")) {
    File f = SD.open("/manifest.json", FILE_WRITE);
    if (f) {
      f.print('{');
      f.print("\"schemaVersion\":"); f.print(MANIFEST_SCHEMA_VER); f.print(',');
      f.print("\"firmware\":\""); f.print(FIRMWARE_VERSION); f.print("\"");
      f.print('}');
      f.close();
      Serial.println(F("[MANIFEST] Created /manifest.json"));
    }
  }
}

static void checkManifestVersion() {
  File f = SD.open("/manifest.json", FILE_READ);
  if (!f) return;
  String s; while (f.available()) s += (char)f.read(); f.close();
  int pos = s.indexOf("schemaVersion");
  if (pos >= 0) {
    int colon = s.indexOf(':', pos);
    if (colon >= 0) {
      int ver = s.substring(colon + 1).toInt();
      if (ver != MANIFEST_SCHEMA_VER) {
        Serial.print(F("[WARN] Manifest schema mismatch: ")); Serial.println(ver);
      }
    }
  }
}

static void verifyRequiredFiles() {
  if (!SD.exists("/config/buttons.csv")) {
    Serial.println(F("[ERROR] Missing /config/buttons.csv"));
  }
  // For each mapped key, ensure playlists exist
  for (uint8_t i = 0; i < buttonCount; i++) {
    if (!buttons[i].used) continue;
    const char* key = buttons[i].key;
    // de-duplicate keys
    bool seen = false;
    for (uint8_t j = 0; j < i; j++) {
      if (buttons[j].used && stringEquals(buttons[j].key, key)) { seen = true; break; }
    }
    if (seen) continue;
    String human = String("/mappings/playlists/") + key + "_human.m3u";
    String gen   = String("/mappings/playlists/") + key + "_generated.m3u";
    if (!SD.exists(human.c_str())) {
      Serial.print(F("[WARN] Missing playlist: ")); Serial.println(human);
    }
    if (!SD.exists(gen.c_str())) {
      Serial.print(F("[WARN] Missing playlist: ")); Serial.println(gen);
    }
  }
}

// ===== CONFIGURATION LOADING =====
void loadConfig() {
  Serial.println(F("[CONFIG] Loading configuration..."));
  
  buttonCount = 0;
  keyCursorCount = 0;
  activeLoaded = false;
  activeKey[0] = '\0';
  cursorDirty = false;
  lastCursorSaveMs = millis();
  
  // Load mode.cfg
  File modeFile = SD.open("/config/mode.cfg", FILE_READ);
  if (modeFile) {
    while (modeFile.available()) {
      String line = modeFile.readStringUntil('\n');
      line.trim();
      if (line.startsWith("PRIORITY=")) {
        globalPriority = (line.indexOf("GENERATED_FIRST") >= 0) ? GENERATED_FIRST : HUMAN_FIRST;
      } else if (line.startsWith("STRICT_PLAYLISTS=")) {
        strictPlaylists = (line.indexOf("1") >= 0);
      }
    }
    modeFile.close();
  }
  
  // Load buttons.csv
  File buttonFile = SD.open("/config/buttons.csv", FILE_READ);
  if (buttonFile) {
    while (buttonFile.available() && buttonCount < MAX_BUTTONS) {
      String line = buttonFile.readStringUntil('\n');
      line.trim();
      
      if (line.length() == 0 || line.startsWith("#")) continue;
      
      int commaIndex = line.indexOf(',');
      if (commaIndex > 0) {
        String inputId = line.substring(0, commaIndex);
        String key = line.substring(commaIndex + 1);
        inputId.trim();
        key.trim();
        
        copyString(buttons[buttonCount].inputId, inputId.c_str(), sizeof(buttons[buttonCount].inputId));
        copyString(buttons[buttonCount].key, key.c_str(), sizeof(buttons[buttonCount].key));
        buttons[buttonCount].used = true;
        buttonCount++;
      }
    }
    buttonFile.close();
  }
  
  Serial.print(F("[CONFIG] Loaded "));
  Serial.print(buttonCount);
  Serial.println(F(" button mappings"));
  // Load persisted cursors last
  loadCursors();

  // Apply optional import file from desktop sync
  if (SD.exists("/state/import.json")) {
    File f = SD.open("/state/import.json", FILE_READ);
    if (f) {
      String s; while (f.available()) s += (char)f.read(); f.close();
      // priority
      int p = s.indexOf("\"priority\"");
      if (p >= 0) {
        int colon = s.indexOf(':', p);
        if (colon >= 0) {
          if (s.indexOf("GENERATED_FIRST", colon) >= 0) globalPriority = GENERATED_FIRST; else globalPriority = HUMAN_FIRST;
          EEPROM.write(EEPROM_ADDR_MODE, (uint8_t)globalPriority);
        }
      }
      // cursors object
      int c = s.indexOf("\"cursors\"");
      if (c >= 0) {
        int brace = s.indexOf('{', c);
        int end = s.indexOf('}', brace);
        if (brace >= 0 && end > brace) {
          // crude parse by reusing loadCursors approach on the substring
          // reset and parse
          keyCursorCount = 0; for (uint8_t i = 0; i < MAX_KEYS; i++) keyCursors[i].used = false;
          String sub = s.substring(brace, end + 1);
          int pos = 0;
          while (true) {
            int ks = sub.indexOf('"', pos); if (ks < 0) break;
            int ke = sub.indexOf('"', ks + 1); if (ke < 0) break;
            String key = sub.substring(ks + 1, ke);
            int os = sub.indexOf('{', ke); int oe = sub.indexOf('}', os);
            if (os < 0 || oe < 0) break;
            String obj = sub.substring(os, oe + 1);
            int hIdx = 0, gIdx = 0;
            int hPos = obj.indexOf("\"human\""); if (hPos >= 0) { int col = obj.indexOf(':', hPos); if (col >= 0) hIdx = obj.substring(col + 1).toInt(); }
            int gPos = obj.indexOf("\"generated\""); if (gPos >= 0) { int col = obj.indexOf(':', gPos); if (col >= 0) gIdx = obj.substring(col + 1).toInt(); }
            if (keyCursorCount < MAX_KEYS) {
              copyString(keyCursors[keyCursorCount].key, key.c_str(), sizeof(keyCursors[keyCursorCount].key));
              keyCursors[keyCursorCount].cursor.humanIdx = (uint8_t)hIdx;
              keyCursors[keyCursorCount].cursor.generatedIdx = (uint8_t)gIdx;
              keyCursors[keyCursorCount].used = true;
              keyCursorCount++;
            }
            pos = oe + 1;
          }
        }
      }
      // cleanup
      SD.remove("/state/import.json");
      saveCursors();
      Serial.println(F("[SYNC] Applied /state/import.json"));
    }
  }
  
  // Verify manifest and required files
  writeManifestIfMissing();
  checkManifestVersion();
  verifyRequiredFiles();
}

void saveConfig() {
  // Save mode.cfg
  File modeFile = SD.open("/config/mode.cfg", FILE_WRITE);
  if (modeFile) {
    modeFile.print(F("PRIORITY="));
    modeFile.println(globalPriority == HUMAN_FIRST ? F("HUMAN_FIRST") : F("GENERATED_FIRST"));
    modeFile.print(F("STRICT_PLAYLISTS="));
    modeFile.println(strictPlaylists ? F("1") : F("0"));
    modeFile.close();
  }
  // Also persist cursors if dirty
  if (cursorDirty) {
    saveCursors();
    cursorDirty = false;
    lastCursorSaveMs = millis();
  }
}

// ===== CURSOR PERSISTENCE =====
static void ensureStateDir() {
  if (!SD.exists("/state")) {
    SD.mkdir("/state");
  }
}

// Write cursors as a compact JSON object: {"A":{"human":1,"generated":2},...}
void saveCursors() {
  ensureStateDir();
  File f = SD.open("/state/cursors.json", FILE_WRITE);
  if (!f) return;
  f.print('{');
  bool first = true;
  for (uint8_t i = 0; i < keyCursorCount; i++) {
    if (!keyCursors[i].used) continue;
    if (!first) f.print(',');
    first = false;
    f.print('\"'); f.print(keyCursors[i].key); f.print('\"'); f.print(':');
    f.print('{');
    f.print("\"human\":"); f.print((int)keyCursors[i].cursor.humanIdx); f.print(',');
    f.print("\"generated\":"); f.print((int)keyCursors[i].cursor.generatedIdx);
    f.print('}');
  }
  f.print('}');
  f.close();
}

// Naive JSON loader: expects the format we write above
void loadCursors() {
  File f = SD.open("/state/cursors.json", FILE_READ);
  if (!f) return;
  String content;
  while (f.available()) {
    content += (char)f.read();
  }
  f.close();

  // Reset any existing cursors; will be recreated lazily on first use
  keyCursorCount = 0;
  for (uint8_t i = 0; i < MAX_KEYS; i++) keyCursors[i].used = false;

  int pos = 0;
  while (true) {
    int keyStart = content.indexOf('\"', pos);
    if (keyStart < 0) break;
    int keyEnd = content.indexOf('\"', keyStart + 1);
    if (keyEnd < 0) break;
    String key = content.substring(keyStart + 1, keyEnd);

    int objStart = content.indexOf('{', keyEnd);
    int objEnd = content.indexOf('}', objStart);
    if (objStart < 0 || objEnd < 0) break;
    String obj = content.substring(objStart, objEnd + 1);

    // Extract numbers after "human": and "generated":
    int hIdx = 0, gIdx = 0;
    int hPos = obj.indexOf("\"human\"");
    if (hPos >= 0) {
      int colon = obj.indexOf(':', hPos);
      if (colon >= 0) {
        hIdx = obj.substring(colon + 1).toInt();
      }
    }
    int gPos = obj.indexOf("\"generated\"");
    if (gPos >= 0) {
      int colon = obj.indexOf(':', gPos);
      if (colon >= 0) {
        gIdx = obj.substring(colon + 1).toInt();
      }
    }

    if (keyCursorCount < MAX_KEYS) {
      copyString(keyCursors[keyCursorCount].key, key.c_str(), sizeof(keyCursors[keyCursorCount].key));
      keyCursors[keyCursorCount].cursor.humanIdx = (uint8_t)hIdx;
      keyCursors[keyCursorCount].cursor.generatedIdx = (uint8_t)gIdx;
      keyCursors[keyCursorCount].used = true;
      keyCursorCount++;
    }

    pos = objEnd + 1;
  }
}

// ===== PLAYLIST MANAGEMENT =====
bool loadPlaylistsForKey(const char* key) {
  // If already active for this key, nothing to do
  if (activeLoaded && stringEquals(activeKey, key)) {
    return true;
  }

  activePlaylists.humanCount = 0;
  activePlaylists.generatedCount = 0;

  // Load human playlist
  String humanPath = String("/mappings/playlists/") + key + "_human.m3u";
  File humanFile = SD.open(humanPath.c_str(), FILE_READ);
  if (humanFile) {
    while (humanFile.available() && activePlaylists.humanCount < 16) {
      String line = humanFile.readStringUntil('\n');
      line.trim();
      if (line.length() > 0 && !line.startsWith("#")) {
        copyString(activePlaylists.human[activePlaylists.humanCount].path, line.c_str(), 64);
        activePlaylists.humanCount++;
      }
    }
    humanFile.close();
  }

  // Load generated playlist
  String generatedPath = String("/mappings/playlists/") + key + "_generated.m3u";
  File generatedFile = SD.open(generatedPath.c_str(), FILE_READ);
  if (generatedFile) {
    while (generatedFile.available() && activePlaylists.generatedCount < 16) {
      String line = generatedFile.readStringUntil('\n');
      line.trim();
      if (line.length() > 0 && !line.startsWith("#")) {
        copyString(activePlaylists.generated[activePlaylists.generatedCount].path, line.c_str(), 64);
        activePlaylists.generatedCount++;
      }
    }
    generatedFile.close();
  }

  copyString(activeKey, key, sizeof(activeKey));
  activeLoaded = true;
  return true;
}

const char* nextTrackForKey(const char* key) {
  if (!loadPlaylistsForKey(key)) return nullptr;

  // Find or create cursor entry for this key
  uint8_t idx = keyCursorCount;
  for (uint8_t i = 0; i < keyCursorCount; i++) {
    if (keyCursors[i].used && stringEquals(keyCursors[i].key, key)) {
      idx = i;
      break;
    }
  }
  if (idx == keyCursorCount) {
    if (keyCursorCount >= MAX_KEYS) return nullptr; // out of cursor slots
    copyString(keyCursors[idx].key, key, sizeof(keyCursors[idx].key));
    keyCursors[idx].cursor.humanIdx = 0;
    keyCursors[idx].cursor.generatedIdx = 0;
    keyCursors[idx].used = true;
    keyCursorCount++;
  }

  PlayCursor& cursor = keyCursors[idx].cursor;
  Playlists& pl = activePlaylists;

  // Priority-based selection with fallback
  if (globalPriority == HUMAN_FIRST) {
    if (pl.humanCount > 0) {
      if (cursor.humanIdx >= pl.humanCount) cursor.humanIdx = 0;
      const char* path = pl.human[cursor.humanIdx].path;
      cursor.humanIdx++;
      cursorDirty = true;
      return path;
    }
    if (pl.generatedCount > 0) {
      if (cursor.generatedIdx >= pl.generatedCount) cursor.generatedIdx = 0;
      const char* path = pl.generated[cursor.generatedIdx].path;
      cursor.generatedIdx++;
      cursorDirty = true;
      return path;
    }
  } else {
    if (pl.generatedCount > 0) {
      if (cursor.generatedIdx >= pl.generatedCount) cursor.generatedIdx = 0;
      const char* path = pl.generated[cursor.generatedIdx].path;
      cursor.generatedIdx++;
      cursorDirty = true;
      return path;
    }
    if (pl.humanCount > 0) {
      if (cursor.humanIdx >= pl.humanCount) cursor.humanIdx = 0;
      const char* path = pl.human[cursor.humanIdx].path;
      cursor.humanIdx++;
      cursorDirty = true;
      return path;
    }
  }
  return nullptr;
}

// ===== BUTTON MAPPING =====
const char* keyForInput(const char* inputId) {
  for (uint8_t i = 0; i < buttonCount; i++) {
    if (buttons[i].used && stringEquals(buttons[i].inputId, inputId)) {
      return buttons[i].key;
    }
  }
  return nullptr;
}

// ===== PRESS HANDLING =====
void onPhysicalPress(const char* inputId) {
  const char* key = keyForInput(inputId);
  if (!key) return;
  
  // Handle period triple-press for priority toggle
  if (stringEquals(key, ".")) {
    unsigned long now = millis();
    if (now - periodWindowStart > PERIOD_WINDOW_MS) {
      periodPressCount = 1;
      periodWindowStart = now;
    } else {
      periodPressCount++;
    }
    
    if (periodPressCount >= 3) {
      // Toggle priority mode
      globalPriority = (globalPriority == HUMAN_FIRST) ? GENERATED_FIRST : HUMAN_FIRST;
      EEPROM.write(EEPROM_ADDR_MODE, (uint8_t)globalPriority);
      saveConfig();
      
      Serial.print(F("[MODE] Priority: "));
      Serial.println(globalPriority == HUMAN_FIRST ? F("HUMAN_FIRST") : F("GENERATED_FIRST"));
      
      // Cancel any pending selection for '.' so it doesn't play afterward
      if (hasPending && stringEquals(pendingKey, ".")) {
        hasPending = false;
        pendingKey[0] = '\0';
        pendingCount = 0;
      }
      periodPressCount = 0;
      return;
    }
    // Else: allow '.' to participate in normal pending aggregation so a single press
    // resolves via Phase 5 playback when the window expires.
  }

  // Aggregate presses per key within a short window
  unsigned long now = millis();
  if (hasPending) {
    if (stringEquals(pendingKey, key) && (now - pendingWindowStart) <= PRESS_WINDOW_MS) {
      pendingCount++;
      pendingWindowStart = now;
      return;
    }
    // Different key or window expired: finalize previous selection first
    if ((now - pendingWindowStart) > PRESS_WINDOW_MS || !stringEquals(pendingKey, key)) {
      finalizePendingSelection();
    }
  }
  // Start new pending for this key
  copyString(pendingKey, key, sizeof(pendingKey));
  pendingCount = 1;
  pendingWindowStart = now;
  hasPending = true;
}

// ===== SETUP =====
void setup() {
  Serial.begin(115200);
  while (!Serial && millis() < 3000);
  
  Serial.println(F("\n=== TACTILE COMMUNICATOR - IMPROVED SD-DEFINED SYSTEM ==="));
  
  // Initialize I2C
  Wire.begin();
  
  // Initialize PCF8575 expanders
  for (uint8_t i = 0; i < NUM_PCF; i++) {
    if (pcf[i].begin(PCF_ADDR[i], &Wire)) {
      for (uint8_t p = 0; p < 16; p++) {
        pcf[i].pinMode(p, INPUT_PULLUP);
      }
      last_state[i] = pcf[i].digitalReadWord();
    } else {
      last_state[i] = 0xFFFF;
    }
  }
  
  // Initialize extra GPIO pins
  for (uint8_t i = 0; i < EXTRA_COUNT; i++) {
    pinMode(extraPins[i], INPUT_PULLUP);
    lastExtra[i] = digitalRead(extraPins[i]);
  }
  
  // Initialize VS1053
  if (!musicPlayer.begin()) {
    Serial.println(F("[ERROR] VS1053 not found"));
    while (1);
  }
  
  // Initialize SD card
  if (!SD.begin(CARDCS)) {
    Serial.println(F("[ERROR] SD card not found"));
    while (1);
  }
  
  musicPlayer.setVolume(20, 20);
  
  // Load priority mode from EEPROM
  uint8_t savedMode = EEPROM.read(EEPROM_ADDR_MODE);
  if (savedMode <= 1) {
    globalPriority = (Priority)savedMode;
  }
  
  loadConfig();
  
  Serial.println(F("[INIT] Ready!"));
  Serial.println(F("Commands: L=load, S=save, P=print, H=help, M=toggle mode, X=stop, GET_VERSION, GET_SUMMARY, GET_VALIDATE, EXPORT_STATE, IMPORT_STATE"));
}

// ===== MAIN LOOP =====
void loop() {
  // Check PCF8575 button presses
  for (uint8_t chip = 0; chip < NUM_PCF; chip++) {
    uint16_t current = pcf[chip].digitalReadWord();
    uint16_t pressed = (last_state[chip] ^ current) & ~current;
    
    if (pressed) {
      for (uint8_t pin = 0; pin < 16; pin++) {
        if (pressed & (1 << pin)) {
          char inputId[16];
          snprintf(inputId, sizeof(inputId), "pcf%d:%d", chip, pin);
          onPhysicalPress(inputId);
        }
      }
    }
    last_state[chip] = current;
  }
  
  // Check extra GPIO button presses
  for (uint8_t i = 0; i < EXTRA_COUNT; i++) {
    bool current = digitalRead(extraPins[i]);
    if (lastExtra[i] && !current) {
      char inputId[16];
      snprintf(inputId, sizeof(inputId), "gpio:%d", extraPins[i]);
      onPhysicalPress(inputId);
    }
    lastExtra[i] = current;
  }
  
  // Handle serial commands (supports single-char and line-based)
  if (Serial.available()) {
    delay(5); // allow buffer to fill a bit
    String line = Serial.readStringUntil('\n');
    line.trim();
    if (line.length() == 1) {
      char cmd = line.charAt(0);
      switch (cmd) {
        case 'L': case 'l': loadConfig(); break;
        case 'S': case 's': saveConfig(); break;
        case 'P': case 'p':
          Serial.println(F("=== BUTTON MAPPINGS ==="));
          for (uint8_t i = 0; i < buttonCount; i++) {
            if (buttons[i].used) {
              Serial.print(buttons[i].inputId);
              Serial.print(F(" -> "));
              Serial.println(buttons[i].key);
            }
          }
          break;
        case 'H': case 'h':
          Serial.println(F("Commands: L=load, S=save, P=print, M=toggle mode, X=stop, GET_VERSION, GET_SUMMARY, GET_VALIDATE, EXPORT_STATE, IMPORT_STATE"));
          break;
        case 'M': case 'm':
          globalPriority = (globalPriority == HUMAN_FIRST) ? GENERATED_FIRST : HUMAN_FIRST;
          EEPROM.write(EEPROM_ADDR_MODE, (uint8_t)globalPriority);
          saveConfig();
          Serial.print(F("[MODE] "));
          Serial.println(globalPriority == HUMAN_FIRST ? F("HUMAN_FIRST") : F("GENERATED_FIRST"));
          break;
        case 'X': case 'x':
          if (isPlaying) {
            musicPlayer.stopPlaying();
            isPlaying = false;
            Serial.println(F("[STOP] Audio stopped"));
          }
          break;
      }
    } else if (line.equalsIgnoreCase("GET_VERSION")) {
      Serial.print(F("{\"firmware\":\"")); Serial.print(FIRMWARE_VERSION); Serial.print(F("\",\"schema\":")); Serial.print(MANIFEST_SCHEMA_VER); Serial.print(F(",\"priority\":\""));
      Serial.print(globalPriority == HUMAN_FIRST ? F("HUMAN_FIRST") : F("GENERATED_FIRST"));
      Serial.println(F("\"}"));
    } else if (line.equalsIgnoreCase("GET_SUMMARY")) {
      // Build a minimal JSON summary
      Serial.print(F("{\"keys\":["));
      bool first = true;
      for (uint8_t i = 0; i < buttonCount; i++) {
        if (!buttons[i].used) continue;
        // unique keys only
        bool seen = false;
        for (uint8_t j = 0; j < i; j++) if (buttons[j].used && stringEquals(buttons[j].key, buttons[i].key)) { seen = true; break; }
        if (seen) continue;
        if (!first) Serial.print(','); first = false;
        const char* key = buttons[i].key;
        String human = String("/mappings/playlists/") + key + "_human.m3u";
        String gen   = String("/mappings/playlists/") + key + "_generated.m3u";
        Serial.print(F("{\"key\":\"")); Serial.print(key); Serial.print(F("\",\"hasHuman\":")); Serial.print(SD.exists(human.c_str())?F("true"):F("false"));
        Serial.print(F(",\"hasGenerated\":")); Serial.print(SD.exists(gen.c_str())?F("true"):F("false")); Serial.print('}');
      }
      Serial.println(F("],\"ok\":true}"));
    } else if (line.equalsIgnoreCase("GET_VALIDATE")) {
      emitValidationReport();
    } else if (line.equalsIgnoreCase("EXPORT_STATE")) {
      // Emit priority and cursors JSON
      Serial.print(F("{\"priority\":\""));
      Serial.print(globalPriority == HUMAN_FIRST ? F("HUMAN_FIRST") : F("GENERATED_FIRST"));
      Serial.print(F("\",\"cursors\":"));
      // reuse saveCursors format by constructing here
      Serial.print('{'); bool first = true;
      for (uint8_t i = 0; i < keyCursorCount; i++) {
        if (!keyCursors[i].used) continue;
        if (!first) Serial.print(','); first = false;
        Serial.print('"'); Serial.print(keyCursors[i].key); Serial.print('"'); Serial.print(':');
        Serial.print('{');
        Serial.print("\"human\":"); Serial.print((int)keyCursors[i].cursor.humanIdx); Serial.print(',');
        Serial.print("\"generated\":"); Serial.print((int)keyCursors[i].cursor.generatedIdx);
        Serial.print('}');
      }
      Serial.println(F("}}"));
    } else if (line.startsWith("IMPORT_STATE")) {
      Serial.println(F("[WARN] IMPORT_STATE over serial not implemented. Place /state/import.json then send 'L' to load."));
    }
  }
  
  // Update audio playing status
  if (isPlaying && !musicPlayer.playingMusic) {
    isPlaying = false;
    currentTrackPath[0] = '\0';
  }
  // Debounced cursor save
  if (cursorDirty) {
    unsigned long now = millis();
    if (now - lastCursorSaveMs >= CURSOR_SAVE_INTERVAL_MS) {
      saveCursors();
      cursorDirty = false;
      lastCursorSaveMs = now;
    }
  }
  // Finalize any pending multi-press after window timeout
  if (hasPending) {
    unsigned long now2 = millis();
    if ((now2 - pendingWindowStart) > PRESS_WINDOW_MS) {
      finalizePendingSelection();
    }
  }
  
  delay(10);
}
