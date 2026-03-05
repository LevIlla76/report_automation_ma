"""
server_entry.py — PyInstaller entry point for the bundled backend.

This file replaces run.py when building the packaged .exe.
It handles environment setup, writable paths, and uvicorn startup.
"""
import os
import sys
from pathlib import Path

# ── PaddlePaddle flags (must be first) ────────────────────────
os.environ["FLAGS_enable_pir_api"] = "0"
os.environ["FLAGS_enable_pir_in_executor"] = "0"
os.environ["FLAGS_enable_pir"] = "0"
os.environ["FLAGS_use_mkldnn"] = "0"
os.environ["PADDLE_PDX_DISABLE_MODEL_SOURCE_CHECK"] = "True"
os.environ["FLAGS_enable_new_executor"] = "0"

# ── When frozen by PyInstaller, add the _MEIPASS dir to sys.path ──
# so that "backend.app.main" is importable as a package.
if getattr(sys, 'frozen', False):
    bundle_dir = Path(sys._MEIPASS)
    if str(bundle_dir) not in sys.path:
        sys.path.insert(0, str(bundle_dir))

# ── Resolve writable directories ───────────────────────────────
# When packaged: Electron passes USERDATA_PATH env var
# When not packaged: fall back to cwd
userdata = Path(os.environ.get("USERDATA_PATH", Path.cwd()))
temp_dir   = userdata / "temp"
output_dir = userdata / "output"
temp_dir.mkdir(parents=True, exist_ok=True)
output_dir.mkdir(parents=True, exist_ok=True)

# Override the default relative paths used in endpoints.py
os.environ["BACKEND_TEMP_DIR"]   = str(temp_dir)
os.environ["BACKEND_OUTPUT_DIR"] = str(output_dir)

# ── PaddleOCR model cache ──────────────────────────────────────
# Store downloaded models in userdata so they persist across updates
model_dir = userdata / "paddle_models"
model_dir.mkdir(parents=True, exist_ok=True)
# PaddleOCR resolves ~/.paddleocr — override HOME so models don't re-download
os.environ["HOME"]            = str(userdata)
os.environ["USERPROFILE"]     = str(userdata)   # Windows equivalent of HOME
os.environ["PADDLEOCR_HOME"]  = str(model_dir)

# ── Start server ───────────────────────────────────────────────
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "backend.app.main:app",
        host="127.0.0.1",   # Bind only to loopback for security
        port=8000,
        reload=False,
        log_level="info",
    )
