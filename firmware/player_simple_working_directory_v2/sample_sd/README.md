# sample_sd

Starter SD layout for quick testing with strict playlists and hardware-agnostic mapping.

Structure:
```
/config/
  buttons.csv
  mode.cfg
/mappings/
  playlists/
    A_human.m3u
    A_generated.m3u
/audio/
  human/A/
  generated/A/
```

Notes:
- Paths in .m3u are absolute-from-root (leading slash) for clarity.
- Add your own .mp3 files into `/audio/human/A/` and `/audio/generated/A/`.
