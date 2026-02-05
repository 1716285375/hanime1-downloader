# UV environment setup script for Windows

# Set console to UTF-8 encoding for proper display
chcp 65001 > $null

Write-Host "====================================" -ForegroundColor Cyan
Write-Host " Hanime1 Downloader v1.0 - Setup    " -ForegroundColor Cyan
Write-Host "====================================" -ForegroundColor Cyan
Write-Host ""

# Ensure we are in the script directory
Set-Location $PSScriptRoot

# Check if uv is installed
Write-Host "[1/5] Checking uv..." -ForegroundColor Yellow
try {
    $uvVersion = uv --version 2>&1
    Write-Host "✓ uv is installed: $uvVersion" -ForegroundColor Green
} catch {
    Write-Host "✗ uv not found, installing..." -ForegroundColor Yellow
    
    # Install uv using PowerShell
    powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✓ uv installed successfully" -ForegroundColor Green
        # Refresh environment variables
        $env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")
    } else {
        Write-Host "✗ Failed to install uv. Please install manually: https://docs.astral.sh/uv/" -ForegroundColor Red
        exit 1
    }
}

# Switch to hentai directory where pyproject.toml is located
Write-Host "[2/5] Switching to project directory..." -ForegroundColor Yellow
if (Test-Path "hentai") {
    Set-Location "hentai"
    Write-Host "✓ Switched to hentai directory" -ForegroundColor Green
} else {
    Write-Host "✗ 'hentai' directory not found!" -ForegroundColor Red
    exit 1
}

# Create virtual environment with Python 3.13
Write-Host ""
Write-Host "[3/5] Syncing project dependencies (creates venv if needed)..." -ForegroundColor Yellow
# uv sync creates venv and installs dependencies
uv sync
if ($LASTEXITCODE -eq 0) {
    Write-Host "✓ Dependencies synced successfully" -ForegroundColor Green
} else {
    Write-Host "✗ Failed to sync dependencies" -ForegroundColor Red
    exit 1
}

# Install Playwright browsers
Write-Host ""
Write-Host "[4/5] Installing Playwright browsers..." -ForegroundColor Yellow
uv run playwright install chromium
if ($LASTEXITCODE -eq 0) {
    Write-Host "✓ Playwright browsers installed successfully" -ForegroundColor Green
} else {
    Write-Host "✗ Failed to install Playwright browsers" -ForegroundColor Red
    exit 1
}

# Create directories
Write-Host ""
Write-Host "[5/5] Creating necessary directories..." -ForegroundColor Yellow
$dirs = @("downloads", "logs", "database")
foreach ($dir in $dirs) {
    if (!(Test-Path $dir)) {
        New-Item -ItemType Directory -Path $dir | Out-Null
        Write-Host "✓ Created directory: $dir" -ForegroundColor Green
    } else {
        Write-Host "✓ Directory already exists: $dir" -ForegroundColor Green
    }
}

Write-Host ""
Write-Host "====================================" -ForegroundColor Cyan
Write-Host "      Setup completed!              " -ForegroundColor Green
Write-Host "====================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "To start the server, return to root and run:" -ForegroundColor Yellow
Write-Host "    .\run.ps1" -ForegroundColor White
Write-Host ""
Write-Host "Or from hentai directory:" -ForegroundColor Yellow
Write-Host "    uv run python main.py" -ForegroundColor White
Write-Host ""

# Return to original directory
Set-Location $PSScriptRoot
