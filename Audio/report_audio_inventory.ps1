param(
    [Parameter(Mandatory=$true)] [string]$RecordedWordsPath,
    [Parameter(Mandatory=$true)] [string]$GeneratedWordsPath,
    [string]$OutReport = "audio_inventory_report.json"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

function Write-Info($m){ Write-Host "[INFO] $m" -ForegroundColor Cyan }
function Write-Warn($m){ Write-Host "[WARN] $m" -ForegroundColor Yellow }

$RecordedWordsPath = (Get-Item -LiteralPath $RecordedWordsPath).FullName
$GeneratedWordsPath = (Get-Item -LiteralPath $GeneratedWordsPath).FullName

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
$labels = $wordsMap.PSObject.Properties.Name | Sort-Object

$exts = @('*.mp3','*.wav','*.m4a','*.ogg')

function Build-Index($root){
  $idx = @{}
  foreach($e in $exts){
    Get-ChildItem -LiteralPath $root -Recurse -File -Filter $e -ErrorAction SilentlyContinue | ForEach-Object {
      $bn = $_.BaseName.ToLowerInvariant()
      if (-not $idx.ContainsKey($bn)) { $idx[$bn] = @() }
      $idx[$bn] += $_.FullName
    }
  }
  return $idx
}

Write-Info "Scanning sources..."
$humanIdx = Build-Index $RecordedWordsPath
$genIdx   = Build-Index $GeneratedWordsPath

$report = @{
  recordedRoot = $RecordedWordsPath
  generatedRoot = $GeneratedWordsPath
  labels = @{}
}

foreach($label in $labels){
  $want = @($wordsMap.$label)
  $haveHuman = @()
  $missingHuman = @()
  $haveGen = @()
  $missingGen = @()

  foreach($w in $want){
    $k = $w.ToLowerInvariant()
    if ($humanIdx.ContainsKey($k)) { $haveHuman += $w } else { $missingHuman += $w }
    if ($genIdx.ContainsKey($k))   { $haveGen   += $w } else { $missingGen   += $w }
  }

  $report.labels[$label] = @{
    total = $want.Count
    human = @{ have = $haveHuman; missing = $missingHuman }
    generated = @{ have = $haveGen; missing = $missingGen }
  }
}

# Totals
$totalWanted = 0; $totalHuman = 0; $totalGen = 0
foreach($label in $labels){
  $totalWanted += $report.labels[$label].total
  $totalHuman  += $report.labels[$label].human.have.Count
  $totalGen    += $report.labels[$label].generated.have.Count
}
$report.summary = @{ wanted = $totalWanted; humanHave = $totalHuman; generatedHave = $totalGen }

# Output
$json = $report | ConvertTo-Json -Depth 6
Set-Content -LiteralPath $OutReport -Value $json -Encoding UTF8
Write-Info ("Report written: {0}" -f (Resolve-Path -LiteralPath $OutReport))

# Also emit a brief table to console
"Label,Total,HumanHave,HumanMissing,GenHave,GenMissing" | Write-Output
foreach($label in $labels){
  $L = $report.labels[$label]
  $line = "{0},{1},{2},{3},{4},{5}" -f $label, $L.total, $L.human.have.Count, $L.human.missing.Count, $L.generated.have.Count, $L.generated.missing.Count
  $line | Write-Output
}
