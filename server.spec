# -*- mode: python ; coding: utf-8 -*-
# PyInstaller spec for bundling the FastAPI backend into a single .exe
#
# ⚠️  Run this INSIDE the venv:
#     backend\venv\Scripts\activate
#     pip install pyinstaller
#     pyinstaller server.spec --clean --noconfirm
#
import sys
from pathlib import Path

block_cipher = None

# ──────────────────────────────────────────────────────────────
# Hidden imports needed by paddleocr / paddlepaddle ecosystem
# ──────────────────────────────────────────────────────────────
hidden_imports = [
    # FastAPI / Uvicorn
    "uvicorn.logging",
    "uvicorn.loops",
    "uvicorn.loops.auto",
    "uvicorn.loops.asyncio",
    "uvicorn.protocols",
    "uvicorn.protocols.http",
    "uvicorn.protocols.http.auto",
    "uvicorn.protocols.http.h11_impl",
    "uvicorn.protocols.http.httptools_impl",
    "uvicorn.protocols.websockets",
    "uvicorn.protocols.websockets.auto",
    "uvicorn.lifespan",
    "uvicorn.lifespan.off",
    "uvicorn.lifespan.on",
    "fastapi",
    "starlette",
    "pydantic",
    # PaddleOCR / PaddlePaddle
    "paddle",
    "paddleocr",
    "paddleocr.paddleocr",
    "paddleocr.tools",
    # Image / doc
    "cv2",
    "PIL",
    "PIL.Image",
    "docx",
    "python_docx",
    # Utils
    "multipart",
    "anyio",
    "anyio._backends._asyncio",
    "h11",
    "httptools",
]

# ──────────────────────────────────────────────────────────────
# Data files (models are downloaded to ~/.paddleocr on first run)
# ──────────────────────────────────────────────────────────────
datas = []

# Include paddleocr package data
import paddleocr
paddleocr_path = Path(paddleocr.__file__).parent
datas += [(str(paddleocr_path), "paddleocr")]

# Include the backend package source so it's importable at runtime
backend_path = Path("backend")
datas += [(str(backend_path), "backend")]

a = Analysis(
    ["server_entry.py"],
    pathex=["."],
    binaries=[],
    datas=datas,
    hiddenimports=hidden_imports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=["tkinter", "matplotlib", "PyQt5", "PyQt6"],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="server",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,   # Keep console for logging; Electron hides it
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon="electron/assets/icon.ico",
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="server",
)
