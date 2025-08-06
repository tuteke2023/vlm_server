#!/usr/bin/env python3
"""Start VLM server in CPU mode to bypass CUDA issues"""

import os
import sys

# Force CPU mode
os.environ['CUDA_VISIBLE_DEVICES'] = ''
os.environ['VLM_DEVICE'] = 'cpu'
os.environ['VLM_MODEL'] = 'Qwen/Qwen2.5-VL-3B-Instruct'

# Import and modify vlm_server config
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import vlm_server

# Override device configuration
vlm_server.Config.DEVICE = "cpu"
vlm_server.Config.MODEL_NAME = "Qwen/Qwen2.5-VL-3B-Instruct"
vlm_server.Config.DEFAULT_MODEL = "Qwen/Qwen2.5-VL-3B-Instruct"

if __name__ == "__main__":
    import uvicorn
    print("Starting VLM Server in CPU mode...")
    print("Note: This will be slower than GPU mode but will work around CUDA compatibility issues")
    
    uvicorn.run(
        vlm_server.app,
        host=vlm_server.Config.HOST,
        port=vlm_server.Config.PORT,
        reload=False,
        log_level="info"
    )