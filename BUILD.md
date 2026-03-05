# BUILD & RELEASE GUIDE

## Architecture Overview

```
┌─────────────────────────────────────────────┐
│               Electron Shell                │
│  ┌──────────────┐   ┌─────────────────────┐ │
│  │  TitleBar    │   │  BrowserWindow      │ │
│  │  (custom)    │   │  → localhost:8000   │ │  ← Next.js static export (served by FastAPI)
│  └──────────────┘   └─────────────────────┘ │
│                                             │
│  electron-updater → GitHub Releases         │
└────────────────┬────────────────────────────┘
                 │ spawns
┌────────────────▼────────────────────────────┐
│           server.exe (PyInstaller)          │
│  FastAPI + PaddleOCR backend                │
│  Binds to 127.0.0.1:8000                   │
│  Serves: /api/* + static frontend files    │
└─────────────────────────────────────────────┘
```

## How Auto-Update Works

1. Dev pushes a git **tag** like `v1.2.0` to GitHub.
2. GitHub Actions triggers `.github/workflows/build-release.yml`.
3. The workflow:
   - Builds the Python backend with **PyInstaller** (`server.exe`)
   - Builds the Next.js frontend with `next build` (static export)
   - Packages both into an **Electron NSIS installer** with `electron-builder`
   - Publishes the installer + `latest.yml` to **GitHub Releases**
4. Running user instances check GitHub Releases every 4 hours.
5. When a new release is found, **electron-updater** downloads it silently.
6. The TitleBar shows a "v1.2.0 ready — Click to restart & install" button.
7. User clicks → `autoUpdater.quitAndInstall()` → app restarts with new version.

## Local Build (Dev)

### Prerequisites
- Python 3.11 in `backend/venv/`
- Node.js 20+
- PyInstaller: `pip install pyinstaller`

### Build Steps

```powershell
# Option A — All-in-one batch script
.\build_release.bat 1.0.0

# Option B — Manual steps
# 1. Build frontend
cd frontend && npm run build && cd ..

# 2. Build backend  
backend\venv\Scripts\activate
pyinstaller server.spec --clean --noconfirm
# Output: dist/server/

# 3. Copy backend to expected location
xcopy /E /I dist\server backend_dist\server

# 4. Build Electron
cd electron && npm install && npm run build:win
# Output: dist/*.exe
```

## Release Process (Dev → GitHub)

```powershell
git tag v1.0.1
git push origin v1.0.1
```
This automatically triggers the GitHub Actions build.

## Icon

Replace `electron/assets/icon.ico` with your 256×256 icon.
You can convert a PNG to ICO using: https://convertio.co/png-ico/

## User Installation

Users receive the NSIS installer (`OCR Report Automation Setup x.x.x.exe`).
- Installs to `%LOCALAPPDATA%\Programs\OCR Report Automation\`
- Creates a Desktop shortcut
- Creates a Start Menu shortcut
- Data/models stored in `%APPDATA%\report-automation\`
- Uninstaller included

## PaddleOCR Models

The first time the app runs on a user's machine, PaddleOCR downloads
its models (~50MB) to `%APPDATA%\report-automation\paddle_models\`.
This is a one-time operation. Subsequent launches are fast.

To pre-bundle models, download them during CI and include in the PyInstaller build.
