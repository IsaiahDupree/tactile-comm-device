#!/usr/bin/env python3
import argparse
from pathlib import Path


def read_declared_keys(config_dir: Path) -> set:
    keys = set()
    keys_csv = config_dir / 'keys.csv'
    if keys_csv.exists():
        for line in keys_csv.read_text(encoding='utf-8', errors='ignore').splitlines():
            s = line.strip()
            if not s or s.startswith('#'):
                continue
            parts = [p.strip() for p in s.split(',')]
            if parts and parts[0].upper() != 'KEY':
                keys.add(('PERIOD' if parts[0] == '.' else parts[0].upper()))
    buttons_csv = config_dir / 'buttons.csv'
    if buttons_csv.exists():
        for line in buttons_csv.read_text(encoding='utf-8', errors='ignore').splitlines():
            s = line.strip()
            if not s or s.startswith('#'):
                continue
            parts = [p.strip() for p in s.split(',')]
            if len(parts) >= 2:
                key = parts[-1]
                if key:
                    keys.add(('PERIOD' if key == '.' else key.upper()))
    return keys


def ensure_declared_playlists(root: Path) -> int:
    changed = 0
    config = root / 'config'
    playlists = root / 'mappings' / 'playlists'
    playlists.mkdir(parents=True, exist_ok=True)
    keys = read_declared_keys(config)

    # Ensure playlist files exist (empty is fine) for both banks
    for key in keys:
        for bank in ('human','generated'):
            pl = playlists / f"{key}_{bank}.m3u"
            if not pl.exists():
                pl.write_text('', encoding='utf-8')
                changed += 1

    # Ensure index.csv contains entries for all declared keys
    index_csv = root / 'mappings' / 'index.csv'
    index_csv.parent.mkdir(parents=True, exist_ok=True)
    existing_lines = []
    if index_csv.exists():
        existing_lines = index_csv.read_text(encoding='utf-8', errors='ignore').splitlines()
    out = []
    if existing_lines:
        header = existing_lines[0]
    else:
        header = 'KEY,HUMAN_PLAYLIST,GENERATED_PLAYLIST'
    out.append(header)
    present = set()
    for raw in existing_lines[1:]:
        parts = [p.strip() for p in raw.split(',')]
        if len(parts) >= 3:
            present.add(parts[0].upper())
            out.append(raw)
    for key in sorted(keys):
        if key not in present:
            out.append(f"{key},mappings/playlists/{key}_human.m3u,mappings/playlists/{key}_generated.m3u")
            changed += 1
    index_csv.write_text('\n'.join(out) + '\n', encoding='utf-8')
    return changed


def main():
    ap = argparse.ArgumentParser(description='Ensure playlists/index exist for all declared keys')
    ap.add_argument('--root', required=True, help='Path to SD pack root')
    args = ap.parse_args()
    root = Path(args.root).resolve()
    if not (root / 'config').exists():
        print('[ERR] config/ not found under', root)
        return 2
    changed = ensure_declared_playlists(root)
    print(f'[OK] Ensured declared playlists and index. Files changed: {changed}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
