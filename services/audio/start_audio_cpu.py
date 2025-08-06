#!/usr/bin/env python3
"""Start audio service in CPU mode"""
import os
os.environ['CUDA_VISIBLE_DEVICES'] = ''  # Force CPU mode
import subprocess

subprocess.run(['python', 'transcription_server.py'])