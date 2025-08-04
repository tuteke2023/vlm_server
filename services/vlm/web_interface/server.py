#!/usr/bin/env python3
"""
Simple web server for the VLM Server Web Interface
Serves static files and provides a development environment
"""

import http.server
import socketserver
import os
import webbrowser
from pathlib import Path

class CustomHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(Path(__file__).parent), **kwargs)
    
    def end_headers(self):
        # Add CORS headers for development
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        super().end_headers()
    
    def do_OPTIONS(self):
        self.send_response(200)
        self.end_headers()

def main():
    PORT = 8080
    
    print("🌐 Starting VLM Server Web Interface...")
    print(f"📂 Serving files from: {Path(__file__).parent}")
    print(f"🔗 Open in browser: http://localhost:{PORT}")
    print("⚠️  Make sure your VLM server is running on http://localhost:8000")
    print("\nPress Ctrl+C to stop the server\n")
    
    with socketserver.TCPServer(("", PORT), CustomHTTPRequestHandler) as httpd:
        try:
            # Try to open browser automatically
            webbrowser.open(f'http://localhost:{PORT}')
        except:
            pass
        
        print(f"✅ Web interface running on http://localhost:{PORT}")
        httpd.serve_forever()

if __name__ == "__main__":
    main()