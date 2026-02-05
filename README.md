<div align="center">

# Hanime1 Downloader

![Version](https://img.shields.io/badge/version-v1.0-blue?style=flat-square)
![Python](https://img.shields.io/badge/python-3.13+-blue.svg?style=flat-square)
![License](https://img.shields.io/badge/license-MIT-green.svg?style=flat-square)
![Platform](https://img.shields.io/badge/platform-win%20|%20linux%20|%20macos-lightgrey?style=flat-square)

**中文** | [English](README_EN.md)

现代化异步视频下载器，支持 [hanime1.me](https://hanime1.me)，带可视化 WebUI。

![App Screenshot](docs/app.png)

</div>

## ✨ 特性

- **🚀 高性能**: 基于 Playwright + httpx + asyncio 异步架构，极致速度。
- **🎨 WebUI**: 现代化可视管理面板，支持实时监控、断点续传、并发控制。
- **🛠️ 功能强大**: 支持多分辨率 (360p-1080p)、WebSocket 实时推送。

## 📦 快速开始

本项目使用 [uv](https://docs.astral.sh/uv/) 进行依赖管理。需要 Python 3.13+。

### 1. 一键安装

自动安装 uv、Playwright 及所有依赖。

- **Windows (CMD/PowerShell)**:
  ```cmd
  .\setup.bat
  ```
  _或者 PowerShell: `.\setup.ps1`_

- **Linux / macOS**:
  ```bash
  chmod +x setup.sh run.sh
  ./setup.sh
  ```

### 2. 启动服务

- **Windows**: `.\run.bat`
- **Linux / macOS**: `./run.sh`

启动后访问: [http://127.0.0.1:8000](http://127.0.0.1:8000)

### 3. 🎨 前端开发 (可选)

如果需要修改界面：

1. **安装依赖**:
   ```bash
   cd frontend
   npm install
   ```
2. **启动开发**:
   ```bash
   npm run dev
   ```
3. **构建**:
   ```bash
   npm run build
   ```

## 🔧 配置 (`hentai/config.py`)

- **ScraperConfig**: Headless 模式 (`headless=True`/`False`)
- **DownloadConfig**: 并发数 (`max_concurrent_downloads`)、代理 (`use_proxy`)
- **WebUIConfig**: 端口 (`port`，默认 8000)

## 📁 目录结构

- `hentai/main.py`: 入口文件
- `hentai/core/`: 核心逻辑 (爬虫、下载器)
- `hentai/web/`: 前端构建资源
- `frontend/`: 前端源代码 (React/Vite)

## 📝 许可证

[MIT License](LICENSE)