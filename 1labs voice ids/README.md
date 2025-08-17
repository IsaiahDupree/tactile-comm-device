# ElevenLabs Voice IDs — Quick Samples

This folder contains a quick generator to produce sample MP3s for two ElevenLabs voices used in this project.

Voices included:
- Rilou — `RILOU7YmBhvwJGDGjNmP`
- Rachel — `21m00Tcm4TlvDq8ikWAM`

## How to run (Windows PowerShell)

1. Set your API key in the current shell (do NOT commit keys):
```powershell
$env:ELEVENLABS_API_KEY = "<your_api_key>"
```

2. Optionally set custom sample text:
```powershell
$env:TTS_SAMPLE_TEXT = "This is a test of the tactile communicator."
```

3. Run the generator:
```powershell
python .\generate_samples.py
```

Outputs:
- `rilou_test.mp3`
- `rachel_test.mp3`

Both files are saved in this folder.

## Notes
- The script uses the ElevenLabs v1 Text-to-Speech endpoint and a conservative voice settings preset for clear speech suitable for device prompts.
- If you see an authentication error, ensure `ELEVENLABS_API_KEY` is set in your environment for the session.
- To change the model or settings, edit `PAYLOAD_TEMPLATE` inside `generate_samples.py`.
