<div align="center">

# Hanime1 Downloader

![Version](https://img.shields.io/badge/version-v1.0-blue?style=flat-square)
![Python](https://img.shields.io/badge/python-3.13+-blue.svg?style=flat-square)
![License](https://img.shields.io/badge/license-MIT-green.svg?style=flat-square)
![Platform](https://img.shields.io/badge/platform-win%20|%20linux%20|%20macos-lightgrey?style=flat-square)

[中文](README.md) | **English**

A modern asynchronous video downloader for [hanime1.me](https://hanime1.me) with a beautiful WebUI.

![App Screenshot](docs/app.png)

</div>

## ✨ Features

- **🚀 High Performance**: Built with Playwright + httpx + asyncio for maximum speed.
- **🎨 Modern WebUI**: Visual management panel with real-time monitoring, resume support, and concurrency control.
- **🛠️ Powerful**: Supports multiple resolutions (360p-1080p) and real-time WebSocket updates.

## 📦 Quick Start

This project uses [uv](https://docs.astral.sh/uv/) for dependency management. Requires Python 3.13.

### 1. One-Click Setup

Automatically installs uv, Playwright, and all dependencies.

- **Windows (CMD/PowerShell)**:
  ```cmd
  .\setup.bat
  ```
  _Or via PowerShell: `.\setup.ps1`_

- **Linux / macOS**:
  ```bash
  chmod +x setup.sh run.sh
  ./setup.sh
  ```

### 2. Start Server

- **Windows**: `.\run.bat`
- **Linux / macOS**: `./run.sh`

Access WebUI at: [http://127.0.0.1:8000](http://127.0.0.1:8000)

### 3. 🎨 Frontend Development (Optional)

If you want to modify the UI:

1. **Install Dependencies**:
   ```bash
   cd frontend
   npm install
   ```
2. **Start Dev Server**:
   ```bash
   npm run dev
   ```
3. **Build**:
   ```bash
   npm run build
   ```

## 🔧 Configuration (`hentai/config.py`)

- **ScraperConfig**: Headless mode (`headless=True`/`False`)
- **DownloadConfig**: Concurrency (`max_concurrent_downloads`), Proxy (`use_proxy`)
- **WebUIConfig**: Port (`port`, default 8000)

## 📁 Directory Structure

- `hentai/main.py`: Entry point
- `hentai/core/`: Core logic (Scraper, Downloader)
- `hentai/web/`: Frontend assets (Static)
- `frontend/`: Frontend source (React/Vite)

## 📝 License

[MIT License](LICENSE)
