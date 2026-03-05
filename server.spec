# -*- mode: python ; coding: utf-8 -*-
# PyInstaller spec — FastAPI + PaddleOCR 3.x backend
#
# Run with GLOBAL Python (has paddleocr 3.4 + paddlex):
#     pyinstaller server.spec --clean --noconfirm
#
import sys
from pathlib import Path

block_cipher = None

# ──────────────────────────────────────────────────────────────
# Hidden imports — only what paddleocr v3 + FastAPI actually need
# ──────────────────────────────────────────────────────────────
hidden_imports = [
    # Uvicorn internals (not auto-detected)
    "uvicorn.logging",
    "uvicorn.loops",
    "uvicorn.loops.auto",
    "uvicorn.loops.asyncio",
    "uvicorn.protocols",
    "uvicorn.protocols.http",
    "uvicorn.protocols.http.auto",
    "uvicorn.protocols.http.h11_impl",
    "uvicorn.lifespan",
    "uvicorn.lifespan.off",
    "uvicorn.lifespan.on",
    # FastAPI / Starlette
    "fastapi",
    "fastapi.staticfiles",
    "fastapi.responses",
    "fastapi.middleware",
    "fastapi.middleware.cors",
    "fastapi.concurrency",
    "starlette",
    "starlette.staticfiles",
    "starlette.responses",
    "starlette.middleware",
    "starlette.middleware.cors",
    "starlette.background",
    "pydantic",
    "pydantic.v1",
    # PaddleOCR 3.4.x + paddlex (new structure)
    "paddleocr",
    "paddleocr._pipelines",
    "paddleocr._models",
    "paddleocr._utils",
    "paddleocr._common",
    "paddlex",
    "paddlex.inference",
    "paddlex.repo_manager",
    "paddlex.utils",
    # PaddlePaddle 3.x
    "paddle",
    "paddle.base",
    "paddle.nn",
    "paddle.optimizer",
    # Image / doc
    "cv2",
    "PIL",
    "PIL.Image",
    "PIL.ImageOps",
    "docx",
    "docx.oxml",
    "docx.shared",
    # Async / network
    "multipart",
    "anyio",
    "anyio._backends._asyncio",
    "h11",
    "chardet",
    # python-magic-bin (Windows DLL-based)
    "magic",
]

# ──────────────────────────────────────────────────────────────
# Exclusions — heavy packages that sneak in via paddle/cv2 hooks
# but are NOT needed at runtime
# ──────────────────────────────────────────────────────────────
excludes = [
    "tkinter", "_tkinter",
    "matplotlib", "mpl_toolkits",
    "PyQt5", "PyQt6",
    "torch", "torchvision", "torchaudio",
    "tensorflow", "keras", "tensorboard",
    "sklearn", "scipy",
    "spacy", "thinc",
    "transformers",
    "numba", "llvmlite",
    "librosa",
    "nltk",
    "grpc", "grpcio",
    "IPython", "notebook", "jupyter",
    "pytest",
    "Cython",           # build-time only
    "cython",
]

# ──────────────────────────────────────────────────────────────
# Data files
# ──────────────────────────────────────────────────────────────
datas = []

# Locate paddleocr + paddlex from whatever Python is running PyInstaller
import paddleocr as _poc
import paddlex as _pxx
import paddle as _paddle
import importlib.metadata as _meta
paddleocr_path = Path(_poc.__file__).parent
paddlex_path   = Path(_pxx.__file__).parent
paddle_libs    = Path(_paddle.__file__).parent / "libs"
datas += [(str(paddleocr_path), "paddleocr")]
datas += [(str(paddlex_path),   "paddlex")]
# Bundle ALL paddle DLLs — PyInstaller only picks up a subset automatically
if paddle_libs.exists():
    datas += [(str(paddle_libs), "paddle/libs")]

# Include dist-info for packages that paddlex checks via importlib.metadata
# Without these, paddlex.utils.deps thinks the OCR extras are missing
_meta_pkgs = [
    "imagesize", "opencv-contrib-python", "pyclipper",
    "pypdfium2", "python-bidi", "shapely",
    "paddleocr", "paddlex", "paddlepaddle",
]
for _pkg in _meta_pkgs:
    try:
        _dist = _meta.Distribution.from_name(_pkg)
        _dist_path = Path(str(_dist._path))
        if _dist_path.exists():
            datas += [(str(_dist_path), _dist_path.name)]
    except _meta.PackageNotFoundError:
        pass

# backend source — makes "backend.app.main" importable at runtime
# ⚠️  Only source files — NOT venv, output, temp, debug
backend_src = Path("backend")
for sub in ["app", "__init__.py"]:
    src = backend_src / sub
    if src.exists():
        dest = f"backend/{sub}" if src.is_dir() else "backend"
        datas += [(str(src), dest)]

# ──────────────────────────────────────────────────────────────
# Analysis
# ──────────────────────────────────────────────────────────────
a = Analysis(
    ["server_entry.py"],
    pathex=["."],
    binaries=[],
    datas=datas,
    hiddenimports=hidden_imports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=excludes,
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
    console=True,   # Keep console; Electron hides the window
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
