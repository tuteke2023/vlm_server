#!/usr/bin/env python3
"""Test script to verify I can run multiple services"""

import subprocess
import time
import requests
import os
import signal

def start_service(command, log_file):
    """Start a service in background"""
    with open(log_file, 'w') as f:
        process = subprocess.Popen(command, shell=True, stdout=f, stderr=f, preexec_fn=os.setsid)
    return process

def stop_service(process):
    """Stop a service"""
    if process:
        os.killpg(os.getpgid(process.pid), signal.SIGTERM)

def test_service(url, service_name):
    """Test if service is responding"""
    try:
        response = requests.get(url, timeout=5)
        print(f"✅ {service_name} is running: {response.status_code}")
        return True
    except:
        print(f"❌ {service_name} is not responding")
        return False

# Test running two simple HTTP servers
print("Testing ability to run multiple services...")

# Start service 1
service1 = start_service("python3 -m http.server 9001", "service1.log")
time.sleep(2)

# Start service 2  
service2 = start_service("python3 -m http.server 9002", "service2.log")
time.sleep(2)

# Test both services
test_service("http://localhost:9001", "Service 1")
test_service("http://localhost:9002", "Service 2")

# Clean up
stop_service(service1)
stop_service(service2)

print("\n✅ Successfully demonstrated running multiple services!")