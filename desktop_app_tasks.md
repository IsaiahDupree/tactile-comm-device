# Tactile Communication Device - Desktop App Development Tasks

This document outlines the development plan for a comprehensive UI application that will interface with the tactile communication device.

## Application Goals

* Allow users to edit per-letter **Human (orange)** and **Generated (blue)** audio mappings
* Display **device + SD card status** with a one-click health check
* Mirror the **physical layout** of the device (7×4 grid + top quick-phrases)
* Support unlimited mappings per letter through playlist management

## Development Milestones

### Overview

**M0** groundwork → **M1** device link → **M2** SD model → **M3** grid UI → **M4** editors & playlists → **M5** status/health → **M6** sync/apply → **M7** polish & tests

### M0 — Groundwork & UX

1. **Choose stack & project scaffold** ✅
   - Selected Tauri + React with TypeScript
   - Set up routing, state management (Zustand), and file dialog capabilities
   - Project repository initialized with proper linting and testing configuration

2. **Design tokens & color system** ✅
   - Defined color system with **Orange = Human**, **Blue = Generated**
   - Created neutral gray palette for UI elements
   - Established accessible contrast ratios
   - Selected icon set including human (👤) and computer (💻) symbols

3. **Wireframes that mirror hardware layout** ✅
   - Created 7×4 grid wireframe (A-Z plus "-" and ".")
   - Added top row for quick phrases (YES, NO, WATER, HOW ARE YOU)
   - Layout exactly matches physical device positioning

### M1 — Device link & protocol shell

4. **Serial transport & device discovery** ✅
   - Implemented port picker dropdown
   - Created connect/disconnect functionality
   - Added keepalive ping with timeout detection

5. **Implement/consume minimal device API** ⚠️ (In Progress)
   - Implemented core commands:
     - `GET_INFO` ✅
     - `LIST_FILES` ✅
     - `READ_FILE` ✅
     - `PUT_FILE` ⚠️ (Testing needed)
     - `CFG_RELOAD` ✅
     - `TEST_PLAY` ⚠️ (Partially working)
   - Added error handling for device communication

### M2 — SD data model (strict mode)

6. **Model + parser for SD layout (strict)** ⚠️ (In Progress)
   - Created parsers for:
     - `/config/mode.cfg` ✅
     - `/config/buttons.csv` ✅
     - `/mappings/playlists/*` ⚠️ (Partially implemented)
   - Started work on folder tree structure for `/audio/human` and `/audio/generated`

7. **M3U loader/writer (per key, per bank)** ⚠️ (In Progress)
   - Built parser for UTF-8 M3U files that handles comment lines
   - Created serializer that maintains proper line endings
   - Need to complete round-trip testing

8. **Strict validator** ❌ (Not Started)
   - Need to implement validation system to check:
     - M3U line paths exist within correct bank
     - Detection of missing files
     - Detection of orphan files
     - Identification of duplicate entries
     - Flagging of empty playlists

### M3 — Grid UI that matches the device

9. **Grid renderer (7×4) + quick-phrase row** ✅
   - Implemented responsive grid layout
   - Created quick-phrase row that matches physical device
   - Added placeholder styling for letter tiles

10. **Tile component** ⚠️ (In Progress)
    - Created basic tile component with click handler
    - Added human/generated count indicators
    - Need to implement hover state with last-played index

11. **Legend + color accessibility** ❌ (Not Started)
    - Need to implement legend components
    - Add proper ARIA labels
    - Test color-blind safe contrast

### M4 — Editors & playlist management

12. **Letter editor drawer** ❌ (Not Started)
    - Need to implement drawer component with two tabs:
      - Human (orange)
      - Generated (blue)
    - Add sortable list with drag-reorder functionality

13. **Add track (file picker + copy)** ❌ (Not Started)
    - Need to implement file picker for MP3 selection
    - Create file copy mechanism to proper SD card location
    - Add auto-numbering to prevent filename collisions

14. **Bulk import** ❌ (Not Started)
    - Need to implement drag-drop zone for multiple files
    - Create staging interface for multiple imports
    - Add sorting options (e.g., by filename)

15. **Audio preview (local)** ❌ (Not Started)
    - Need to implement HTML5 audio player component
    - Add integration with device `TEST_PLAY` command

16. **Per-key notes / labels (optional)** ❌ (Not Started)
    - Need to create JSON storage for friendly labels
    - Add UI for editing custom labels per key

### M5 — Status & health

17. **Device status panel** ⚠️ (In Progress)
    - Created basic connection status indicator
    - Added firmware version display
    - Need to implement:
      - Priority mode display
      - Strict flag indicator
      - PCF detection
      - SD space monitoring

18. **SD health check** ❌ (Not Started)
    - Need to implement validation runner
    - Create badge system for key status
    - Add shortcut to jump to editor for problem keys

19. **Priority mode control** ⚠️ (In Progress)
    - Created toggle UI component
    - Need to connect to device API for actual mode change

### M6 — Apply/sync changes

20. **Change set & diff view** ❌ (Not Started)
    - Need to implement change tracking system
    - Create diff visualization UI
    - Add confirmation dialog with item selection

21. **Uploader with staging & CRC** ❌ (Not Started)
    - Need to implement staged upload system
    - Add CRC verification
    - Create commit/reload flow

22. **Post-sync self-test** ❌ (Not Started)
    - Need to implement test sound playback
    - Create pass/fail indicator

### M7 — Polish & tests

23. **Offline "SD folder" mode** ❌ (Not Started)
    - Need to implement local folder mode
    - Add toggle between device and folder targets

24. **Autosave & backups** ❌ (Not Started)
    - Need to implement automatic backup creation
    - Add restore functionality

25. **QA: large playlists & edge cases** ❌ (Not Started)
    - Need to conduct comprehensive testing with:
      - Large playlists (100+ entries)
      - Duplicate detection
      - Invalid paths
      - Missing audio files

26. **Packaging & first-run onboarding** ❌ (Not Started)
    - Need to create installers for Windows and Mac
    - Implement welcome experience explaining key concepts

## Progress Assessment

- **Complete**: 6 tasks (23%)
- **In Progress**: 7 tasks (27%)
- **Not Started**: 13 tasks (50%)

Current focus is on completing the device communication API and SD card data model before moving on to the more advanced UI components for playlist management.

## Next Steps

1. Complete the M3U loader/writer implementation
2. Finish the SD layout parser for playlists
3. Implement the strict validator for health checks
4. Complete the tile component with proper hover states and indicators
5. Begin work on the letter editor drawer

## Future Enhancements

- In-app voice clip recording
- Per-key priority override options
- Bulk import from CSV/ZIP for legacy content migration
