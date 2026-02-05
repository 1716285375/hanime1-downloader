@echo off
chcp 65001 > nul

echo Starting Hanime1 Downloader...

if exist "hentai" (
    cd hentai
    uv run python main.py
) else (
    echo Error: 'hentai' directory not found!
    pause
)
