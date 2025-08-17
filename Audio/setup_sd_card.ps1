param(
    [Parameter(Mandatory=$true)] [string]$SdRoot,
    [Parameter(Mandatory=$true)] [string]$RecordedWordsPath,
    [Parameter(Mandatory=$true)] [string]$GeneratedWordsPath,
    [ValidateSet('HUMAN_FIRST','GENERATED_FIRST')] [string]$Mode = 'HUMAN_FIRST',
    [string]$ElevenLabsVoiceId = 'RILOU7YmBhvwJGDGjNmP',
    [switch]$SynthesizeMissing,
    [switch]$NormalizeAudio
)

# Best-practice: Strict mode and error handling
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

function Write-Info($msg) { Write-Host "[INFO]  $msg" -ForegroundColor Cyan }
function Write-Warn($msg) { Write-Host "[WARN]  $msg" -ForegroundColor Yellow }
function Write-Err ($msg) { Write-Host "[ERROR] $msg" -ForegroundColor Red }

# Validate SD root
if (-not (Test-Path -LiteralPath $SdRoot)) { Write-Err "SD root '$SdRoot' not found"; exit 1 }
$sdRootItem = Get-Item -LiteralPath $SdRoot
if (-not $sdRootItem.PSIsContainer) { Write-Err "'$SdRoot' is not a directory"; exit 1 }

# Validate removable drive where possible
try {
    $driveLetter = ($SdRoot.TrimEnd('\')).Substring(0,1)
    $vol = Get-Volume -DriveLetter $driveLetter -ErrorAction Stop
    if ($vol.DriveType -ne 'Removable') {
        Write-Warn ("Drive {0}: is not reported as Removable (DriveType={1}). Proceeding cautiously." -f $driveLetter, $vol.DriveType)
    }
} catch {
    Write-Warn "Could not query volume for '$SdRoot': $($_.Exception.Message)"
}

# Normalize paths (no trailing backslash)
$SdRoot = $sdRootItem.FullName.TrimEnd('\')
$RecordedWordsPath = (Get-Item -LiteralPath $RecordedWordsPath).FullName.TrimEnd('\')
$GeneratedWordsPath = (Get-Item -LiteralPath $GeneratedWordsPath).FullName.TrimEnd('\')

Write-Info "SD Root: $SdRoot"
Write-Info "RecordedWords: $RecordedWordsPath"
Write-Info "GeneratedWords: $GeneratedWordsPath"
Write-Info "Mode: $Mode"
if ($SynthesizeMissing) { Write-Info "SynthesizeMissing: ON (ElevenLabs VoiceId=$ElevenLabsVoiceId)" }
if ($NormalizeAudio) { Write-Info "NormalizeAudio: ON (requires ffmpeg in PATH)" }

# Backup current SD contents
$timestamp = Get-Date -Format 'yyyyMMdd_HHmmss'
$backupRoot = Join-Path -Path ([Environment]::GetFolderPath('MyDocuments')) -ChildPath 'SD_BACKUPS'
$backupPath = Join-Path -Path $backupRoot -ChildPath ("SD_" + $timestamp)
New-Item -ItemType Directory -Force -Path $backupPath | Out-Null

Write-Info "Backing up SD card to: $backupPath"
# Use robocopy for efficient backup
$rc = Start-Process -FilePath robocopy -ArgumentList @("$SdRoot\", "$backupPath\", '/E', '/R:2', '/W:2', '/NFL', '/NDL', '/NJH', '/NJS', '/NP') -Wait -PassThru
if ($rc.ExitCode -ge 8) { Write-Err "Robocopy backup reported error (ExitCode=$($rc.ExitCode))"; exit 1 }

# Clear SD contents (do not format)
Write-Info "Clearing SD card contents (non-format)..."
Get-ChildItem -LiteralPath $SdRoot -Force | ForEach-Object {
    try {
        Remove-Item -LiteralPath $_.FullName -Recurse -Force -ErrorAction Stop
    } catch {
        Write-Err "Failed to remove '$($_.FullName)': $($_.Exception.Message)"; exit 1
    }
}

# Create strict folder structure
$dirs = @(
    'config',
    'mappings',
    'mappings\playlists',
    'audio',
    'audio\human',
    'audio\generated',
    'audio\generated\SYSTEM',
    'state'
)
foreach ($d in $dirs) { New-Item -ItemType Directory -Force -Path (Join-Path $SdRoot $d) | Out-Null }

# Label and folder mapping (special characters mapped to safe folder names)
$LabelToFolder = @{ '.' = 'PERIOD'; '_' = 'UNDERSCORE' }
function Get-FolderNameForLabel($label) {
    if ($LabelToFolder.ContainsKey($label)) { return $LabelToFolder[$label] } else { return $label }
}

# Locate ffmpeg if normalization requested
$ffmpeg = $null
if ($NormalizeAudio) {
    try {
        $ffmpeg = (Get-Command ffmpeg -ErrorAction Stop).Source
        Write-Info ("ffmpeg found at: {0}" -f $ffmpeg)
    } catch {
        Write-Warn "ffmpeg not found in PATH; audio normalization and WAV→MP3 conversion will be skipped"
        $NormalizeAudio = $false
    }
}

# Provide the hardware index -> label mapping
$buttons = @(
    @{ index = 2;  label = 'K' },
    @{ index = 3;  label = 'A' },
    @{ index = 5;  label = 'P' },
    @{ index = 6;  label = 'C' },
    @{ index = 7;  label = 'R' },
    @{ index = 8;  label = 'I' },
    @{ index = 9;  label = 'J' },
    @{ index = 10; label = 'Q' },
    @{ index = 11; label = 'W' },
    @{ index = 13; label = 'V' },
    @{ index = 14; label = 'X' },
    @{ index = 15; label = '.' },
    @{ index = 16; label = 'N' },
    @{ index = 17; label = 'G' },
    @{ index = 18; label = 'F' },
    @{ index = 21; label = 'U' },
    @{ index = 22; label = 'T' },
    @{ index = 23; label = 'M' },
    @{ index = 24; label = 'E' },
    @{ index = 27; label = '_' },
    @{ index = 28; label = 'Z' },
    @{ index = 29; label = 'S' },
    @{ index = 30; label = 'D' },
    @{ index = 31; label = 'Y' },
    @{ index = 32; label = 'B' },
    @{ index = 33; label = 'H' },
    @{ index = 35; label = 'O' }
)

# Build quick label set
$labels = $buttons | ForEach-Object { $_.label } | Sort-Object -Unique

# All words per label (provided)
$wordsJson = @'
{
  "A": ["Alari", "Amer", "Amory", "Apple", "Arabic", "Arabic Show"],
  "B": ["Bagel", "Ball", "Bathroom", "Bed", "Blanket", "Breathe", "Bye"],
  "C": ["Call", "Car", "Cat", "Chair", "Coffee", "Cold", "Cucumber"],
  "D": ["Daddy", "Deen", "Doctor", "Dog", "Door", "Down"],
  "E": ["Elephant"],
  "F": ["FaceTime", "Fish", "Funny"],
  "G": ["Garage", "Go", "Good Morning"],
  "H": ["Happy", "Heartburn", "Hello", "Hot", "House", "How are you", "Hungry"],
  "I": ["Ice", "Inside", "iPad"],
  "J": ["Jump"],
  "K": ["Kaiser", "Key", "Kiyah", "Kleenex", "Kyan"],
  "L": ["I love you", "Lee", "Light", "Light Down", "Light Up", "Love"],
  "M": ["Mad", "Medical", "Medicine", "Meditate", "Mohammad", "Moon"],
  "N": ["Nada", "Nadowie", "Net", "No", "Noah"],
  "O": ["Orange", "Outside"],
  "P": ["Pain", "Period", "Phone", "Purple"],
  "Q": ["Queen"],
  "R": ["Red", "Rest", "Room"],
  "S": ["Sad", "Scarf", "Shoes", "Sinemet", "Sleep", "Socks", "Space", "Stop", "Sun", "Susu"],
  "T": ["Togamet", "Tree", "TV", "Tylenol"],
  "U": ["Up", "Urgent Care"],
  "V": ["Van"],
  "W": ["Walk", "Walker", "Water", "Wheelchair"],
  "X": ["X-ray"],
  "Y": ["Yes", "Yellow"],
  "Z": ["Zebra"]
}
'@
$wordsMap = $wordsJson | ConvertFrom-Json

# Write buttons.csv
$buttonsCsvPath = Join-Path $SdRoot 'config\buttons.csv'
Write-Info "Writing $buttonsCsvPath"
"index,label" | Set-Content -LiteralPath $buttonsCsvPath -Encoding UTF8
$buttons | ForEach-Object { "{0},{1}" -f $_.index, $_.label } | Add-Content -LiteralPath $buttonsCsvPath -Encoding UTF8

# Write mode.cfg
$modeCfgPath = Join-Path $SdRoot 'config\mode.cfg'
Write-Info "Writing $modeCfgPath"
Set-Content -LiteralPath $modeCfgPath -Value $Mode -Encoding UTF8

# Helper: Find and copy audio files matching a given set of names
function Copy-MatchingAudio {
    param(
        [string]$SourceRoot,
        [string]$DestDir,
        [string[]]$Names,
        [switch]$Normalize
    )
    New-Item -ItemType Directory -Force -Path $DestDir | Out-Null

    $extensions = @('*.mp3','*.wav','*.m4a','*.ogg')
    $copiedFiles = @()

    foreach ($name in $Names) {
        # Build a case-insensitive search for file names that equal the base name (ignoring extension)
        $pattern = $name
        # Search under source recursively for files whose base name -replace matches exactly (case-insensitive)
        $fileMatches = @()
        foreach ($ext in $extensions) {
            $fileMatches += Get-ChildItem -LiteralPath $SourceRoot -Filter $ext -Recurse -ErrorAction SilentlyContinue |
                Where-Object { $_.BaseName -ieq $pattern }
        }
        if ($fileMatches.Count -eq 0) {
            Write-Warn "No source audio found for '$name' under '$SourceRoot'"
            continue
        }
        foreach ($m in $fileMatches) {
            $destPath = Join-Path $DestDir $m.Name
            try {
                Copy-Item -LiteralPath $m.FullName -Destination $destPath -Force
                if ($Normalize -and $NormalizeAudio) {
                    $destPath = Use-AudioNormalization -InputPath $destPath
                }
                $copiedFiles += $destPath
            } catch {
                Write-Warn "Failed to copy '$($m.FullName)' -> '$destPath': $($_.Exception.Message)"
            }
        }
    }
    return ,$copiedFiles
}

# Write M3U playlist given a list of files (full paths on SD) and a base path for relative entries
function Write-M3U {
    param(
        [string]$M3UPath,
        [string[]]$FilePathsOnSd,
        [string]$RelativeFrom
    )
    # Ensure directory
    New-Item -ItemType Directory -Force -Path (Split-Path -Parent $M3UPath) | Out-Null

    # Convert absolute to relative paths for M3U
    $relEntries = $FilePathsOnSd | ForEach-Object {
        $uriBase = New-Object System.Uri("$RelativeFrom\")
        $uriFile = New-Object System.Uri($_)
        $rel = $uriBase.MakeRelativeUri($uriFile).ToString()
        # Normalize to forward slashes as per M3U convention
        $rel -replace '\\','/'
    }
    # Write M3U (no header needed)
    Set-Content -LiteralPath $M3UPath -Value $relEntries -Encoding UTF8
}

# Normalize/convert a single audio file to mp3 44.1kHz mono 128k using ffmpeg; returns path to normalized file
function Use-AudioNormalization {
    param([Parameter(Mandatory=$true)] [string]$InputPath)
    if (-not $NormalizeAudio) { return $InputPath }
    $ext = [IO.Path]::GetExtension($InputPath)
    $base = [IO.Path]::GetFileNameWithoutExtension($InputPath)
    $dir  = [IO.Path]::GetDirectoryName($InputPath)
    $outPath = Join-Path $dir ($base + '.mp3')
    $ffArgs = @(
        '-y',
        '-i', $InputPath,
        '-ac', '1',
        '-ar', '44100',
        '-b:a', '128k',
        '-codec:a', 'libmp3lame',
        $outPath
    )
    try {
        $p = Start-Process -FilePath $ffmpeg -ArgumentList $ffArgs -NoNewWindow -Wait -PassThru
        if ($p.ExitCode -ne 0) { Write-Warn ("ffmpeg failed for {0} (ExitCode={1})" -f $InputPath, $p.ExitCode); return $InputPath }
        if ($ext -ne '.mp3') { Remove-Item -LiteralPath $InputPath -Force -ErrorAction SilentlyContinue }
        return $outPath
    } catch {
        Write-Warn ("ffmpeg error for {0}: {1}" -f $InputPath, $_.Exception.Message)
        return $InputPath
    }
}

# Synthesize missing generated audio via ElevenLabs
function New-ElevenLabsAudio {
    param(
        [Parameter(Mandatory=$true)] [string]$Text,
        [Parameter(Mandatory=$true)] [string]$VoiceId,
        [Parameter(Mandatory=$true)] [string]$OutFile
    )
    $apiKey = $env:ELEVENLABS_API_KEY
    if (-not $apiKey) { Write-Err 'ELEVENLABS_API_KEY environment variable not set'; return $false }
    $url = "https://api.elevenlabs.io/v1/text-to-speech/$VoiceId/stream"
    $headers = @{ 'xi-api-key' = $apiKey; 'Accept' = 'audio/mpeg' }
    $body = @{ text = $Text; model_id = 'eleven_multilingual_v2'; voice_settings = @{ stability = 0.5; similarity_boost = 0.75 } } | ConvertTo-Json -Depth 4
    try {
        Invoke-WebRequest -Uri $url -Headers $headers -Method Post -ContentType 'application/json' -Body $body -OutFile $OutFile -TimeoutSec 120 | Out-Null
        return $true
    } catch {
        Write-Warn ("TTS synthesis failed for '{0}': {1}" -f $Text, $_.Exception.Message)
        return $false
    }
}

# Process each label for human & generated audio
foreach ($label in $labels) {
    $folder = Get-FolderNameForLabel $label

    # Human
    $humanWords = @()
    if ($wordsMap.PSObject.Properties.Name -contains $label) {
        $humanWords = @($wordsMap.$label)
    } else {
        Write-Warn "No human word list provided for label '$label'"
    }
    $humanDest = Join-Path $SdRoot ("audio\\human\\" + $folder)
    $humanCopied = @()
    if ($humanWords.Count -gt 0) {
        $humanCopied = Copy-MatchingAudio -SourceRoot $RecordedWordsPath -DestDir $humanDest -Names $humanWords -Normalize:$NormalizeAudio
    } else {
        New-Item -ItemType Directory -Force -Path $humanDest | Out-Null
    }
    $humanM3U = Join-Path $SdRoot ("mappings\\playlists\\" + $label + "_human.m3u")
    Write-M3U -M3UPath $humanM3U -FilePathsOnSd $humanCopied -RelativeFrom (Join-Path $SdRoot 'mappings\\playlists')

    # Generated: attempt to match the same words from GeneratedWordsPath
    $genDest = Join-Path $SdRoot ("audio\\generated\\" + $folder)
    $genCopied = @()
    if ($humanWords.Count -gt 0) {
        $genCopied = Copy-MatchingAudio -SourceRoot $GeneratedWordsPath -DestDir $genDest -Names $humanWords -Normalize:$NormalizeAudio
        # If some are missing and synthesis is enabled, synthesize into destination
        if ($SynthesizeMissing) {
            $haveNames = ($genCopied | ForEach-Object { [IO.Path]::GetFileNameWithoutExtension($_) })
            $need = $humanWords | Where-Object { $haveNames -notcontains $_ }
            foreach ($word in $need) {
                $outMp3 = Join-Path $genDest ("{0}.mp3" -f $word)
                if (Test-Path -LiteralPath $outMp3) { continue }
                Write-Info ("Synthesizing '{0}' -> {1}" -f $word, $outMp3)
                $ok = New-ElevenLabsAudio -Text $word -VoiceId $ElevenLabsVoiceId -OutFile $outMp3
                if ($ok -and $NormalizeAudio) { $null = Use-AudioNormalization -InputPath $outMp3 }
                if ($ok) { $genCopied += $outMp3 }
            }
        }
    } else {
        New-Item -ItemType Directory -Force -Path $genDest | Out-Null
    }
    $genM3U = Join-Path $SdRoot ("mappings\\playlists\\" + $label + "_generated.m3u")
    Write-M3U -M3UPath $genM3U -FilePathsOnSd $genCopied -RelativeFrom (Join-Path $SdRoot 'mappings\\playlists')
}

# System folder placeholder (for announcements)
$systemDir = Join-Path $SdRoot 'audio\generated\SYSTEM'
if (-not (Test-Path -LiteralPath $systemDir)) { New-Item -ItemType Directory -Force -Path $systemDir | Out-Null }

# Ensure fallback clip exists: missing.mp3 (short 880Hz beep)
$missingClip = Join-Path $systemDir 'missing.mp3'
if (-not (Test-Path -LiteralPath $missingClip)) {
    $ffmpegPath = $null
    try { $ffmpegPath = (Get-Command ffmpeg -ErrorAction Stop).Source } catch { $ffmpegPath = $null }
    if ($ffmpegPath) {
        Write-Info ("Creating fallback clip: {0}" -f $missingClip)
        # 0.7s 880Hz sine, -3 dBFS, mono, 44.1kHz, 128k mp3
        $ffArgs = @('-y','-f','lavfi','-i','sine=frequency=880:duration=0.7','-filter:a','volume=0.7','-c:a','libmp3lame','-ar','44100','-ac','1','-b:a','128k', $missingClip)
        $proc = Start-Process -FilePath $ffmpegPath -ArgumentList $ffArgs -Wait -PassThru
        if ($proc.ExitCode -ne 0 -or -not (Test-Path -LiteralPath $missingClip)) {
            Write-Warn "Failed to create fallback missing.mp3 via ffmpeg"
        }
    } else {
        Write-Warn 'ffmpeg not found; cannot create /audio/generated/SYSTEM/missing.mp3 automatically'
    }
}

# Create initial state placeholders for future read/write
$stateFile = Join-Path $SdRoot 'state\cursors.json'
if (-not (Test-Path -LiteralPath $stateFile)) { '{}' | Set-Content -LiteralPath $stateFile -Encoding UTF8 }

# Simple manifest for desktop app compatibility
$manifest = @{ version = 1; generated = (Get-Date).ToString('o') }
$manifestPath = Join-Path $SdRoot 'manifest.json'
($manifest | ConvertTo-Json -Depth 4) | Set-Content -LiteralPath $manifestPath -Encoding UTF8

Write-Info "SD card provisioning complete."
