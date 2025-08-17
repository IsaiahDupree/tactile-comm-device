import os
import sys
import json
import pathlib
import requests

# Output directory
BASE_DIR = pathlib.Path(__file__).parent
OUT_DIR = BASE_DIR

# Voice IDs
VOICES = {
    "Rilou": "RILOU7YmBhvwJGDGjNmP",
    "Rachel": "21m00Tcm4TlvDq8ikWAM",
}

# Sample text
TEXT = os.environ.get("TTS_SAMPLE_TEXT", "This is a test of the tactile communicator.")

API_KEY = os.environ.get("ELEVENLABS_API_KEY")
if not API_KEY:
    print("ERROR: ELEVENLABS_API_KEY is not set in the environment.")
    print("In PowerShell: $env:ELEVENLABS_API_KEY=\"<your_api_key>\"")
    sys.exit(1)

BASE_URL = "https://api.elevenlabs.io/v1"
HEADERS = {
    "xi-api-key": API_KEY,
    "Content-Type": "application/json",
}

# Common settings tuned for clarity and natural pace
VOICE_SETTINGS = {
    "stability": 0.4,
    "similarity_boost": 0.7,
    "style": 0.0,
    "use_speaker_boost": True,
}

PAYLOAD_TEMPLATE = {
    "text": TEXT,
    "model_id": "eleven_monolingual_v1",
    "voice_settings": VOICE_SETTINGS,
}

def synth(voice_name: str, voice_id: str, text: str) -> pathlib.Path:
    url = f"{BASE_URL}/text-to-speech/{voice_id}"
    data = PAYLOAD_TEMPLATE.copy()
    data["text"] = text
    print(f"• Generating with {voice_name} ({voice_id}) …")
    resp = requests.post(url, headers=HEADERS, data=json.dumps(data))
    if resp.status_code != 200:
        print(f"  FAILED: HTTP {resp.status_code} — {resp.text[:200]}")
        sys.exit(2)
    out_path = OUT_DIR / f"{voice_name.lower()}_test.mp3"
    with open(out_path, "wb") as f:
        f.write(resp.content)
    print(f"  Saved: {out_path}")
    return out_path


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    for name, vid in VOICES.items():
        synth(name, vid, TEXT)
    print("Done.")


if __name__ == "__main__":
    main()
