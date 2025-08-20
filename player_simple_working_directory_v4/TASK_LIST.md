# Tactile Communication Device - Task List

## Milestones Overview

* **M0** Baseline & utilities (✅ COMPLETE)
* **M1** SD config (strict) + hardware-agnostic routing (🚧 IN PROGRESS)
* **M2** Playlist engine (m3u) + cursors
* **M3** Priority mode (+ PERIOD triple-press) with persistence
* **M4** Update path (serial FS protocol, staging/rollback, reload)
* **M5** Desktop app (flash + SD sync + self-test)
* **M6** Acceptance, fault-injection, and resilience
* **M7** Docs & release packaging

---

## Detailed Task List

| ID       | Task                                            | Status | Depends on          | Details                                                                                                                                                                                                | Deliverables                            | DoD                                                                         |
| -------- | ----------------------------------------------- | ------ | ------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | --------------------------------------- | --------------------------------------------------------------------------- |
| **T-00** | **Verify "utility sweep to 48 + EXTRA_COUNT"** | ✅ DONE | —                   | Ensure all arrays/loops use `TOTAL_BUTTONS = NUM_PCF*16 + EXTRA_COUNT`. Sweep `initializeHardwareMapping, handlePress, handleMultiPress, printMap, testAllButtons, sanityCheckAudio`, timers/counters. | PR with audit notes                     | Press at highest logical index works; no OOB; utilities iterate full range. |
| **T-01** | Branch & config gate                            | ✅ DONE | —                   | Branch `feature/sd-playlists-3xpand-generalized`. Parse `STRICT_PLAYLISTS` from `/config/mode.cfg` (default `0` if missing).                                                                           | Branch + config parser                  | Firmware boots with/without `mode.cfg`.                                     |
| **T-02** | PCF array generalization (3 chips)              | ✅ DONE | T-00                | `PCF_ADDR[] = {0x20,0x21,0x22}` (or your actual addrs), `pcf[]`, `last_state[]`. Edge detect per chip; extras start at `NUM_PCF*16`.                                                                   | PCF init/logging                        | Boot logs each PCF; button on each chip triggers `pcf<i>:pin`.              |
| **T-03** | `/config/buttons.csv` parser                    | 🔄 PARTIAL | T-01                | Load `#INPUT,KEY` rows; support `pcfN:PP` and `gpio:X`. Map `inputId -> key`.                                                                                                                          | Parser + unit tests (CSV cases)         | Moving a wire only needs CSV change; unmapped inputs log once.              |
| **T-04** | Hardware-agnostic routing                       | 📋 TODO | T-03                | `onPhysicalPress(inputId) -> keyForInput -> playback`.                                                                                                                                                 | Integration commit                      | Press on any input produces the resolved KEY string in logs.                |
| **T-05** | `/config/mode.cfg` parser                       | ✅ DONE | T-01                | Parse `PRIORITY=...`, `STRICT_PLAYLISTS=0|1`.                                                                                                                                                          | Parser + tests                          | Priority & strict flags visible at runtime.                                 |
| **M1**   | **Milestone: SD config + routing**              | 🚧 75% | T-02..T-05          | —                                                                                                                                                                                                      | Demo SD with `buttons.csv` + `mode.cfg` | Rewire test passes; strict flag toggles behavior guards.                    |
| **T-06** | m3u reader (strict)                             | 📋 TODO | T-05                | Read `/mappings/playlists/<KEY>_human.m3u` and `_generated.m3u`. Trim, ignore `#`, **SD-root-relative** paths; UTF-8 (no BOM).                                                                         | Reader + unit tests                     | Valid/invalid playlists parsed; paths normalized.                           |
| **T-07** | Playlist cache & invalidation                   | 📋 TODO | T-06                | Per-key cache `{human, generated, loaded}`; lazy load on first use; `CFG_RELOAD` will flush.                                                                                                           | Cache module                            | First press of a key triggers load; reload clears cache.                    |
| **T-08** | Strict bank enforcement                         | 📋 TODO | T-06                | If `STRICT_PLAYLISTS=1` and both lists empty → key disabled (log once). No directory scanning fallback.                                                                                                | Guard + tests                           | Missing lists disable bank/key per spec.                                    |
| **T-09** | Per-key cursors                                 | 📋 TODO | T-07                | Track `hIdx/gIdx` with wrap; advance only after successful `startPlayingFile`. Optional debounce flush.                                                                                                | Cursor state                            | Consecutive presses cycle in playlist order.                                |
| **M2**   | **Milestone: Playlist engine**                  | 📋 0%  | T-06..T-09          | —                                                                                                                                                                                                      | Keys play in m3u order                  | Order change in m3u reflects in playback w/o flash.                         |
| **T-10** | Priority enum + boot load                       | ✅ DONE | T-05                | `HUMAN_FIRST|GENERATED_FIRST` global.                                                                                                                                                                  | Enum + state                            | Global order used by selection logic.                                       |
| **T-11** | PERIOD triple-press detector                    | ✅ DONE | T-04                | ~1200 ms window, count presses only for `KEY="PERIOD"`.                                                                                                                                               | Detector + tests                        | 3 presses within window toggles; 1–2 behave normally.                       |
| **T-12** | Persist priority to `mode.cfg` + announce       | ✅ DONE | T-10,T-11           | On toggle: write `PRIORITY=...` back to SD; play announcement clip.                                                                                                                                    | Writer + audio hook                     | Reboot preserves new mode; clip plays.                                      |
| **M3**   | **Milestone: Priority mode**                    | ✅ DONE | T-10..T-12          | —                                                                                                                                                                                                      | Demo toggle in logs & audio             | Desktop sees updated `mode.cfg`.                                            |
| **T-13** | Playback selector integration                   | 🔄 PARTIAL | T-02,T-07,T-09,T-10 | Selection: try preferred bank → fallback bank; wrap; stop/reset VS1053 if needed, then play.                                                                                                           | Integrated player                       | Human-first vs generated-first works end-to-end.                            |
| **T-14** | Serial FS: protocol skeleton                    | 📋 TODO | —                   | Implement `FS_BEGIN/FS_PUT/FS_DATA/FS_DONE/FS_COMMIT/FS_ABORT/CFG_RELOAD`.                                                                                                                             | State machine + docs                    | Happy-path file upload works to staging.                                    |
| **T-15** | Staging & atomic swap                           | 📋 TODO | T-14                | Write to `/_staging`, verify CRC32, then rename into place; optional `/_rollback`.                                                                                                                     | Filesystem ops                          | Power loss during transfer leaves previous state intact.                    |
| **T-16** | Maintenance mode                                | 📋 TODO | T-14                | During update: ignore presses; stop audio; resume after `FS_COMMIT/ABORT`.                                                                                                                             | Gating                                  | No user input processed mid-update.                                         |
| **T-17** | `CFG_RELOAD` command                            | 📋 TODO | T-07,T-05           | Re-parse `mode.cfg`/`buttons.csv`; flush playlist caches; keep audio stopped.                                                                                                                          | Reload handler                          | Config changes apply without reboot.                                        |
| **M4**   | **Milestone: Update path (device)**             | 📋 0%  | T-14..T-17          | —                                                                                                                                                                                                      | Upload + atomic swap + reload           | Verified CRC, no partial state on failure.                                  |
| **T-18** | Desktop: device discovery + flash               | 📋 TODO | M4                  | Bundle Arduino CLI; auto-detect board/port; stream logs; allow `.hex` direct upload.                                                                                                                   | "Flash firmware" action                 | Flash succeeds on Win/Mac with logs.                                        |
| **T-19** | Desktop: SD sync over serial FS                 | 📋 TODO | M4                  | Implement client side of protocol; per-file CRC; resume by file; manifest summary.                                                                                                                     | "Sync SD" action                        | SD updates complete; device reports `OK`; reload applied.                   |
| **T-20** | Desktop: self-test                              | 📋 TODO | T-18,T-19           | After sync, ask device to play a known short clip; show pass/fail.                                                                                                                                     | Self-test button                        | Hear clip / receive device OK.                                              |
| **M5**   | **Milestone: Desktop app**                      | 📋 0%  | T-18..T-20          | —                                                                                                                                                                                                      | One-click "Update Device"               | Flash + SD sync + self-test all via UI.                                     |
| **T-21** | Fault injection: missing playlists              | 📋 TODO | M2                  | Remove one/both playlists; verify strict behavior & logs.                                                                                                                                              | Test report                             | Behavior matches spec.                                                      |
| **T-22** | Fault injection: power-loss on update           | 📋 TODO | M4                  | Cut power during `FS_DATA` and during `FS_COMMIT`; verify rollback.                                                                                                                                    | Test report                             | Device boots with last good set; staging cleaned next boot.                 |
| **T-23** | Performance & loop timing                       | 📋 TODO | M2                  | Ensure main loop feeds VS1053; log average loop time; ≤ ~20 ms.                                                                                                                                       | Perf log                                | No audio underruns; I²C stable.                                             |
| **T-24** | Docs: Operator & Developer guides               | 📋 TODO | M5                  | Operator: SD layout, adding audio, editing playlists, flipping priority. Dev: protocol spec, file formats.                                                                                             | `/docs` + PDF                           | Docs reviewed and accurate.                                                 |
| **T-25** | Release packaging                               | 📋 TODO | M5                  | Version stamp into `/manifest.json`; tag repo; produce SD starter pack.                                                                                                                                | Release bundle                          | Installable app + SD pack + firmware tag.                                   |

---

## Current Status Assessment (as of 2025-08-16)

### ✅ COMPLETED (M0 + M3 + Partial M1)
- **T-00**: Phase 0.a utility sweep - All hardcoded button counts replaced with computed constants
- **T-01**: Config parsing infrastructure - `mode.cfg` parser implemented
- **T-02**: PCF generalization - 3-chip support with proper addressing
- **T-05**: Mode config parser - Priority and strict playlist flags
- **T-10**: Priority enum system - HUMAN_FIRST/GENERATED_FIRST
- **T-11**: PERIOD triple-press detection - Working with 1200ms window
- **T-12**: Priority persistence - Saves to mode.cfg and announces

### 🚧 IN PROGRESS (M1 Completion)
- **T-03**: `buttons.csv` parser - Structure ready, needs PCF input format parsing
- **T-13**: Playback selector - Basic priority system works, needs playlist integration

### 📋 NEXT UP (M1 → M2)
- **T-04**: Hardware-agnostic routing - Connect parsed buttons.csv to key resolution
- **T-06**: M3U playlist reader - Core playlist parsing engine
- **T-07**: Playlist caching - Memory management for loaded playlists

### 🎯 MILESTONE PROGRESS
- **M0**: ✅ 100% Complete
- **M1**: 🚧 75% Complete (T-03, T-04 remaining)
- **M2**: 📋 0% Complete (playlist engine)
- **M3**: ✅ 100% Complete (priority mode)
- **M4-M7**: 📋 0% Complete (future phases)

### 📁 DELIVERABLES READY
- ✅ Strict-mode SD card structure (`sd_strict_mode/`)
- ✅ Complete playlist generation (`generate_strict_playlists.py`)
- ✅ SD setup tooling (`setup_sd_card.py`)
- ✅ Calibrated button mappings (`config/buttons.csv`)
- ✅ Priority mode configuration (`config/mode.cfg`)

---

## Cross-cutting Notes

* **KEY naming:** use slugs like `PERIOD`, `SPACE`, `YES` (avoid raw punctuation for folder/playlist names).
* **Strict mode:** set `STRICT_PLAYLISTS=1`; no dir scanning fallback.
* **Logging:** always include chip index and I²C addr: `pcf2@0x22:pin10`.
* **Addresses:** set `PCF_ADDR[]` to *actual* wired addrs (e.g., `{0x20,0x21,0x22}` or `{0x20,0x21,0x24}`).
* **Content preview:** before playback, firmware prints caption from sibling `.txt` next to the selected `.mp3` (e.g., `/audio/human/U/001.txt`). If the caption file is missing, firmware logs `[CONTENT] Missing caption file: <path>`.

---

## Incremental Demo Plan

* **M1 demo:** Rewire a button; only `buttons.csv` changes. Show strict flag toggling guards.
* **M2 demo:** Change order in an `.m3u`; hear new order without reflashing.
* **M3 demo:** ✅ DONE - Triple-press `PERIOD`; hear announcement; `mode.cfg` updated.
* **M4 demo:** Push a changed playlist via serial FS; device reloads without reboot.
* **M5 demo:** One-click desktop "Update Device" (flash + SD sync + self-test).
* **M6 demo:** Pull power during update; previous SD content intact on reboot.
