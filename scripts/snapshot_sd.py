#!/usr/bin/env python3
import argparse
import shutil
from pathlib import Path
import time

SKIP_DIRS = {"System Volume Information", "$RECYCLE.BIN"}


def copy_tree(src: Path, dst: Path):
    for p in src.rglob('*'):
        # Skip system dirs
        if any(part in SKIP_DIRS for part in p.parts):
            continue
        rel = p.relative_to(src)
        out = dst / rel
        if p.is_dir():
            out.mkdir(parents=True, exist_ok=True)
        else:
            out.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(p, out)


def main():
    ap = argparse.ArgumentParser(description='Snapshot an SD card (mounted path) to a timestamped folder')
    ap.add_argument('--src', required=True, help='Mounted SD root (e.g., D:\\)')
    ap.add_argument('--out', default='sd_packs', help='Output base dir (default: sd_packs)')
    args = ap.parse_args()

    src = Path(args.src)
    if src.drive and len(str(src)) == 2 and str(src).endswith(':'):
        # Normalize drive letter root like 'D:' -> 'D:\'
        src = Path(str(src) + '\\')
    if not src.exists():
        raise SystemExit(f"Source not found: {src}")

    ts = time.strftime('%Y%m%d-%H%M%S')
    dst = Path(args.out).resolve() / f'SD_DUMP_{ts}'
    dst.mkdir(parents=True, exist_ok=True)

    print(f'Copying from {src} to {dst} ...')
    copy_tree(src, dst)
    print('Snapshot complete')


if __name__ == '__main__':
    main()
