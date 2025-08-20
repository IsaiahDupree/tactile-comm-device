---
description: Jira story and sub-task checklist for SD playlists + 3x PCF8575 + desktop integration
---

# Story: SD-Defined, Hardware-Agnostic Playlists with 3× PCF8575 and Desktop Sync

As a caregiver/operator, I want the device to load button mappings and ordered audio playlists from the SD card so that I can rewire hardware and update content without reflashing firmware, while the desktop app safely syncs files and toggles priority mode.

## Business Value
- Zero firmware edits for wiring/content changes
- Safer, auditable SD updates via desktop
- Consistent behavior across different hardware builds

## Acceptance Criteria
- Device boots and detects up to 3 PCF8575 expanders; missing chips do not break the others
- Physical input → key label mapping comes from `/config/buttons.csv`
- Playback order for each key comes from `.m3u` playlists
- Priority mode is persisted and toggleable via period triple‑press and reflected in `/config/mode.cfg`
- Desktop can push updates atomically and trigger a config reload without reboot

---

## Sub‑Tasks and Checklists

### ST‑0: Scaffolding and Branch
- [ ] Create branch `feature/sd-playlists-3xpand-generalized`
- [ ] Add compile‑time fallback `STRICT_PLAYLISTS_DEFAULT`
- [ ] Add runtime load for `/config/mode.cfg` (PRIORITY, STRICT_PLAYLISTS)
- [ ] 0.a Utility sweep to `TOTAL_BUTTONS = (NUM_PCF*16) + EXTRA_COUNT` (arrays, loops, guards)
- DoD:
  - [ ] Highest index (`TOTAL_BUTTONS-1`) logs correctly
  - [ ] No out‑of‑bounds in utilities (sanity check, tests)

Git commands (reference):
```
git checkout -b feature/sd-playlists-3xpand-generalized
git add -A && git commit -m "Phase 0 scaffolding + flags + utility sweep"
```

### ST‑1: PCF Generalization (N Expanders)
- [ ] `PCF_ADDR[]` array and `NUM_PCF` compute
- [ ] Initialize each `Adafruit_PCF8575` with `begin(addr, &Wire1)`
- [ ] Configure `pinMode(p, INPUT_PULLUP)` for 0..15, prime `last_state[i]`
- [ ] In loop, read `.digitalReadWord()` per chip; detect HIGH→LOW
- [ ] Map extras after `TOTAL_EXPANDER_PINS`
- DoD:
  - [ ] Each detected chip logs online with pin range
  - [ ] Button on each chip reports `pcf<i>:<pin>` and logical index
  - [ ] Unplugging a chip leaves others fully functional

### ST‑2: Hardware‑Agnostic Input Routing
- [ ] Implement `/config/buttons.csv` loader into memory map `{inputId, key}`
- [ ] Format: `pcf0:00,A` / `pcf1:03,Water` / `gpio:8,Back`
- [ ] `keyForInput(inputId)` resolves on press; unmapped inputs log once per boot
- DoD:
  - [ ] Moving a wire only requires CSV edit
  - [ ] No firmware change needed to remap inputs

### ST‑3: Playlist Loading & Caching (Strict Optional)
- [ ] Parse `/mappings/playlists/<KEY>_human.m3u` and `<KEY>_generated.m3u`
- [ ] Cache per key: `human`, `generated`, `hIdx`, `gIdx`
- [ ] Enforce `STRICT_PLAYLISTS` (mode.cfg) — if both empty, disable key with clear log
- DoD:
  - [ ] Changing `.m3u` order changes playback order without reflashing
  - [ ] Missing list in strict mode disables that bank

Optional 3.x
- [ ] (3.1) `/state/cursors.json` persistence
- [ ] (3.2) `/manifest.json` schema/version check
- [ ] (3.3) Desktop verbs: `GET_VERSION`, `GET_SUMMARY`, `EXPORT_STATE`, `IMPORT_STATE`

### ST‑4: Priority Mode + Period Triple‑Press
- [ ] Enum: `HUMAN_FIRST | GENERATED_FIRST`
- [ ] Boot: read from `/config/mode.cfg`
- [ ] Triple‑press `.` within ~1200 ms toggles mode, writes back to `mode.cfg`, plays announcement
- DoD:
  - [ ] Mode persists across reboots
  - [ ] Announcement plays and is audible
  - [ ] Desktop reads updated `mode.cfg`

### ST‑5: Playback Algorithm & Cursoring
- [ ] Resolve preferred bank from priority; choose next track; wrap indices
- [ ] Stop current, soft‑reset VS1053 if needed, start new file
- [ ] Advance cursor on success; optional debounce to persist cursors
- DoD:
  - [ ] Human‑first vs generated‑first works as specified
  - [ ] Multi‑press within window advances within chosen bank

### ST‑6: Desktop Update Protocol (Serial)
- [ ] Implement `FS_BEGIN/FS_PUT/FS_DATA/FS_DONE/FS_COMMIT/FS_ABORT`
- [ ] Write to `/.staging`, atomic rename on commit
- [ ] `CFG_RELOAD` command reloads configs without reboot
- DoD:
  - [ ] Power loss mid‑transfer leaves previous state intact
  - [ ] `CFG_RELOAD` applies new config immediately

### ST‑7: Desktop App Integration
- [ ] Add firmware flash (Arduino CLI) and SD sync support
- [ ] Implement resume‑by‑file and per‑file CRC
- [ ] One‑click “Update Device” → flash (optional) + sync + `CFG_RELOAD` + self‑test
- DoD:
  - [ ] End‑to‑end update from desktop succeeds reliably on Win/Mac/Linux

### ST‑8: Acceptance Tests
- [ ] Boot discovery: logs for 0x20/0x21/0x22
- [ ] Mapping change via `buttons.csv` with behavior preserved
- [ ] Strictness behavior verified
- [ ] Priority toggle via `.` with persistence
- [ ] Playlist order honored
- [ ] Atomic SD update path validated
- [ ] Resilience: mid‑transfer power‑loss test

---

## Risks & Mitigations
- SPI/I2C contention → avoid VS1053 interrupts; poll and feed buffer
- SD corruption → staging + atomic commit; CRC32 per file
- User error in CSV/M3U → strict logging; desktop validation before push

## Definition of Done (Story)
- All acceptance criteria pass on real hardware with 3× PCF8575
- Operator quickstart published
- Desktop “Update Device” flow works end‑to‑end
