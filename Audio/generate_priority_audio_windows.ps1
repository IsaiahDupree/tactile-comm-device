# Generate Priority Mode Audio Files using Windows TTS
# Creates improved, concise announcements for priority mode switching

Write-Host "🎵 GENERATING PRIORITY MODE AUDIO (Windows TTS)" -ForegroundColor Cyan
Write-Host "=" * 55 -ForegroundColor Cyan

# Create output directory
$outputDir = "priority_audio_windows"
if (!(Test-Path $outputDir)) {
    New-Item -ItemType Directory -Path $outputDir -Force | Out-Null
}

# Initialize Windows Speech API
Add-Type -AssemblyName System.Speech
$synthesizer = New-Object System.Speech.Synthesis.SpeechSynthesizer

# Configure voice settings for clarity
$synthesizer.Rate = 0      # Normal speed
$synthesizer.Volume = 100  # Maximum volume

# Try to select a clear female voice (like Microsoft Zira)
$voices = $synthesizer.GetInstalledVoices()
$preferredVoices = @("Microsoft Zira Desktop", "Microsoft Hazel Desktop", "Microsoft Eva Desktop")

foreach ($preferredVoice in $preferredVoices) {
    $voice = $voices | Where-Object { $_.VoiceInfo.Name -eq $preferredVoice }
    if ($voice) {
        $synthesizer.SelectVoice($preferredVoice)
        Write-Host "🎤 Using voice: $preferredVoice" -ForegroundColor Green
        break
    }
}

# Audio files to generate
$audioFiles = @(
    @{
        filename = "004.wav"
        text = "Personal voice first"
        description = "HUMAN_FIRST mode - Personal recordings prioritized"
    },
    @{
        filename = "005.wav" 
        text = "Computer voice first"
        description = "GENERATED_FIRST mode - TTS audio prioritized"
    }
)

$successCount = 0

foreach ($audio in $audioFiles) {
    Write-Host ""
    Write-Host "📢 $($audio.description)" -ForegroundColor Yellow
    Write-Host "🎤 Generating: '$($audio.text)'" -ForegroundColor White
    
    try {
        $outputPath = Join-Path $outputDir $audio.filename
        $synthesizer.SetOutputToWaveFile($outputPath)
        $synthesizer.Speak($audio.text)
        $synthesizer.SetOutputToDefaultAudioDevice()
        
        Write-Host "✅ Generated: $outputPath" -ForegroundColor Green
        $successCount++
    }
    catch {
        Write-Host "❌ Error generating $($audio.filename): $($_.Exception.Message)" -ForegroundColor Red
    }
}

$synthesizer.Dispose()

Write-Host ""
Write-Host "🎊 GENERATION COMPLETE!" -ForegroundColor Cyan
Write-Host "✅ Successfully generated $successCount/$($audioFiles.Count) files" -ForegroundColor Green

if ($successCount -gt 0) {
    Write-Host ""
    Write-Host "📁 Files saved to: $outputDir\" -ForegroundColor Yellow
    Write-Host "📋 Next steps:" -ForegroundColor Yellow
    Write-Host "   1. Convert WAV files to MP3 (if needed)" -ForegroundColor White
    Write-Host "   2. Copy files to SD card folder E:\33\" -ForegroundColor White
    Write-Host "   3. Rename to 004.mp3 and 005.mp3" -ForegroundColor White
    Write-Host "   4. Test priority mode switching" -ForegroundColor White
    
    Write-Host ""
    Write-Host "🎯 GENERATED ANNOUNCEMENTS:" -ForegroundColor Cyan
    foreach ($audio in $audioFiles) {
        Write-Host "   • $($audio.filename): '$($audio.text)'" -ForegroundColor White
    }
    
    Write-Host ""
    Write-Host "💡 These announcements are:" -ForegroundColor Cyan
    Write-Host "   ✅ More concise (3 words vs 4+ words)" -ForegroundColor Green
    Write-Host "   ✅ More natural and conversational" -ForegroundColor Green
    Write-Host "   ✅ Easier to understand quickly" -ForegroundColor Green
    Write-Host "   ✅ Less technical jargon" -ForegroundColor Green
}
