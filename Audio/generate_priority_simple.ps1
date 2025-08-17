# Generate Priority Mode Audio Files using Windows TTS
Write-Host "Generating Priority Mode Audio (Windows TTS)"
Write-Host "=============================================="

# Create output directory
$outputDir = "priority_audio_windows"
if (!(Test-Path $outputDir)) {
    New-Item -ItemType Directory -Path $outputDir -Force | Out-Null
}

# Initialize Windows Speech API
Add-Type -AssemblyName System.Speech
$synthesizer = New-Object System.Speech.Synthesis.SpeechSynthesizer

# Configure voice settings
$synthesizer.Rate = 0      # Normal speed
$synthesizer.Volume = 100  # Maximum volume

Write-Host "Using default Windows TTS voice"

# Generate first file - Personal voice first
Write-Host ""
Write-Host "Generating: Personal voice first"
try {
    $outputPath1 = Join-Path $outputDir "004.wav"
    $synthesizer.SetOutputToWaveFile($outputPath1)
    $synthesizer.Speak("Personal voice first")
    Write-Host "Generated: $outputPath1"
    $success1 = $true
}
catch {
    Write-Host "Error generating 004.wav: $($_.Exception.Message)"
    $success1 = $false
}

# Generate second file - Computer voice first  
Write-Host ""
Write-Host "Generating: Computer voice first"
try {
    $outputPath2 = Join-Path $outputDir "005.wav"
    $synthesizer.SetOutputToWaveFile($outputPath2)
    $synthesizer.Speak("Computer voice first")
    Write-Host "Generated: $outputPath2"
    $success2 = $true
}
catch {
    Write-Host "Error generating 005.wav: $($_.Exception.Message)"
    $success2 = $false
}

$synthesizer.SetOutputToDefaultAudioDevice()
$synthesizer.Dispose()

Write-Host ""
Write-Host "Generation Complete!"
if ($success1 -and $success2) {
    Write-Host "Both files generated successfully"
    Write-Host "Files saved to: $outputDir"
    Write-Host ""
    Write-Host "Next steps:"
    Write-Host "1. Convert WAV to MP3 (if needed)"
    Write-Host "2. Copy to SD card E:\33\ as 004.mp3 and 005.mp3"
} else {
    Write-Host "Some files failed to generate"
}
