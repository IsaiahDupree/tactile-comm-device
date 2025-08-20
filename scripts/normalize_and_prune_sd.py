#!/usr/bin/env python3
import argparse
from pathlib import Path

ALLOWED_BANKS = {"human", "generated"}


def ensure_upper_key(name: str) -> str:
    return name.upper()


def parse_playlist_filename(p: Path):
    stem = p.stem  # e.g., A_human
    if '_' not in stem:
        return None, None
    key, bank = stem.rsplit('_', 1)
    return key, bank


def normalize_playlists(root: Path) -> int:
    changed = 0
    audio_root = root / 'audio'
    playlists_dir = root / 'mappings' / 'playlists'
    index_csv = (root / 'mappings' / 'index.csv')

    playlists_dir.mkdir(parents=True, exist_ok=True)

    # Pass 1: rename playlist files for key case and PERIOD
    for pl in list(playlists_dir.glob('*.m3u')):
        key, bank = parse_playlist_filename(pl)
        if not key or not bank:
            continue
        norm_key = 'PERIOD' if key == '.' else ensure_upper_key(key)
        norm_bank = bank.lower()
        new_name = f"{norm_key}_{norm_bank}.m3u"
        target = playlists_dir / new_name
        if pl.name != new_name:
            if target.exists():
                pl.unlink()  # remove duplicate old variant
            else:
                pl.rename(target)
            changed += 1

    # Pass 2: rewrite playlist contents and prune missing
    for pl in playlists_dir.glob('*.m3u'):
        key, bank = parse_playlist_filename(pl)
        if not key or not bank:
            continue
        key_norm = 'PERIOD' if key == '.' else ensure_upper_key(key)
        try:
            lines = pl.read_text(encoding='utf-8', errors='ignore').splitlines()
        except Exception:
            lines = []
        out = []
        modified = False
        for raw in lines:
            s = raw.strip()
            if not s or s.startswith('#'):
                # preserve comments and blanks
                out.append(raw)
                continue
            # strip any BOM
            if s and ord(s[0]) == 0xFEFF:
                s = s.lstrip('\ufeff')
                modified = True
            # strip leading 'audio/' if present
            if s.startswith('audio/'):
                s = s[len('audio/'):]
                modified = True
            parts = s.split('/')
            if len(parts) != 3:
                modified = True
                continue
            bank_part, key_part, file_part = parts
            bank_part = bank_part.lower()
            key_part_norm = 'PERIOD' if key_part == '.' else ensure_upper_key(key_part)
            rel = f"{bank_part}/{key_part_norm}/{file_part}"
            full = audio_root / rel
            if full.exists():
                out.append(rel)
                if bank_part not in ALLOWED_BANKS or key_part_norm != key_norm:
                    modified = True
            else:
                modified = True
        if modified:
            try:
                pl.write_text('\n'.join(out) + '\n', encoding='utf-8')
                changed += 1
            except Exception:
                pass

    # Pass 3: update index.csv to use normalized playlist filenames and uppercase keys
    if index_csv.exists():
        try:
            lines = index_csv.read_text(encoding='utf-8', errors='ignore').splitlines()
        except Exception:
            lines = []
        out = []
        hdr_done = False
        modified = False
        for raw in lines:
            if not hdr_done:
                out.append(raw)
                hdr_done = True
                continue
            if not raw.strip() or raw.lstrip().startswith('#'):
                out.append(raw)
                continue
            parts = [p.strip() for p in raw.split(',')]
            if len(parts) < 3:
                out.append(raw)
                continue
            key = parts[0]
            # Drop '.' key entirely
            if key == '.':
                modified = True
                continue
            key = ensure_upper_key(key)
            human_pl = (root / f"mappings/playlists/{key}_human.m3u")
            gen_pl = (root / f"mappings/playlists/{key}_generated.m3u")
            # Only keep row if both playlists exist
            if human_pl.exists() and gen_pl.exists():
                out.append(f"{key},mappings/playlists/{key}_human.m3u,mappings/playlists/{key}_generated.m3u")
                modified = True
            else:
                # prune row
                modified = True
        if modified:
            try:
                index_csv.write_text('\n'.join(out) + '\n', encoding='utf-8')
                changed += 1
            except Exception:
                pass

    # Pass 4: update config/keys.csv to uppercase and PERIOD
    keys_csv = root / 'config' / 'keys.csv'
    if keys_csv.exists():
        try:
            lines = keys_csv.read_text(encoding='utf-8', errors='ignore').splitlines()
        except Exception:
            lines = []
        out = []
        modified = False
        for i, raw in enumerate(lines):
            if i == 0:
                out.append(raw)
                continue
            if not raw.strip():
                out.append(raw)
                continue
            parts = [p.strip() for p in raw.split(',')]
            if not parts:
                out.append(raw)
                continue
            parts[0] = 'PERIOD' if parts[0] == '.' else ensure_upper_key(parts[0])
            out.append(','.join(parts))
            modified = True
        if modified:
            try:
                keys_csv.write_text('\n'.join(out) + '\n', encoding='utf-8')
                changed += 1
            except Exception:
                pass

    return changed


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--root', required=True, help='Path to SD pack root (folder containing audio/, mappings/, config/)')
    args = ap.parse_args()
    root = Path(args.root).resolve()
    if not (root / 'audio').exists():
        print('[ERR] audio/ not found under', root)
        return 2
    changed = normalize_playlists(root)
    print(f'[OK] Normalization complete. Files changed: {changed}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
