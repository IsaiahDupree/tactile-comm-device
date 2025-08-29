---
description: SD-defined, hardware-agnostic playlists + 3x PCF8575 + desktop integration
---

# Program Plan — SD-Defined, Hardware-Agnostic Playlists + Extra PCF8575 + Desktop Update

Backup repo reference: `C:\Users\Isaia\Documents\3D Printing\Projects\Button\Audio\Adafruit_VS1053_Library\player_simple_working_directory` (GitHub backup)
Active workdir: `C:\Users\Isaia\Documents\3D Printing\Projects\Button\Audio\Adafruit_VS1053_Library\player_simple_working_directory_v2`

Key computed constants to use everywhere:
- `TOTAL_EXPANDER_PINS = NUM_PCF * 16`
- `TOTAL_BUTTONS = TOTAL_EXPANDER_PINS + EXTRA_COUNT`

Phase 0 — Branch & scaffolding
0.a Utility sweep to 48 + EXTRA_COUNT ✅ (your prior fix)
- Intent: ensure every loop/array/guard uses the computed total buttons, not hardcoded 32.
- Scope: initializeHardwareMapping, handlePress, handleMultiPress, printMap, testAllButtons, sanityCheckAudio, arrays `lastPressTime[]`, `pressCount[]`, `mapTab[]` sized by `TOTAL_BUTTONS`.
- DoD: pressing the highest index (`TOTAL_BUTTONS-1`) logs correctly; no out-of-bounds; utilities iterate full range.

0.b Branch & flags
- Branch: `feature/sd-playlists-3xpand-generalized`.
- Config gate: `STRICT_PLAYLISTS` sourced from `/config/mode.cfg` (default 0 if missing). Keep a compile-time fallback `STRICT_PLAYLISTS_DEFAULT` during bring-up.

Phase 1 — PCF generalization (support N expanders)
- Treat PCF8575s as an array; add chip at 0x22 (or the addresses you use).
- Data:
  - `const uint8_t PCF_ADDR[] = {0x20, 0x21, 0x22};`
  - `constexpr uint8_t NUM_PCF = sizeof(PCF_ADDR)/sizeof(PCF_ADDR[0]);`
  - `Adafruit_PCF8575 pcf[NUM_PCF];`
  - `uint16_t last_state[NUM_PCF];`
- Setup: loop i=0..NUM_PCF-1 → `begin(addr,&Wire1)`, `pinMode(p, INPUT_PULLUP)` for p=0..15, prime `last_state[i]`, log found/missing.
- Loop: per chip, read `.digitalReadWord()`, detect HIGH→LOW, emit `onPhysicalPress("pcf<i>:<pin>")`.
- Indexing: extras start at `TOTAL_EXPANDER_PINS`.
- DoD: all detected chips log; each chip’s buttons register with `pcf<idx>:<pin>` and correct logical index; unplugging one chip leaves others working.

Phase 2 — Hardware-agnostic input routing
- File: `/config/buttons.csv`
  ```
  #INPUT,KEY
  pcf0:00,A
  pcf1:03,Water
  pcf2:10,S
  gpio:8,Back
  ```
- Runtime: load to vector of `{inputId, key}`. Press path: physical → `inputId` → `keyForInput()` → playback. Unmapped inputs log once per boot.
- DoD: moving a wire (e.g., pcf0:00→pcf1:07) only needs a CSV edit; no firmware change.

Phase 3 — Strict playlist loading & caching
- Files:
  - `/config/mode.cfg` → `PRIORITY=HUMAN_FIRST|GENERATED_FIRST`, `STRICT_PLAYLISTS=0|1`
  - `/mappings/playlists/<KEY>_human.m3u`
  - `/mappings/playlists/<KEY>_generated.m3u`
- Cache per key:
  ```
  struct KeyPlaylists { std::vector<String> human, generated; uint16_t hIdx=0, gIdx=0; bool loaded=false; };
  std::map<String, KeyPlaylists> plCache;
  ```
- Load rules: trim lines, ignore `#`, treat entries as SD-root-relative paths; if `STRICT_PLAYLISTS=1` and both empty ⇒ disable key (clear log).
- DoD: changing `.m3u` order changes playback order without reflashing; missing list in strict mode disables that bank.

Phase 3.x — Options
- (3.1) Cursor persistence: `/state/cursors.json` holds `{key: {human, generated}}`.
- (3.2) Manifest check: `/manifest.json` sanity-verifies presence/versions.
- (3.3) Desktop verbs over serial: `GET_VERSION/GET_SUMMARY/EXPORT_STATE/IMPORT_STATE`.

Phase 4 — Priority mode + period triple‑press
- Global bank order. Toggle via PERIOD.
- Enum: `HUMAN_FIRST | GENERATED_FIRST`.
- Boot: read from `/config/mode.cfg`.
- Toggle: triple-press `.` within ~1200 ms → flip mode, write back to `mode.cfg`, play announcement.
- DoD: mode persists across power cycles; announcement plays; desktop sees updated `mode.cfg`.

Phase 5 — Playback algorithm & cursoring
- Select next track with fallback and wrap, then play.
- Resolve preferred bank from priority. Try next from preferred playlist; if empty, try the other; wrap indices.
- Stop current, soft-reset VS1053 if needed, then `startPlayingFile(path)`.
- On success, advance cursor; optionally flush cursors to `/state/cursors.json` (debounced).
- DoD: human-first vs generated-first behaves as specified; multi-press within 1s advances within chosen bank.

Phase 6 — Desktop update protocol (serial, minimal)
- Safe SD updates from the app on any board.
- Commands:
  - `FS_BEGIN <files> <totalBytes> <manifestCrc32>` → OK
  - `FS_PUT <path> <size> <crc32>` → OK → repeat `FS_DATA <n>\n<bytes>` … → `FS_DONE`
  - `FS_COMMIT` (atomic rename from `/.staging`) / `FS_ABORT`
  - `CFG_RELOAD` (reload mode/buttons/playlist caches)
- Guards: maintenance mode (ignore presses), per-file CRC32, write only to staging, atomic swap, optional `/manifest.json`.
- DoD: power loss during transfer leaves previous state intact; `CFG_RELOAD` applies new config without reboot.

Phase 7 — Desktop app contract (Win/Mac/Linux)
- App flashes firmware + syncs SD.
- Flash: bundle Arduino CLI, autodetect board/port, stream logs.
- SD sync: implement the serial protocol; retry per file; resume by file.
- Single source of truth (the app manages):
  - `/config/mode.cfg`, `/config/buttons.csv`
  - `/mappings/playlists/*.m3u`
  - `/audio/human|generated/...`
  - `/state/cursors.json` (optional)
  - `/manifest.json` (optional schema)
- DoD: “Update Device” runs firmware flash (optional) + SD sync + `CFG_RELOAD` + quick self-test clip.

Phase 8 — Acceptance tests (end-to-end)
- Discovery: boot logs all PCFs at 0x20/0x21/0x22 with 16 inputs each.
- Mapping: rewire a button; edit `buttons.csv`; behavior unchanged.
- Strictness: with `STRICT_PLAYLISTS=1`, missing `*_human.m3u` disables that bank for the key (clear log).
- Priority: `.` triple-press flips mode, persists to `mode.cfg`, plays announcement.
- Ordering: edit `.m3u` order; device plays in that order.
- Update path: desktop app flashes + pushes SD atomically; `CFG_RELOAD` applies without reboot.
- Resilience: mid-transfer power loss → old SD contents still work; staging cleaned on next boot.

Notes on addresses
- If your third expander is wired to 0x22 (as stated) or 0x24 (noted earlier), set `PCF_ADDR` to the exact list you have. The array approach supports either.
