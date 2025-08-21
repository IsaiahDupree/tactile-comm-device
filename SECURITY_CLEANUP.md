# Security Cleanup Guide

## ⚠️ Exposed API Keys Detected

GitHub has detected exposed ElevenLabs API keys in the following files:
- `README.md` (line 33)
- `test_elevenlabs_api.py` (line 11) 
- `test_api.py` (line 6)
- `generate_wordlist_audio.py` (line 14)

## ✅ Files Already Fixed

All files have been updated to use environment variables instead of hardcoded keys:

### Changes Made:
1. **README.md** - Added instructions for setting `ELEVENLABS_API_KEY` environment variable
2. **test_elevenlabs_api.py** - Now reads from `os.getenv('ELEVENLABS_API_KEY')`
3. **test_api.py** - Now reads from `os.getenv('ELEVENLABS_API_KEY')`
4. **generate_wordlist_audio.py** - Now checks for environment variable
5. **Added .env.example** - Template for secure configuration
6. **Updated .gitignore** - Added patterns to prevent future key exposure

## 🚨 Critical Next Steps

### 1. Clean Git History
The API keys are still in Git history. Run the cleanup script:

```powershell
# Install git-filter-repo if needed
pip install git-filter-repo

# Run the cleanup script
.\fix_git_secrets.ps1
```

### 2. Rotate API Keys
**IMMEDIATELY** rotate the exposed ElevenLabs API keys:
- `sk_c25a828d5ede8743dd5c78b4ffbddd23c5777f4877818c30`
- `sk_e349c46da16f713a586a3848e96bda3a0f40b1b3f709b7c1`
- `sk_c167a8fb150750ebb1cb825a8e4ddfbfd48fc8b9125d6f49`
- `sk_a1f0b666e5d55d5d504adea14168dfd01488f1feed22a710`

### 3. Set Up Environment Variables
Create a `.env` file (not tracked by Git):
```bash
ELEVENLABS_API_KEY=your_new_api_key_here
DEFAULT_VOICE_ID=RILOU7YmBhvwJGDGjNmP
```

### 4. Force Push Clean History
After running the cleanup script:
```bash
git push --force-with-lease origin main
```

### 5. Notify Collaborators
Anyone with a local clone will need to:
```bash
git fetch origin
git reset --hard origin/main
```

## 🔐 Prevention Measures

1. **Never commit API keys** - Always use environment variables
2. **Use .env files** - Keep them in .gitignore
3. **Pre-commit hooks** - Consider adding secret scanning
4. **Regular audits** - Check for accidentally committed secrets

## 📞 Support

If you need help with the cleanup process or have questions about the security fixes, the changes are ready to commit and the cleanup script is prepared.
