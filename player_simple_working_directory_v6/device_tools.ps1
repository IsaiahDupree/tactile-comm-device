# ===== SEGMENT 4: PowerShell helpers =====
# Save as: device_tools.ps1   (use: dot-source =>  . .\device_tools.ps1)
# Requires: data_cli.py + pyserial

# Defaults (override per call)
$Global:Port = "COM5"
$Global:Baud = 115200

function LS-Device([string]$Bank, [string]$Key, [string]$Port=$Global:Port, [int]$Baud=$Global:Baud) {
  python data_cli.py ls -p $Port -b $Baud $Bank $Key
}

function DEL-Device([string]$Bank,[string]$Key,[string]$File,[string]$Port=$Global:Port,[int]$Baud=$Global:Baud){
  python data_cli.py del -p $Port -b $Baud $Bank $Key $File
}

function EXIT-Device([string]$Port=$Global:Port,[int]$Baud=$Global:Baud){
  python data_cli.py exit -p $Port -b $Baud
}

# ===== SEGMENT 5: PowerShell put/get & folder ops =====

function PUT-File([string]$Bank,[string]$Key,[string]$DestName,[string]$LocalPath,
                  [string]$Port=$Global:Port,[int]$Baud=$Global:Baud,[switch]$NoCrc){
  if (!(Test-Path $LocalPath)) { throw "File not found: $LocalPath" }
  $args = @("put","-p",$Port,"-b",$Baud,$Bank,$Key,$DestName,$LocalPath)
  if ($NoCrc) { $args += "--no-crc" }
  python data_cli.py @args
}

function GET-File([string]$Bank,[string]$Key,[string]$File,[string]$OutPath,
                  [string]$Port=$Global:Port,[int]$Baud=$Global:Baud){
  New-Item -ItemType Directory -Force -Path (Split-Path $OutPath) | Out-Null
  python data_cli.py get -p $Port -b $Baud $Bank $Key $File $OutPath
}

# Upload all *.ext in a folder as 001.ext, 002.ext, ...
function PUT-FolderSeq([string]$Bank,[string]$Key,[string]$Folder,[string]$Ext="mp3",
                       [string]$Port=$Global:Port,[int]$Baud=$Global:Baud){
  if (!(Test-Path $Folder)) { throw "Folder not found: $Folder" }
  $i = 1
  Get-ChildItem -File -Path $Folder -Filter "*.$Ext" | Sort-Object Name | ForEach-Object {
    $num = "{0:D3}" -f $i
    Write-Host ">> PUT $($_.FullName) -> $num.$Ext"
    python data_cli.py put -p $Port -b $Baud $Bank $Key "$num.$Ext" $_.FullName
    $i++
  }
}

# Upload preserving local filenames
function PUT-FolderPreserve([string]$Bank,[string]$Key,[string]$Folder,[string]$Ext="mp3",
                            [string]$Port=$Global:Port,[int]$Baud=$Global:Baud){
  if (!(Test-Path $Folder)) { throw "Folder not found: $Folder" }
  Get-ChildItem -File -Path $Folder -Filter "*.$Ext" | Sort-Object Name | ForEach-Object {
    Write-Host ">> PUT $($_.FullName) -> $($_.Name)"
    python data_cli.py put -p $Port -b $Baud $Bank $Key $_.Name $_.FullName
  }
}

# ===== SEGMENT 6: PowerShell examples =====
# dot-source this file first:
#   . .\device_tools.ps1
# ensure /config/allow_writes.flag exists on the SD before PUT/DEL.

function Show-Examples {
  Write-Host @"

=== Data Mode PowerShell Examples ===

# List available serial ports:
python -c "from serial.tools import list_ports; [print(f'{p.device} - {p.description}') for p in list_ports.comports()]"

# List files in /audio/human/A
LS-Device human A -Port COM5

# Upload a single file as 001.mp3
PUT-File human A 001.mp3 "C:\path\to\local\001.mp3" -Port COM5

# Download a file
GET-File human A 001.mp3 ".\out\001.mp3" -Port COM5

# Delete a file
DEL-Device human A 001.mp3 -Port COM5

# Upload an entire folder as 001/002/003.mp3 ...
PUT-FolderSeq human A "C:\clips\A" mp3 -Port COM5

# Upload preserving original filenames
PUT-FolderPreserve human A "C:\clips\A" mp3 -Port COM5

# Exit DATA_MODE
EXIT-Device -Port COM5

=== Quick Setup ===
1. Dot-source this file: . .\device_tools.ps1
2. Set your port: `$Global:Port = "COM5"`
3. Ensure /config/allow_writes.flag exists on SD
4. Run commands above

"@
}

# Sync by size function - upload if missing or different size
function SYNC-FolderBySize([string]$Bank,[string]$Key,[string]$Folder,[string]$Ext="mp3",
                           [string]$Port=$Global:Port,[int]$Baud=$Global:Baud){
  if (!(Test-Path $Folder)) { throw "Folder not found: $Folder" }
  
  Write-Host "🔄 Syncing folder by size..."
  
  # Get device file list
  Write-Host "📋 Getting device file list..."
  $deviceFiles = @{}
  $output = python data_cli.py ls -p $Port -b $Baud $Bank $Key 2>$null
  $output | ForEach-Object {
    if ($_ -match "^(\S+)\s+(\d+)$") {
      $deviceFiles[$matches[1]] = [int]$matches[2]
    }
  }
  
  # Check local files
  Get-ChildItem -File -Path $Folder -Filter "*.$Ext" | Sort-Object Name | ForEach-Object {
    $localSize = $_.Length
    $deviceSize = $deviceFiles[$_.Name]
    
    if (-not $deviceSize -or $deviceSize -ne $localSize) {
      $status = if ($deviceSize) { "size mismatch ($deviceSize vs $localSize)" } else { "missing" }
      Write-Host ">> SYNC $($_.Name) - $status"
      python data_cli.py put -p $Port -b $Baud $Bank $Key $_.Name $_.FullName
    } else {
      Write-Host "✓ SKIP $($_.Name) - up to date"
    }
  }
}

# ==== SEGMENT 5: PowerShell sync-by-size ====

function SYNC-FolderBySizeSeq(
  [string]$Bank,[string]$Key,[string]$Folder,[string]$Ext="mp3",
  [int]$Start=1,[switch]$DryRun,[string]$Port=$Global:Port,[int]$Baud=$Global:Baud) {
  if (!(Test-Path $Folder)) { throw "Folder not found: $Folder" }
  $args = @("sync-seq","-p",$Port,"-b",$Baud,"--ext",$Ext,"--start",$Start,$Bank,$Key,$Folder)
  if ($DryRun) { $args += "--dry-run" }
  python data_cli.py @args
}

function SYNC-FolderBySizePreserve(
  [string]$Bank,[string]$Key,[string]$Folder,[string]$Ext="mp3",
  [switch]$DryRun,[string]$Port=$Global:Port,[int]$Baud=$Global:Baud) {
  if (!(Test-Path $Folder)) { throw "Folder not found: $Folder" }
  $args = @("sync-preserve","-p",$Port,"-b",$Baud,"--ext",$Ext,$Bank,$Key,$Folder)
  if ($DryRun) { $args += "--dry-run" }
  python data_cli.py @args
}

# Show examples on load
Show-Examples
