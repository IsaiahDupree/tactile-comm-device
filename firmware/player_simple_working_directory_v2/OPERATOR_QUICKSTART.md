---
description: Operator quickstart – add audio, edit playlists, flip priority
---

# Operator Quickstart

This is the 1‑pager for day‑to‑day tasks. Works with both legacy folders and the new strict playlists.

## 1) Add or update audio
- Plug the SD card into your computer.
- Place audio files under these folders:
  - Personal (human) recordings: `/audio/human/<KEY>/`
  - Generated (TTS) audio: `/audio/generated/<KEY>/`
- File format: `.mp3` (44.1kHz recommended). Names can be freeform.

## 2) Edit playback order (strict playlists)
- For each key, edit the two playlist files in `/mappings/playlists/`:
  - `<KEY>_human.m3u`
  - `<KEY>_generated.m3u`
- Each line is a file path relative to SD root, example:
  ```
  /audio/human/A/hello.mp3
  /audio/human/A/how_are_you.mp3
  ```
- Save the file. The device will play in the listed order.

Tip: If `STRICT_PLAYLISTS=1` in `/config/mode.cfg` and a playlist is empty, that bank is disabled for the key.

## 3) Change which voice plays first
- File: `/config/mode.cfg`
  - `PRIORITY=HUMAN_FIRST`  (personal recordings first)
  - `PRIORITY=GENERATED_FIRST` (computer voice first)
- On device: triple‑press the period button `.` within ~1.2 seconds to toggle. You will hear an announcement. The setting is saved.

## 4) Remap a physical button (no firmware changes)
- File: `/config/buttons.csv`
- Format: `pcf<chip>:<pin>,<KEY>` or `gpio:<pin>,<KEY>`
  - Examples:
    - `pcf0:00,A`
    - `pcf1:07,Water`
    - `gpio:8,Back`
- Save and either reboot or send `CFG_RELOAD` from the desktop app.

## 5) Desktop app update (recommended)
- Open the Tactile Device Manager.
- Click “Update Device”. It will:
  1) Stage files safely on the SD card
  2) Commit atomically so power loss does not corrupt data
  3) Send `CFG_RELOAD` to apply changes without reboot

## 6) Quick sanity checks
- On boot, the device logs which PCF8575 chips are online at `0x20/0x21/0x22`.
- Press a button: you should see `pcf<i>:<pin> → <KEY>` in the console.
- If audio does not play, check the playlist files and `STRICT_PLAYLISTS` setting.

That’s it. You can change wiring and content entirely from files on the SD card. No reflashing required.
