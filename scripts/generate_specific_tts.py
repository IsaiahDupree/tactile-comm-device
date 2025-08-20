#!/usr/bin/env python3
import argparse
from pathlib import Path
import sys
from pathlib import Path as _P

# Ensure repository root is importable when running from scripts/
_repo_root = _P(__file__).resolve().parent.parent
if str(_repo_root) not in sys.path:
    sys.path.insert(0, str(_repo_root))

from generate_audio import generate_audio, DEFAULT_VOICE_ID


def main():
    ap = argparse.ArgumentParser(description='Generate specific TTS MP3 for a given text')
    ap.add_argument('--text', required=True, help='Text to synthesize')
    ap.add_argument('--out', required=True, help='Target MP3 path')
    ap.add_argument('--voice', default=DEFAULT_VOICE_ID, help='Voice ID to use')
    ap.add_argument('--model', default='eleven_monolingual_v1', help='Model ID (e.g. eleven_monolingual_v1)')
    ap.add_argument('--stability', type=float, default=0.5, help='Voice stability (0.0-1.0)')
    ap.add_argument('--similarity', type=float, default=0.85, help='Voice similarity boost (0.0-1.0)')
    ap.add_argument('--style', type=float, default=None, help='Optional style (0.0-1.0)')
    ap.add_argument('--speaker-boost', type=int, choices=[0,1], default=1, help='Use speaker boost (1) or not (0)')
    args = ap.parse_args()

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    ok = generate_audio(
        args.text,
        args.voice,
        str(out_path),
        model_id=args.model,
        stability=args.stability,
        similarity_boost=args.similarity,
        style=args.style,
        use_speaker_boost=bool(args.speaker_boost),
    )
    print('[OK]' if ok else '[ERR]', str(out_path))
    return 0 if ok else 2


if __name__ == '__main__':
    raise SystemExit(main())
