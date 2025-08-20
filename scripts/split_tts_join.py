#!/usr/bin/env python3
"""
Split a long SHIFT mapping text into 4 parts, synthesize each with ElevenLabs,
then join into one WAV output. Optionally also write the 4 parts as individual WAVs.

Usage:
  python scripts/split_tts_join.py \
    --input-text-file "player_simple_working_directory_v5/SD_CARD_STRUCTURE/audio/GENERA~1/SHIFT/004.txt" \
    --out-dir "test_output/shift_split" \
    --voice-id RILOU7YmBhvwJGDGjNmP \
    --model-id eleven_monolingual_v1 \
    --combined-out "player_simple_working_directory_v5/SD_CARD_STRUCTURE/audio/GENERA~1/SHIFT/004_combined.wav"

Notes:
- ELEVENLABS_API_KEY must be set in your environment.
- We request WAV from the API so we can safely concatenate without ffmpeg.
- You can convert the combined WAV to MP3 with ffmpeg or another tool if needed.
"""

import argparse
import os
import re
import sys
import time
import json
import tempfile
from pathlib import Path
import wave
import requests

ELEVEN_BASE_URL = "https://api.elevenlabs.io/v1"


def read_text(path: str) -> str:
    p = Path(path)
    return p.read_text(encoding="utf-8").strip()


def split_into_four_parts(full_text: str) -> list[str]:
    """
    Split by letter anchors into 4 logical parts:
      Part 1: preamble + A–G
      Part 2: H–N
      Part 3: O–T
      Part 4: U–Z + closing reminders
    We locate occurrences of " A:", " B:", ..., " Z:" (literal pattern with space then letter then colon).
    If any anchor is missing, we fall back to an even quarter split by length.
    """
    anchors = {}
    for ch in "ABCDEFGHIJKLMNOPQRSTUVWXYZ":
        m = re.search(rf"\b{ch}:", full_text)
        if m:
            anchors[ch] = m.start()

    needed_groups = [("A", "H"), ("H", "O"), ("O", "U"), ("U", None)]

    if not all(k in anchors for k in ["A", "H", "O", "U"]):
        # Fallback: length-based quarters
        n = len(full_text)
        q = n // 4
        return [
            full_text[0:q],
            full_text[q:2*q],
            full_text[2*q:3*q],
            full_text[3*q:]
        ]

    parts = []
    start_idx = 0
    # Ensure preamble goes into first part
    for start_letter, next_letter in needed_groups:
        seg_start = anchors[start_letter] if start_letter in anchors else start_idx
        if start_letter == "A":
            seg_start = min(seg_start, anchors.get("A", seg_start))
            seg_start = min(seg_start, len(full_text))
            # part 1 starts from 0 (preamble) to before H
            seg_begin = 0
        else:
            seg_begin = anchors.get(start_letter, start_idx)

        if next_letter is None:
            seg_end = len(full_text)
        else:
            seg_end = anchors.get(next_letter, len(full_text))

        parts.append(full_text[seg_begin:seg_end].strip())

    # Clean empty parts by merging if any are blank
    cleaned = []
    for p in parts:
        if p:
            cleaned.append(p)
    while len(cleaned) < 4:
        cleaned.append("")
    return cleaned[:4]


def tts_to_wav(text: str, out_wav: Path, voice_id: str, model_id: str,
               stability: float = 0.5, similarity: float = 0.5,
               style: float | None = 0.2, use_speaker_boost: bool = True,
               sleep_s: float = 0.6) -> bool:
    api_key = os.environ.get("ELEVENLABS_API_KEY")
    if not api_key:
        print("ERROR: ELEVENLABS_API_KEY not set in environment", file=sys.stderr)
        return False

    url = f"{ELEVEN_BASE_URL}/text-to-speech/{voice_id}"
    headers = {
        "Accept": "audio/wav",
        "Content-Type": "application/json",
        "xi-api-key": api_key,
    }
    body = {
        "text": text,
        "model_id": model_id,
        "voice_settings": {
            "stability": stability,
            "similarity_boost": similarity,
        }
    }
    # Optional extras
    if style is not None:
        body["voice_settings"]["style"] = style
    body["voice_settings"]["use_speaker_boost"] = use_speaker_boost

    try:
        r = requests.post(url, headers=headers, data=json.dumps(body))
        if r.status_code != 200:
            print(f"TTS failed ({r.status_code}): {r.text[:200]}", file=sys.stderr)
            return False
        out_wav.parent.mkdir(parents=True, exist_ok=True)
        out_wav.write_bytes(r.content)
        print(f"✓ Wrote {out_wav}")
        time.sleep(sleep_s)
        return True
    except Exception as e:
        print(f"TTS error: {e}", file=sys.stderr)
        return False


def concat_wavs(wav_paths: list[Path], out_path: Path) -> bool:
    if not wav_paths:
        print("No WAVs to concatenate", file=sys.stderr)
        return False

    # Read params from the first file
    with wave.open(str(wav_paths[0]), 'rb') as w0:
        params = w0.getparams()
        frames = [w0.readframes(w0.getnframes())]

    # Verify and collect remaining
    for p in wav_paths[1:]:
        with wave.open(str(p), 'rb') as w:
            if w.getparams() != params:
                print("WAV parameter mismatch; cannot concatenate safely", file=sys.stderr)
                return False
            frames.append(w.readframes(w.getnframes()))

    out_path.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(out_path), 'wb') as out:
        out.setparams(params)
        for fr in frames:
            out.writeframes(fr)
    print(f"✓ Combined into {out_path}")
    return True


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input-text-file", required=True, help="Path to the full mapping text file (e.g., SHIFT/004.txt)")
    ap.add_argument("--out-dir", default="test_output/shift_split", help="Directory to place intermediate WAV files")
    ap.add_argument("--voice-id", default="RILOU7YmBhvwJGDGjNmP")
    ap.add_argument("--model-id", default="eleven_monolingual_v1")
    ap.add_argument("--combined-out", required=True, help="Path to write the combined WAV output")
    args = ap.parse_args()

    text = read_text(args.input_text_file)

    # Light pacing tweak: insert small pauses after periods
    # This helps slow delivery a bit without SSML.
    paced = re.sub(r"\.\s+", ".  ", text)

    parts = split_into_four_parts(paced)
    print("Split lengths:", [len(p) for p in parts])

    out_dir = Path(args.out_dir)
    tmp_wavs = []
    for i, part in enumerate(parts, start=1):
        part_file = out_dir / f"part_{i:02d}.txt"
        part_file.parent.mkdir(parents=True, exist_ok=True)
        part_file.write_text(part, encoding="utf-8")
        wav_path = out_dir / f"part_{i:02d}.wav"
        ok = tts_to_wav(
            text=part,
            out_wav=wav_path,
            voice_id=args.voice_id,
            model_id=args.model_id,
            stability=0.5,
            similarity=0.5,
            style=0.2,
            use_speaker_boost=True,
            sleep_s=0.7,
        )
        if not ok:
            print(f"Aborting due to TTS failure on part {i}", file=sys.stderr)
            return 2
        tmp_wavs.append(wav_path)

    combined_out = Path(args.combined_out)
    ok = concat_wavs(tmp_wavs, combined_out)
    return 0 if ok else 3


if __name__ == "__main__":
    sys.exit(main())
