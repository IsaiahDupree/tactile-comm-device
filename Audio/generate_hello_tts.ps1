$ErrorActionPreference = 'Stop'
$envPath = 'C:\Users\Isaia\Documents\3D Printing\Projects\Button\.env'
if (!(Test-Path $envPath)) { throw "Missing .env at $envPath" }
$content = Get-Content -Raw $envPath
$apiLine = ($content -split "`n") | Where-Object { $_ -match '^ELEVENLABS_API_KEY=' } | Select-Object -First 1
if (-not $apiLine) { throw 'ELEVENLABS_API_KEY not found in .env' }
$apiKey = $apiLine.Substring(19).Trim()

$voiceId = 'RILOU7YmBhvwJGDGjNmP' # Rilou (fallback available: 21m00Tcm4TlvDq8ikWAM)
$outDir = 'C:\Users\Isaia\Documents\3D Printing\Projects\Button\Audio\GeneratedStaging\hello_how_are_you'
New-Item -ItemType Directory -Force -Path $outDir | Out-Null

function Invoke-ElevenLabsTTS {
  param([string]$text, [string]$outFile)
  $uri = "https://api.elevenlabs.io/v1/text-to-speech/$voiceId"
  $headers = @{ 'xi-api-key' = $apiKey; 'Accept'='audio/mpeg' }
  $bodyObj = @{
    text = $text
    model_id = 'eleven_multilingual_v2'
    voice_settings = @{ stability = 0.5; similarity_boost = 0.75 }
  }
  $body = $bodyObj | ConvertTo-Json -Depth 5
  Invoke-RestMethod -Method Post -Uri $uri -Headers $headers -ContentType 'application/json' -Body $body -OutFile $outFile
}

Invoke-ElevenLabsTTS 'Shift button - press the shift twice for instructions' (Join-Path $outDir 'shift_press_2_instructions.mp3')
Invoke-ElevenLabsTTS 'Welcome to your Tactile Communication Device. The device has 4 special buttons: YES, NO, WATER, and Shift, plus 26 letter buttons A through Z. Each button supports multiple presses to cycle through different words. Press once for the first word, twice for second word, and so on to cycle through the words mapped to the letter. The device uses text-to-speech and personal recordings stored locally for offline operation. The device runs on rechargeable batteries through usb c and requires no internet connection. Press the shift button twice to repeat these instructions. Press the shift button three times to hear the word list mapping.' (Join-Path $outDir 'shift_press_3_full_instructions.mp3')
Invoke-ElevenLabsTTS 'Word list mapping - all letters and their corresponding words' (Join-Path $outDir 'shift_press_4_word_list_mapping.mp3')

Get-ChildItem $outDir -Filter *.mp3 | Select-Object Name, Length
