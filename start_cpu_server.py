#!/usr/bin/env python3
"""
Start VLM server in CPU mode for testing quantization features
(Will be very slow but functional for testing)
"""

import os
import sys
import subprocess
import time

def start_cpu_server():
    """Start the server in CPU-only mode"""
    
    print("🖥️  Starting VLM Server in CPU Mode")
    print("=" * 50)
    print("⚠️  WARNING: CPU mode will be very slow!")
    print("   This is only for testing the quantization interface.")
    print("   For production use, fix CUDA compatibility first.")
    print()
    
    # Set environment to disable CUDA
    env = os.environ.copy()
    env['CUDA_VISIBLE_DEVICES'] = ''
    
    # Start server
    print("🚀 Starting server...")
    print("   This may take 2-3 minutes to load the model...")
    
    try:
        # Start server in background
        process = subprocess.Popen([
            sys.executable, 'vlm_server.py'
        ], env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        # Wait and check if it starts successfully
        time.sleep(60)  # Give it time to load
        
        if process.poll() is None:  # Still running
            print("✅ Server appears to be starting...")
            print("🌐 Web interface should be available at: http://localhost:8080")
            print("🔧 API server should be available at: http://localhost:8000")
            print()
            print("💡 Test steps:")
            print("1. Open http://localhost:8080 in your browser")
            print("2. Try uploading a document")
            print("3. The quantization controls should work")
            print("4. Processing will be very slow (10-30 minutes)")
            print()
            print("📋 To stop server: kill", process.pid)
            return process.pid
        else:
            # Server failed
            stdout, stderr = process.communicate()
            print("❌ Server failed to start:")
            print("STDOUT:", stdout.decode()[-500:])
            print("STDERR:", stderr.decode()[-500:])
            return None
            
    except Exception as e:
        print(f"❌ Failed to start server: {e}")
        return None

if __name__ == "__main__":
    start_cpu_server()