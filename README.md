# Tactile Communication Device Project

This project contains tools and resources for the tactile communication device, including:

## Files Created

- `tasks.csv` - Master task list for the project milestones
- `generate_audio.py` - Python script for generating audio files using Eleven Labs API
- `.gitignore` - Git ignore file for the project

## Audio Generation

The `generate_audio.py` script uses the Eleven Labs API to generate TTS audio files for the tactile communication device.

### Usage

```bash
# List available voices
python generate_audio.py --list-voices

# Generate audio for specific letters
python generate_audio.py --letter A,B,C

# Generate audio for all letters
python generate_audio.py --all

# Generate with custom voice and count
python generate_audio.py --letter A --voice VOICE_ID --count 5
```

### API Key

Set your ElevenLabs API key as an environment variable:
```bash
export ELEVENLABS_API_KEY="your_api_key_here"
```

Or create a `.env` file in the project root:
```
ELEVENLABS_API_KEY=your_api_key_here
```

## Project Structure

```
tactile-comm-device/
├── sd/SD_FUTURE_PROOF/
│   ├── audio/
│   │   ├── human/
│   │   └── generated/
│   └── mappings/playlists/
└── docs/
```

## Git Testing

This repository is set up to test git capabilities for version control of the project files.
