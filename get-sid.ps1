<#
.SYNOPSIS
    SID OS Bootstrap for Windows — zero dependencies, uses only built-in PowerShell
.DESCRIPTION
    Downloads and runs SID OS on Windows without needing wget, curl, git, or Python pre-installed.
    If Python is not found, opens the download page.
#>
param(
    [switch]$Setup,
    [switch]$Update,
    [switch]$Help
)

$SID_VERSION = "1.0.0"
$GITHUB_REPO = "Ryuupyroxi/SID-OS"
$RELEASE_URL = "https://github.com/$GITHUB_REPO/releases/download/v$SID_VERSION/sid-$SID_VERSION-portable.tar.gz"
$BOOTSTRAP_URL = "https://raw.githubusercontent.com/$GITHUB_REPO/main/get-sid.py"

function Show-Banner {
    Write-Host ""
    Write-Host "=========================================================" -ForegroundColor Cyan
    Write-Host "   ███████╗██╗██████╗      ██████╗ ███████╗" -ForegroundColor Cyan
    Write-Host "   ██╔════╝██║██╔══██╗    ██╔═══██╗██╔════╝" -ForegroundColor Cyan
    Write-Host "   ███████╗██║██║  ██║    ██║   ██║███████╗" -ForegroundColor Cyan
    Write-Host "   ╚════██║██║██║  ██║    ██║   ██║╚════██║" -ForegroundColor Cyan
    Write-Host "   ███████║██║██████╔╝    ╚██████╔╝███████║" -ForegroundColor Cyan
    Write-Host "   ╚══════╝╚═╝╚═════╝      ╚═════╝ ╚══════╝" -ForegroundColor Cyan
    Write-Host "   SUPER INTELLIGENT DISTRO    v$SID_VERSION" -ForegroundColor Green
    Write-Host "=========================================================" -ForegroundColor Cyan
    Write-Host ""
}

function Find-SID {
    $candidates = @(
        Join-Path $PWD "SID-OS",
        Join-Path $PWD "sid",
        Join-Path $env:USERPROFILE "SID-OS",
        Join-Path $env:USERPROFILE "sid"
    )
    foreach ($dir in $candidates) {
        if (Test-Path (Join-Path $dir "src\main.py")) {
            return $dir
        }
        if (Test-Path (Join-Path $dir "sid.bat")) {
            return $dir
        }
    }
    return $null
}

function Download-SID {
    param([string]$TargetDir)
    
    Write-Host "  Downloading SID OS v$SID_VERSION..." -ForegroundColor Yellow
    
    $tarballPath = Join-Path $env:TEMP "sid-$SID_VERSION-portable.tar.gz"
    
    try {
        Write-Host "     $RELEASE_URL"
        $wc = New-Object System.Net.WebClient
        $wc.Headers["User-Agent"] = "SID-OS-Bootstrap/1.0"
        $wc.DownloadFile($RELEASE_URL, $tarballPath)
        Write-Host "  Downloaded successfully" -ForegroundColor Green
    } catch {
        Write-Host "  Download failed: $_" -ForegroundColor Red
        Write-Host "  Download manually from: https://github.com/$GITHUB_REPO/releases" -ForegroundColor Yellow
        exit 1
    }
    
    # Extract (PowerShell 5+ has Expand-Archive for .zip, but for .tar.gz we need workaround)
    Write-Host "  Extracting..." -ForegroundColor Yellow
    New-Item -ItemType Directory -Force -Path $TargetDir | Out-Null
    
    if (Get-Command "tar" -ErrorAction SilentlyContinue) {
        # Windows 10 1803+ has built-in tar
        tar -xzf $tarballPath -C $TargetDir
    } else {
        # Fallback: use .NET for extraction
        # First decompress gzip
        $inFile = [System.IO.File]::OpenRead($tarballPath)
        $outFile = [System.IO.File]::OpenWrite((Join-Path $env:TEMP "sid.tar"))
        $gzip = New-Object System.IO.Compression.GzipStream($inFile, [System.IO.Compression.CompressionMode]::Decompress)
        $gzip.CopyTo($outFile)
        $gzip.Close()
        $inFile.Close()
        $outFile.Close()
        
        # Then extract tar (no built-in, so we use a simple approach)
        Write-Host "  Extracting tar (this may take a moment)..." -ForegroundColor Yellow
        # For .tar files without 7zip, we need another approach
        # Best option: download the .zip from releases instead
        $zipUrl = "https://github.com/$GITHUB_REPO/releases/download/v$SID_VERSION/sid-$SID_VERSION-portable.zip"
        $zipPath = Join-Path $env:TEMP "sid-$SID_VERSION-portable.zip"
        try {
            $wc.DownloadFile($zipUrl, $zipPath)
            Expand-Archive -Path $zipPath -DestinationPath $TargetDir -Force
        } catch {
            Write-Host "  Could not extract. Download manually." -ForegroundColor Red
            exit 1
        }
    }
    
    # Mark as downloaded
    Set-Content -Path (Join-Path $TargetDir ".sid_configured") -Value "version=$SID_VERSION"
    Write-Host "  Extracted to: $TargetDir" -ForegroundColor Green
}

function Check-Python {
    # Check if Python is available
    $pythonCmds = @("python3", "python")
    foreach ($cmd in $pythonCmds) {
        try {
            $version = & $cmd --version 2>&1
            if ($version -match "Python 3\.(\d+)") {
                return $cmd
            }
        } catch {
            continue
        }
    }
    return $null
}

function Install-Deps {
    param([string]$SidDir)
    
    $python = Check-Python
    if (-not $python) {
        Write-Host "  Python 3 is not installed!" -ForegroundColor Red
        Write-Host "  Download from: https://www.python.org/downloads/" -ForegroundColor Yellow
        Write-Host "  MAKE SURE TO CHECK 'Add Python to PATH' during installation" -ForegroundColor Yellow
        Start-Process "https://www.python.org/downloads/"
        return $false
    }
    
    Write-Host "  Python found: $python" -ForegroundColor Green
    Write-Host "  Installing dependencies..." -ForegroundColor Yellow
    
    $sidDir = $TargetDir
    if (-not $sidDir) { $sidDir = $PWD }
    
    # Run the Python bootstrap's install deps
    Push-Location $sidDir
    try {
        & $python get-sid.py --install-deps
    } catch {
        Write-Host "  Could not auto-install deps. Please run: pip install numpy psutil pillow pyyaml requests" -ForegroundColor Yellow
    }
    Pop-Location
    
    return $true
}

function Launch-SID {
    param([string]$SidDir)
    
    $python = Check-Python
    if (-not $python) {
        Write-Host "  Cannot launch SID without Python 3." -ForegroundColor Red
        Write-Host "  Install Python from: https://www.python.org/downloads/" -ForegroundColor Yellow
        return
    }
    
    Write-Host ""
    Write-Host "  ==================================================" -ForegroundColor Cyan
    Write-Host "  Launching SID OS..." -ForegroundColor Green
    Write-Host "  ==================================================" -ForegroundColor Cyan
    Write-Host ""
    
    Push-Location $SidDir
    & $python src\main.py --theme vt100
    Pop-Location
}

# ---- MAIN ----
Show-Banner

if ($Help) {
    Write-Host @"
USAGE:
  .\get-sid.ps1              Download and launch SID
  .\get-sid.ps1 -Setup       Download + install deps + launch
  .\get-sid.ps1 -Update      Update to latest version
  .\get-sid.ps1 -Help        This help

REQUIREMENTS:
  - Windows 7 or later
  - PowerShell 3.0 or later (built into Windows)
  - Internet connection (first run only)
  - For AI features: Python 3.8+ (will prompt if missing)
"@
    return
}

# Find existing SID
$sidDir = Find-SID
if (-not $sidDir -or $Update) {
    $sidDir = Join-Path $PWD "SID-OS"
    Download-SID -TargetDir $sidDir
} else {
    Write-Host "  Found SID at: $sidDir" -ForegroundColor Green
}

# Setup mode: install deps
if ($Setup) {
    $python = Check-Python
    if (-not $python) {
        Write-Host "`n  Python 3 is required but not found on this system." -ForegroundColor Red
        Write-Host "  Since Windows doesn't ship with Python, you need to:" -ForegroundColor Yellow
        Write-Host "  1. Go to: https://www.python.org/downloads/" -ForegroundColor Cyan
        Write-Host "  2. Download Python 3.8+ (Windows installer)" -ForegroundColor Cyan
        Write-Host "  3. Run the installer and CHECK 'Add Python to PATH'" -ForegroundColor Cyan
        Write-Host "  4. Reopen Command Prompt and run this script again" -ForegroundColor Cyan
        Write-Host ""
        Write-Host "  Opening Python download page in your browser..." -ForegroundColor Yellow
        Start-Process "https://www.python.org/downloads/"
        return
    }
}

# Launch
Launch-SID -SidDir $sidDir
