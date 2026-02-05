#!/bin/bash

echo "Starting Hanime1 Downloader..."

if [ -d "hentai" ]; then
    cd hentai
    uv run python main.py
else
    echo "Error: 'hentai' directory not found!"
    read -p "Press Enter to exit..."
fi
