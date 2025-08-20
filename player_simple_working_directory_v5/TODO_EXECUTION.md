# Execution TODO (Device bring-up to "all buttons working")

Last updated: 2025-08-19 16:46

## Scope
Operational checklist to complete the v4 device: all buttons mapped and working, human/generated audio organized, mode toggling verified, and groundwork for playlists and desktop sync.

## Tasks

- [ ] Audit SD structure vs keys
  - Source: `SD_CARD_STRUCTURE/config/keys.csv`
  - Output: list keys that have 0 tracks in `audio/human/<KEY>/` and `audio/generated/<KEY>/`

- [ ] Organize human recordings
  - Source recordings: `C:/Users/Cypress/Documents/Coding/Buttons/Recordings`
  - Destination: `player_simple_working_directory_v4/SD_CARD_STRUCTURE/audio/human/<KEY>/001.mp3`
  - Also create `001.txt` next to each MP3 with the spoken caption for console preview

- [ ] Normalize firmware mode to current behavior
  - Edit `SD_CARD_STRUCTURE/config/mode.cfg`
  - Set `STRICT_PLAYLISTS=0` (current firmware uses directory discovery, not M3U)

- [ ] On-device verification pass
  - Upload `player_simple_working_directory_v4.ino`
  - Press each mapped button
  - Confirm logs show `[CONTENT] About to say: ...` and audio plays
  - Triple-press `PERIOD` to toggle modes; confirm announcement

- [ ] Add remaining phrase buttons (if desired)
  - Add rows to `SD_CARD_STRUCTURE/config/keys.csv` for phrases like `WHEELCHAIR`, `WALKER`, `GOOD_MORNING`
  - Map to available inputs (`pcfX:P` or `gpio:<pin>`), then add corresponding `audio/human/<KEY>/001.mp3`

## Next Milestones (optional)

- [ ] Implement playlist engine (M3U)
  - T-06..T-09: M3U reader, cache, per-key cursors
  - After implementation, set `STRICT_PLAYLISTS=1`

- [ ] Implement serial FS + desktop sync
  - Device: T-14..T-17 (FS protocol, staging, reload)
  - Desktop: T-19 minimal client to push files and trigger reload

## Notes
- Firmware source of truth: `player_simple_working_directory_v4/player_simple_working_directory_v4.ino`
- SD pack used for testing: `player_simple_working_directory_v4/SD_CARD_STRUCTURE/`
- Keys file used by firmware in this build: `/config/keys.csv` (on SD)
