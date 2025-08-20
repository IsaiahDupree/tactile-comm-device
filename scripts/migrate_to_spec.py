#!/usr/bin/env python3
import argparse
import re
from pathlib import Path

REL_AUDIO_PREFIX = ('human/', 'generated/')

PERIOD_PLAYLIST_CANDIDATES = [
    '._human.m3u',
    '._generated.m3u',
    '. _human.m3u',
    '. _generated.m3u',
]


def fix_mode_cfg(cfg_path: Path) -> bool:
    if not cfg_path.exists():
        return False
    txt = cfg_path.read_text(encoding='utf-8', errors='ignore').splitlines()
    out = []
    changed = False
    have_priority_mode = False
    have_strict = False
    for line in txt:
        s = line.strip()
        if s.startswith('PRIORITY='):
            # rename to PRIORITY_MODE
            val = s.split('=', 1)[1]
            out.append(f'PRIORITY_MODE={val}')
            changed = True
            have_priority_mode = True
        else:
            if s.startswith('PRIORITY_MODE='):
                have_priority_mode = True
            if s.startswith('STRICT_PLAYLISTS='):
                have_strict = True
            out.append(line)
    if not have_priority_mode:
        out.append('PRIORITY_MODE=HUMAN_FIRST')
        changed = True
    if not have_strict:
        out.append('STRICT_PLAYLISTS=1')
        changed = True
    if changed:
        cfg_path.write_text('\n'.join(out) + '\n', encoding='utf-8')
    return changed


def rewrite_playlist_lines(pl_path: Path) -> bool:
    changed = False
    lines = pl_path.read_text(encoding='utf-8', errors='ignore').splitlines()
    new_lines = []
    for raw in lines:
        line = raw.strip()
        if not line or line.startswith('#'):
            new_lines.append(raw)
            continue
        if line.startswith('audio/'):
            line = line[len('audio/'):]
            changed = True
            # keep comments/structure by replacing raw with normalized path
            new_lines.append(line)
        else:
            new_lines.append(raw if raw == line else line)
            changed = changed or (raw != line)
    if changed:
        pl_path.write_text('\n'.join(new_lines) + '\n', encoding='utf-8')
    return changed


def rename_period_playlists(playlists_dir: Path) -> int:
    count = 0
    # Direct candidates like '._human.m3u'
    for name in PERIOD_PLAYLIST_CANDIDATES:
        p = playlists_dir / name
        if p.exists():
            if 'human' in name:
                target = playlists_dir / 'PERIOD_human.m3u'
            else:
                target = playlists_dir / 'PERIOD_generated.m3u'
            if not target.exists():
                p.rename(target)
                count += 1
    # Also handle files like '._something.m3u' with leading dot and underscore
    for p in playlists_dir.glob('.*.m3u'):
        # skip hidden files unrelated
        if p.name.lower().endswith('_human.m3u') or p.name.lower().endswith('_generated.m3u'):
            bank = 'human' if p.name.lower().endswith('_human.m3u') else 'generated'
            target = playlists_dir / f'PERIOD_{bank}.m3u'
            if not target.exists():
                p.rename(target)
                count += 1
    return count


def update_index_csv(index_csv: Path) -> bool:
    if not index_csv.exists():
        return False
    lines = index_csv.read_text(encoding='utf-8', errors='ignore').splitlines()
    out = []
    changed = False
    header_done = False
    for raw in lines:
        line = raw
        if not header_done:
            out.append(raw)
            header_done = True
            continue
        if not raw.strip() or raw.lstrip().startswith('#'):
            out.append(raw)
            continue
        parts = [p.strip() for p in raw.split(',')]
        if len(parts) < 3:
            out.append(raw)
            continue
        key, human_pl, gen_pl = parts[0], parts[1], parts[2]
        # Normalize key '.' -> 'PERIOD'
        if key == '.':
            key = 'PERIOD'
            changed = True
        # Normalize playlist filenames
        human_pl = human_pl.replace('._human.m3u', 'PERIOD_human.m3u')
        gen_pl = gen_pl.replace('._generated.m3u', 'PERIOD_generated.m3u')
        # Ensure playlists path points to mappings/playlists/
        # leave as-is otherwise
        out.append(f"{key},{human_pl},{gen_pl}")
    if changed:
        index_csv.write_text('\n'.join(out) + '\n', encoding='utf-8')
    return changed


def update_keys_csv(keys_csv: Path) -> bool:
    if not keys_csv.exists():
        return False
    txt = keys_csv.read_text(encoding='utf-8', errors='ignore')
    new = txt.replace('\n.,', '\nPERIOD,')
    if new != txt:
        keys_csv.write_text(new, encoding='utf-8')
        return True
    return False


def migrate(root: Path) -> None:
    changes = 0
    # 1) mode.cfg
    changes += int(fix_mode_cfg(root / 'config' / 'mode.cfg'))
    # 2) playlists entries
    playlists_dir = root / 'mappings' / 'playlists'
    for pl in playlists_dir.glob('*.m3u'):
        changes += int(rewrite_playlist_lines(pl))
    # 3) rename PERIOD playlists
    changes += rename_period_playlists(playlists_dir)
    # 4) update index.csv and keys.csv
    changes += int(update_index_csv(root / 'mappings' / 'index.csv'))
    changes += int(update_keys_csv(root / 'config' / 'keys.csv'))
    print(f'Migration complete. Files changed/renamed: {changes}')


def main():
    ap = argparse.ArgumentParser(description='Migrate SD pack to strict spec (paths, PERIOD, mode.cfg)')
    ap.add_argument('--root', required=True, help='Path to SD pack root (e.g., tactile-comm-device/sd/SD_FUTURE_PROOF)')
    args = ap.parse_args()

    migrate(Path(args.root).resolve())


if __name__ == '__main__':
    main()
