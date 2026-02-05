# Quick run script using uv

# Set console to UTF-8 encoding for proper Chinese display
chcp 65001 > $null

Write-Host "Starting Hanime1 Downloader..." -ForegroundColor Cyan

# Ensure we are in the script directory
Set-Location $PSScriptRoot

if (Test-Path "hentai") {
    Set-Location "hentai"
    uv run python main.py
} else {
    Write-Host "Error: 'hentai' directory not found!" -ForegroundColor Red
    Read-Host "Press Enter to exit..."
}
