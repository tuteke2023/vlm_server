#!/usr/bin/env python3
"""Patch PyTorch to bypass GPU compatibility check"""

import torch
import torch.cuda

# Override the capability check
original_check = torch.cuda._check_capability

def patched_check():
    """Bypass capability check"""
    print("Bypassing CUDA capability check...")
    return

# Apply the patch
torch.cuda._check_capability = patched_check

# Also patch the warning function
original_warn = torch.cuda._lazy_call

def patched_lazy_call(func):
    """Filter out capability check from lazy calls"""
    if func.__name__ != "_check_capability":
        original_warn(func)

torch.cuda._lazy_call = patched_lazy_call

print("PyTorch patched to bypass GPU compatibility check")
print("Note: This may lead to unexpected behavior. Use at your own risk.")

# Test it
try:
    x = torch.tensor([1.0]).cuda()
    print("✅ Basic CUDA operation successful!")
except Exception as e:
    print(f"❌ CUDA operation still failed: {e}")