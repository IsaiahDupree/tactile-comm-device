#!/usr/bin/env python3
"""
Regenerate ONLY the 'generated' audio bank for v5 with a specified voice ID,
mirroring v4's SD_CARD_STRUCTURE but optimized for SdFat (8.3 root name).

- Input vocabulary: repo-root `wordlist` (JSON)
- Output root: `player_simple_working_directory_v5/SD_CARD_STRUCTURE/audio/GENERA~1/`
- Folders created: letters A..Z and phrase keys (PERIOD, SPACE, YES, NO, WATER, SHIFT)
- Filenames: 001.mp3, 002.mp3, ...

Usage examples:
  python regenerate_generated_audio_v5.py --all
  python regenerate_generated_audio_v5.py --letters A,B,C
  python regenerate_generated_audio_v5.py --phrases PERIOD,SPACE
  python regenerate_generated_audio_v5.py --voice RILOU7YmBhvwJGDGjNmP --all

Notes:
- API key is read by generate_audio.py from environment or .env file in repo root.
- Default voice comes from generate_audio.DEFAULT_VOICE_ID; can be overridden via --voice.
- By default, existing files will be overwritten (use --no-force to skip existing files).
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import time
import sys

# Ensure repo root is importable
_repo_root = Path(__file__).resolve().parents[1]
if str(_repo_root) not in sys.path:
    sys.path.insert(0, str(_repo_root))

from generate_audio import generate_audio, DEFAULT_VOICE_ID

# Paths
V5_AUDIO_GEN_ROOT = Path(__file__).resolve().parent / "SD_CARD_STRUCTURE" / "audio" / "GENERA~1"
WORDLIST_PATH = _repo_root / "wordlist"

# Phrase key normalization: map wordlist keys to on-disk folder names
# v4 uses uppercase for phrases and SHIFT directory, so we normalize to upper.

def normalize_dir_name(key: str) -> str:
    # For letters keep as single uppercase letter; for phrases use uppercase token
    if len(key) == 1 and key.isalpha():
        return key.upper()
    return key.upper()


def iter_generated_entries(wordlist: dict, target_letters: set[str] | None, target_phrases: set[str] | None):
    # Letters
    letters = wordlist.get("letters", {})
    for letter, banks in letters.items():
        if target_letters is not None and letter.upper() not in target_letters:
            continue
        words = list(banks.get("generated", []) or [])
        yield (normalize_dir_name(letter), words)

    # Phrases
    phrases = wordlist.get("phrases", {})
    for phrase_key, banks in phrases.items():
        norm = normalize_dir_name(phrase_key)
        if target_phrases is not None and norm not in target_phrases:
            continue
        texts = list(banks.get("generated", []) or [])
        yield (norm, texts)


def _write_sidecar_txt(out_dir: Path, index: int, text: str, overwrite: bool) -> None:
    txt_path = out_dir / f"{index:03d}.txt"
    if txt_path.exists() and not overwrite:
        return
    content = f"# {index:03d}.mp3 should contain: {text}\n"
    txt_path.write_text(content, encoding='utf-8')


def regenerate_generated(voice_id: str, model_id: str, stability: float, similarity: float,
                         style: float | None, use_speaker_boost: bool,
                         letters: set[str] | None, phrases: set[str] | None,
                         force: bool, sleep_s: float, txt_only: bool, txt_overwrite: bool):
    # Ensure root exists
    V5_AUDIO_GEN_ROOT.mkdir(parents=True, exist_ok=True)

    # Load wordlist
    if not WORDLIST_PATH.exists():
        print(f"[ERR] wordlist not found at {WORDLIST_PATH}")
        return 2
    with open(WORDLIST_PATH, 'r', encoding='utf-8') as f:
        wordlist = json.load(f)

    total = 0
    written = 0

    print("=== Regenerating 'generated' audio for v5 ===")
    print(f"Output root: {V5_AUDIO_GEN_ROOT}")
    print(f"Voice ID: {voice_id}")

    for dir_name, items in iter_generated_entries(wordlist, letters, phrases):
        if not items:
            continue
        out_dir = V5_AUDIO_GEN_ROOT / dir_name
        out_dir.mkdir(parents=True, exist_ok=True)

        print(f"\n-- {dir_name} --")
        for i, text in enumerate(items, start=1):
            total += 1
            out_file = out_dir / f"{i:03d}.mp3"
            # Always ensure sidecar .txt reflects the intended content
            _write_sidecar_txt(out_dir, i, text, overwrite=txt_overwrite or force)

            if txt_only:
                # Skip audio synthesis when only generating sidecars
                continue

            if out_file.exists() and not force:
                print(f"  [SKIP] {out_file.name} exists")
                continue
            ok = generate_audio(
                text=text,
                voice_id=voice_id,
                output_file=str(out_file),
                model_id=model_id,
                stability=stability,
                similarity_boost=similarity,
                style=style,
                use_speaker_boost=use_speaker_boost,
            )
            if ok:
                written += 1
            time.sleep(sleep_s)

    print(f"\n=== Done: wrote {written}/{total} files ===")
    print("Files are ready under SD_CARD_STRUCTURE/audio/GENERA~1/")
    return 0 if written > 0 else 1


def parse_args():
    ap = argparse.ArgumentParser(description="Regenerate 'generated' audio bank for v5 with SdFat-friendly paths and write sidecar .txt prompts")
    ap.add_argument('--voice', default=DEFAULT_VOICE_ID, help='Voice ID to use (default from generate_audio)')
    ap.add_argument('--model', default='eleven_monolingual_v1', help='Model ID (default: eleven_monolingual_v1)')
    ap.add_argument('--stability', type=float, default=0.5, help='Voice stability (0.0-1.0)')
    ap.add_argument('--similarity', type=float, default=0.85, help='Voice similarity boost (0.0-1.0)')
    ap.add_argument('--style', type=float, default=None, help='Optional style (0.0-1.0)')
    ap.add_argument('--speaker-boost', type=int, choices=[0,1], default=1, help='Use speaker boost (1) or not (0)')

    group = ap.add_mutually_exclusive_group(required=True)
    group.add_argument('--all', action='store_true', help='Regenerate for all letters and phrases')
    group.add_argument('--letters', help='Comma-separated letters (e.g., A,B,C)')
    group.add_argument('--phrases', help='Comma-separated phrases (e.g., PERIOD,SPACE,YES)')

    ap.add_argument('--no-force', action='store_true', help='Do not overwrite existing MP3 files')
    ap.add_argument('--txt-only', action='store_true', help='Only write sidecar .txt files without generating audio')
    ap.add_argument('--no-txt-overwrite', action='store_true', help='Do not overwrite existing .txt sidecars')
    ap.add_argument('--sleep', type=float, default=0.6, help='Delay between API calls (seconds)')
    return ap.parse_args()


def main():
    args = parse_args()

    letters: set[str] | None = None
    phrases: set[str] | None = None
    if args.all:
        letters = None
        phrases = None
    elif args.letters:
        letters = {t.strip().upper() for t in args.letters.split(',') if t.strip()}
        phrases = set()
    elif args.phrases:
        letters = set()
        phrases = {normalize_dir_name(t.strip()) for t in args.phrases.split(',') if t.strip()}

    rc = regenerate_generated(
        voice_id=args.voice,
        model_id=args.model,
        stability=args.stability,
        similarity=args.similarity,
        style=args.style,
        use_speaker_boost=bool(args.speaker_boost),
        letters=letters,
        phrases=phrases,
        force=not args.no_force,
        sleep_s=args.sleep,
        txt_only=args.txt_only,
        txt_overwrite=not args.no_txt_overwrite,
    )
    return rc


if __name__ == '__main__':
    raise SystemExit(main())
