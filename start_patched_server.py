#!/usr/bin/env python3
"""Start VLM server with PyTorch GPU compatibility patch"""

import os
import sys
import warnings

# Suppress the CUDA warning
warnings.filterwarnings("ignore", message=".*CUDA capability.*")

# Patch PyTorch before importing anything else
import torch
import torch.cuda

# Override the capability check
def patched_check():
    """Bypass capability check"""
    pass

# Apply the patch
torch.cuda._check_capability = patched_check

# Also patch the lazy call
original_lazy_call = torch.cuda._lazy_call
def patched_lazy_call(func):
    if func.__name__ != "_check_capability":
        original_lazy_call(func)
torch.cuda._lazy_call = patched_lazy_call

print("🔧 PyTorch patched for RTX 5060 Ti compatibility")

# Now import and start the server
os.environ['VLM_MODEL'] = 'Qwen/Qwen2.5-VL-3B-Instruct'
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import vlm_server
import uvicorn

if __name__ == "__main__":
    vlm_server.Config.MODEL_NAME = "Qwen/Qwen2.5-VL-3B-Instruct"
    vlm_server.Config.DEFAULT_MODEL = "Qwen/Qwen2.5-VL-3B-Instruct"
    
    print("Starting VLM Server with GPU compatibility patch...")
    uvicorn.run(
        vlm_server.app,
        host=vlm_server.Config.HOST,
        port=vlm_server.Config.PORT,
        reload=False,
        log_level="info"
    )