# Main entry point for the backend server
import uvicorn
import os

# PaddlePaddle PIR & OneDNN fixes - Must be set at the very start
os.environ["FLAGS_enable_pir_api"] = "0"
os.environ["FLAGS_enable_pir_in_executor"] = "0"
os.environ["FLAGS_enable_pir"] = "0"
os.environ["FLAGS_use_mkldnn"] = "0"
os.environ["PADDLE_PDX_DISABLE_MODEL_SOURCE_CHECK"] = "True"
os.environ["FLAGS_enable_new_executor"] = "0"

if __name__ == "__main__":
    # Ensure directories exist
    os.makedirs("backend/temp", exist_ok=True)
    os.makedirs("backend/output", exist_ok=True)
    
    uvicorn.run("backend.app.main:app", host="0.0.0.0", port=8000, reload=False)
