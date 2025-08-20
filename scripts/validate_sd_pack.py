#!/usr/bin/env python3
import argparse
import json
import re
from pathlib import Path

ALLOWED_KEYS = set([
    *[chr(ord('A')+i) for i in range(26)],
    'YES','NO','WATER','SHIFT','SPACE','PERIOD'
])

ALLOWED_EXTS = {
    'audio': {'.mp3'},
    'playlists': {'.m3u'},
    'config': {'.csv', '.cfg'},
}

RELATIVE_AUDIO_RE = re.compile(r'^(human|generated)/[A-Z_]+/\d{3}\.mp3$')


def read_buttons_keys(config_dir: Path):
    keys = set()
    # Prefer keys.csv if present
    keys_csv = config_dir / 'keys.csv'
    if keys_csv.exists():
        for line in keys_csv.read_text(encoding='utf-8').splitlines():
            line=line.strip()
            if not line or line.startswith('#'): continue
            parts = [p.strip() for p in line.split(',')]
            if parts[0] == 'KEY' or parts[0].upper().startswith('#KEY'): # header
                continue
            key = parts[0]
            if key:
                keys.add(key.upper())
    # Fallback: buttons.csv legacy formats may only list keys in a second column
    buttons_csv = config_dir / 'buttons.csv'
    if buttons_csv.exists():
        for line in buttons_csv.read_text(encoding='utf-8', errors='ignore').splitlines():
            line=line.strip()
            if not line or line.startswith('#'): continue
            parts = [p.strip() for p in line.split(',')]
            if len(parts) >= 2:
                k = parts[-1]
                if k:
                    keys.add(k.upper())
    return keys


def load_playlist(path: Path):
    paths = []
    for raw in path.read_text(encoding='utf-8', errors='ignore').splitlines():
        line = raw.strip()
        if not line or line.startswith('#'):
            continue
        paths.append(line)
    return paths


def validate(root: Path, strict: bool = True) -> int:
    errors = 0
    warnings = 0

    audio = root / 'audio'
    mappings = root / 'mappings' / 'playlists'
    config = root / 'config'

    if not audio.exists():
        print('[ERR] missing /audio')
        return 1
    if not mappings.exists():
        print('[ERR] missing /mappings/playlists')
        return 1
    if not config.exists():
        print('[ERR] missing /config')
        return 1

    declared_keys = read_buttons_keys(config)
    if not declared_keys:
        print('[WARN] no keys found in config; will validate playlists present only')

    # Iterate playlist pairs
    playlist_files = list(mappings.glob('*_*.*'))
    index = {}
    for pf in playlist_files:
        name = pf.stem  # e.g., A_human
        if '_' not in name:
            continue
        key, bank = name.rsplit('_', 1)
        key = key.upper()
        bank = bank.lower()
        if bank not in {'human','generated'}:
            print(f'[ERR] bad bank in playlist name: {pf.name}')
            errors += 1
            continue
        index.setdefault(key, {})[bank] = pf

    # Validate key names
    KEY_NAME_RE = re.compile(r'^[A-Z_]+$')
    for key in index.keys():
        if not KEY_NAME_RE.match(key):
            print(f'[WARN] non-standard key name: {key}')
            warnings += 1

    # Check required playlists for declared keys
    for key in sorted(declared_keys):
        have = index.get(key, {})
        for bank in ('human','generated'):
            if bank not in have:
                msg = f'[ERR] missing playlist for {key} {bank}: {key}_{bank}.m3u'
                if strict:
                    print(msg)
                    errors += 1
                else:
                    print('[WARN]', msg)
                    warnings += 1

    # Validate playlist entries
    for key, banks in index.items():
        for bank, pl in banks.items():
            try:
                entries = load_playlist(pl)
            except Exception as e:
                print(f'[ERR] failed to read {pl}: {e}')
                errors += 1
                continue
            if not entries:
                print(f'[WARN] empty playlist: {pl.name}')
                warnings += 1
            for rel in entries:
                if rel.startswith('audio/'):
                    print(f'[ERR] playlist path should be relative to /audio, not start with audio/: {pl.name} -> {rel}')
                    errors += 1
                if not RELATIVE_AUDIO_RE.match(rel):
                    print(f'[ERR] invalid path format in {pl.name}: {rel}')
                    errors += 1
                    continue
                full = audio / rel
                if not full.exists():
                    print(f'[ERR] referenced file missing: {pl.name} -> {rel}')
                    errors += 1
                # Ensure correct bank folder
                top = rel.split('/',1)[0]
                if top != bank:
                    print(f'[ERR] bank mismatch in {pl.name}: expected {bank}/..., got {rel}')
                    errors += 1

    print(f'Validation finished: errors={errors}, warnings={warnings}')
    return 1 if errors else 0


def main():
    ap = argparse.ArgumentParser(description='Validate SD pack against strict spec')
    ap.add_argument('--root', required=True, help='Path to SD pack root')
    ap.add_argument('--best-effort', action='store_true', help='Downgrade errors to warnings for missing playlists')
    args = ap.parse_args()

    rc = validate(Path(args.root).resolve(), strict=not args.best_effort)
    raise SystemExit(rc)


if __name__ == '__main__':
    main()
