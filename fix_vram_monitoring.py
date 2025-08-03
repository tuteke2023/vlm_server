#!/usr/bin/env python3
"""
Fix for VRAM monitoring to show actual GPU memory usage instead of just PyTorch allocated memory
"""

import subprocess
import re

def get_actual_vram_status():
    """Get actual VRAM usage from nvidia-smi"""
    try:
        # Run nvidia-smi command
        result = subprocess.run(
            ['nvidia-smi', '--query-gpu=memory.used,memory.total,memory.free', '--format=csv,noheader,nounits'],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            # Parse output
            output = result.stdout.strip()
            used, total, free = map(float, output.split(','))
            
            # Convert MB to GB
            used_gb = used / 1024
            total_gb = total / 1024
            free_gb = free / 1024
            usage_percentage = (used / total) * 100
            
            return {
                "allocated_gb": round(used_gb, 2),
                "reserved_gb": round(used_gb, 2),  # Same as allocated for nvidia-smi
                "free_gb": round(free_gb, 2),
                "total_gb": round(total_gb, 2),
                "usage_percentage": round(usage_percentage, 2),
                "source": "nvidia-smi"
            }
    except Exception as e:
        print(f"Error getting nvidia-smi data: {e}")
    
    return None

def compare_vram_methods():
    """Compare PyTorch vs nvidia-smi VRAM reporting"""
    import torch
    
    print("VRAM Monitoring Comparison")
    print("=" * 60)
    
    # PyTorch method (current implementation)
    if torch.cuda.is_available():
        allocated = torch.cuda.memory_allocated() / 1024**3
        reserved = torch.cuda.memory_reserved() / 1024**3
        total = torch.cuda.get_device_properties(0).total_memory / 1024**3
        free = total - allocated
        usage_percentage = (allocated / total) * 100
        
        print("\n1. PyTorch Memory Stats (current method):")
        print(f"   Allocated: {allocated:.2f} GB")
        print(f"   Reserved: {reserved:.2f} GB") 
        print(f"   Free: {free:.2f} GB")
        print(f"   Total: {total:.2f} GB")
        print(f"   Usage: {usage_percentage:.1f}%")
    
    # nvidia-smi method (actual GPU usage)
    actual_status = get_actual_vram_status()
    if actual_status:
        print("\n2. nvidia-smi Stats (actual GPU usage):")
        print(f"   Used: {actual_status['allocated_gb']} GB")
        print(f"   Free: {actual_status['free_gb']} GB")
        print(f"   Total: {actual_status['total_gb']} GB")
        print(f"   Usage: {actual_status['usage_percentage']}%")
        
        # Calculate difference
        if torch.cuda.is_available():
            diff = actual_status['allocated_gb'] - allocated
            print(f"\n3. Difference:")
            print(f"   Untracked memory: {diff:.2f} GB")
            print(f"   This includes: CUDA context, memory fragmentation, other processes")

def create_improved_vram_function():
    """Generate improved get_vram_status function"""
    
    print("\n\nImproved get_vram_status function:")
    print("-" * 60)
    print('''
def get_vram_status(self) -> VRAMStatus:
    """Get current VRAM usage statistics from nvidia-smi for accuracy"""
    if not torch.cuda.is_available():
        return VRAMStatus(
            allocated_gb=0,
            reserved_gb=0,
            free_gb=0,
            total_gb=0,
            usage_percentage=0
        )
    
    try:
        # Try nvidia-smi first for accurate total GPU usage
        result = subprocess.run(
            ['nvidia-smi', '--query-gpu=memory.used,memory.total,memory.free', '--format=csv,noheader,nounits'],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            output = result.stdout.strip()
            used_mb, total_mb, free_mb = map(float, output.split(','))
            
            # Convert MB to GB
            used_gb = used_mb / 1024
            total_gb = total_mb / 1024
            free_gb = free_mb / 1024
            
            # Also get PyTorch's reserved memory
            reserved = torch.cuda.memory_reserved() / 1024**3
            
            usage_percentage = (used_gb / total_gb) * 100
            
            return VRAMStatus(
                allocated_gb=round(used_gb, 2),
                reserved_gb=round(reserved, 2),
                free_gb=round(free_gb, 2),
                total_gb=round(total_gb, 2),
                usage_percentage=round(usage_percentage, 2)
            )
    except Exception:
        pass  # Fall back to PyTorch method
    
    # Fallback to PyTorch method if nvidia-smi fails
    allocated = torch.cuda.memory_allocated() / 1024**3
    reserved = torch.cuda.memory_reserved() / 1024**3
    total = torch.cuda.get_device_properties(0).total_memory / 1024**3
    free = total - allocated
    usage_percentage = (allocated / total) * 100
    
    return VRAMStatus(
        allocated_gb=round(allocated, 2),
        reserved_gb=round(reserved, 2),
        free_gb=round(free, 2),
        total_gb=round(total, 2),
        usage_percentage=round(usage_percentage, 2)
    )
''')

if __name__ == "__main__":
    compare_vram_methods()
    create_improved_vram_function()