#!/usr/bin/env python3
import argparse
from pathlib import Path
import re

BASE_KEYS = set([*(chr(ord('A')+i) for i in range(26)), 'YES','NO','WATER','SHIFT','SPACE','PERIOD'])
KEY_NAME_RE = re.compile(r'^[A-Z_]+$')


def list_candidate_keys(root: Path) -> set:
    keys = set()
    audio = root / 'audio'
    # Discover keys from folder names under audio/*/
    for bank in ('human','generated'):
        bank_dir = audio / bank
        if not bank_dir.exists():
            continue
        for p in bank_dir.glob('*'):
            if p.is_dir():
                key = p.name.upper()
                if KEY_NAME_RE.match(key):
                    keys.add(key)
    # Also discover from playlists present
    for pl in (root / 'mappings' / 'playlists').glob('*_*.m3u'):
        name = pl.stem
        if '_' not in name:
            continue
        key, _ = name.rsplit('_', 1)
        key = key.upper()
        if KEY_NAME_RE.match(key):
            keys.add(key)
    return keys


def ensure_dir(p: Path):
    p.mkdir(parents=True, exist_ok=True)


def move_into_generated(root: Path, key: str) -> int:
    """Move any existing audio for key from any bank except generated into generated/KEY.
    Returns number of files moved or consolidated.
    """
    audio = root / 'audio'
    gen_dir = audio / 'generated' / key
    ensure_dir(gen_dir)
    moved = 0

    # Collect existing indices in generated to avoid collisions
    existing = sorted([int(x.stem) for x in gen_dir.glob('*.mp3') if x.stem.isdigit()])
    next_idx = existing[-1] + 1 if existing else 1

    def add_file(src: Path):
        nonlocal next_idx, moved
        # Keep numbering if already 3-digit and free; else append next
        try:
            n = int(src.stem)
            target = gen_dir / f"{n:03d}{src.suffix.lower()}"
            if not target.exists():
                src.replace(target)
                moved += 1
                return
        except Exception:
            pass
        # assign next available index
        while True:
            target = gen_dir / f"{next_idx:03d}{src.suffix.lower()}"
            next_idx += 1
            if not target.exists():
                src.replace(target)
                moved += 1
                return

    # Move from human/KEY and any stray locations under audio/*/KEY
    for bank in ('human',):
        src_dir = audio / bank / key
        if src_dir.exists():
            for mp3 in sorted(src_dir.glob('*.mp3')):
                add_file(mp3)
    # If there are accidental mixed-case folders, handle them too
    for bank in ('human','generated'):
        bank_dir = audio / bank
        if bank_dir.exists():
            for p in bank_dir.glob('*'):
                if p.is_dir() and p.name.upper() == key and p.name != key:
                    for mp3 in sorted(p.glob('*.mp3')):
                        add_file(mp3)
                    # remove empty dir if becomes empty
                    try:
                        if not any(p.iterdir()):
                            p.rmdir()
                    except Exception:
                        pass

    return moved


def write_playlists(root: Path, key: str):
    playlists = root / 'mappings' / 'playlists'
    ensure_dir(playlists)
    gen_dir = root / 'audio' / 'generated' / key
    human_dir = root / 'audio' / 'human' / key

    # Generated playlist from files present
    gen_entries = [f"generated/{key}/{p.name}" for p in sorted(gen_dir.glob('*.mp3'))]
    (playlists / f"{key}_generated.m3u").write_text('\n'.join(gen_entries) + ('\n' if gen_entries else ''), encoding='utf-8')

    # Human playlist: list existing files if present, else create empty file
    human_entries = [f"human/{key}/{p.name}" for p in sorted(human_dir.glob('*.mp3'))]
    (playlists / f"{key}_human.m3u").write_text('\n'.join(human_entries) + ('\n' if human_entries else ''), encoding='utf-8')


def update_index(root: Path, keys: set):
    index_csv = root / 'mappings' / 'index.csv'
    ensure_dir(index_csv.parent)
    lines = []
    if index_csv.exists():
        lines = index_csv.read_text(encoding='utf-8', errors='ignore').splitlines()
    out = []
    if lines:
        # keep header as-is
        out.append(lines[0])
    else:
        out.append('KEY,HUMAN_PLAYLIST,GENERATED_PLAYLIST')
    present = set()
    for raw in lines[1:]:
        parts = [p.strip() for p in raw.split(',')]
        if len(parts) >= 3:
            present.add(parts[0].upper())
            out.append(raw)
    for key in sorted(keys):
        if key not in present:
            out.append(f"{key},mappings/playlists/{key}_human.m3u,mappings/playlists/{key}_generated.m3u")
    index_csv.write_text('\n'.join(out) + '\n', encoding='utf-8')


def main():
    ap = argparse.ArgumentParser(description='Move phrase audio into generated/KEY and regenerate playlists/index')
    ap.add_argument('--root', required=True, help='Path to SD pack root')
    args = ap.parse_args()
    root = Path(args.root).resolve()
    if not (root / 'audio').exists():
        print('[ERR] audio/ not found under', root)
        return 2

    keys = list_candidate_keys(root)
    # Phrase/excess keys = keys not in BASE_KEYS
    phrase_keys = sorted(k for k in keys if k not in BASE_KEYS)
    total_moved = 0
    for key in phrase_keys:
        moved = move_into_generated(root, key)
        write_playlists(root, key)
        total_moved += moved
        print(f"[OK] {key}: moved {moved} files into generated and wrote playlists")

    update_index(root, set(phrase_keys))
    print(f"[DONE] Processed {len(phrase_keys)} keys. Files moved: {total_moved}")
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
