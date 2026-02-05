@echo off
chcp 65001 > nul
setlocal enabledelayedexpansion

echo ====================================
echo  Hanime1 Downloader v1.0 - Setup    
echo ====================================
echo.

:: Check if uv is installed
echo [1/5] Checking uv...
uv --version > nul 2>&1
if %errorlevel% neq 0 (
    echo x uv not found, installing...
    powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
    if %errorlevel% neq 0 (
        echo x Failed to install uv. Please install manually: https://docs.astral.sh/uv/
        pause
        exit /b 1
    )
    :: Refreshes env vars for current session is hard in batch without restart, 
    :: but the install script might handle user path. 
    :: We'll assume mostly it works or ask user to restart.
    echo v uv installed. Note: You might need to restart terminal if commands fail.
) else (
    echo v uv is installed.
)

:: Switch to hentai directory
echo [2/5] Switching to project directory...
if exist "hentai" (
    cd hentai
    echo v Switched to hentai directory
) else (
    echo x 'hentai' directory not found!
    pause
    exit /b 1
)

:: Sync dependencies
echo.
echo [3/5] Syncing project dependencies...
uv sync
if %errorlevel% neq 0 (
    echo x Failed to sync dependencies
    pause
    exit /b 1
)
echo v Dependencies synced successfully

:: Install Playwright
echo.
echo [4/5] Installing Playwright browsers...
uv run playwright install chromium
if %errorlevel% neq 0 (
    echo x Failed to install Playwright browsers
    pause
    exit /b 1
)
echo v Playwright browsers installed successfully

:: Create directories
echo.
echo [5/5] Creating necessary directories...
if not exist "downloads" mkdir downloads
if not exist "logs" mkdir logs
if not exist "database" mkdir database
echo v Directories created.

echo.
echo ====================================
echo       Setup completed!              
echo ====================================
echo.
echo To start the server, return to root and run:
echo     run.bat
echo.
pause
