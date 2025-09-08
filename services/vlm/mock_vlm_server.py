#!/usr/bin/env python3
"""
Mock VLM server for testing Video-to-SOP without GPU
Simulates VLM responses for development/testing
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import uvicorn
import base64
import json
from datetime import datetime

app = FastAPI(title="Mock VLM Server", version="1.0.0")

class Message(BaseModel):
    role: str
    content: Any

class GenerateRequest(BaseModel):
    messages: List[Message]
    temperature: float = 0.7
    max_tokens: int = 2048

class GenerateResponse(BaseModel):
    choices: List[Dict[str, Any]]
    usage: Dict[str, int]

# Simulated frame analyses for different types of content
MOCK_ANALYSES = [
    "The screen shows a file explorer window with multiple folders visible. The user appears to be navigating to the Documents folder.",
    "A text editor is open with code visible. The cursor is positioned at line 15, and syntax highlighting suggests Python code.",
    "The application menu is expanded, showing various options including File, Edit, View, and Tools. The File menu appears to be selected.",
    "A dialog box is displayed asking for user confirmation. There are 'Yes' and 'No' buttons visible at the bottom.",
    "The terminal window is active with command output visible. The last command appears to have executed successfully.",
    "A web browser is open displaying documentation. The page shows installation instructions with code blocks.",
    "The settings panel is visible with multiple configuration options. The 'General' tab is currently selected.",
    "A progress bar indicates an operation is 45% complete. The estimated time remaining shows 2 minutes.",
    "The desktop is visible with several application icons. The taskbar shows multiple running applications.",
    "An error message is displayed in red text. The message suggests checking the configuration file."
]

@app.get("/")
async def root():
    return {"message": "Mock VLM Server running (CPU mode - for testing only)"}

@app.get("/model_info")
async def model_info():
    return {
        "model_size": "7B (Mock)",
        "status": "ready",
        "device": "cpu",
        "mode": "mock_testing"
    }

@app.post("/api/v1/generate_unified")
async def generate_unified(request: GenerateRequest):
    """Mock VLM generation endpoint"""
    
    # Extract the prompt from messages
    prompt = ""
    has_image = False
    
    for msg in request.messages:
        if isinstance(msg.content, list):
            for item in msg.content:
                if isinstance(item, dict):
                    if item.get("type") == "text":
                        prompt = item.get("text", "")
                    elif item.get("type") == "image_url":
                        has_image = True
        elif isinstance(msg.content, str):
            prompt = msg.content
    
    # Generate mock response based on prompt
    if "describe" in prompt.lower() or "analyze" in prompt.lower():
        # Use one of our mock analyses
        import random
        response_text = random.choice(MOCK_ANALYSES)
        
        # Add context based on prompt
        if "action" in prompt.lower():
            response_text += "\n\nAction detected: User is interacting with the interface element."
        if "next step" in prompt.lower():
            response_text += "\n\nNext step: Continue with the current operation or select an option."
        if "warning" in prompt.lower():
            response_text += "\n\nWarning: Ensure data is saved before proceeding."
            
    elif "transcribe" in prompt.lower():
        response_text = "This is a mock transcription. In production, actual audio would be transcribed here."
    else:
        response_text = f"Mock VLM response for: {prompt[:100]}..."
    
    return GenerateResponse(
        choices=[{
            "message": {
                "role": "assistant",
                "content": response_text
            },
            "index": 0,
            "finish_reason": "stop"
        }],
        usage={
            "prompt_tokens": len(prompt.split()),
            "completion_tokens": len(response_text.split()),
            "total_tokens": len(prompt.split()) + len(response_text.split())
        }
    )

@app.post("/switch_model")
async def switch_model(request: Dict[str, Any]):
    """Mock model switching"""
    model_size = request.get("model_size", "7B")
    return {
        "success": True,
        "message": f"Switched to {model_size} model (mock)",
        "model_size": model_size
    }

if __name__ == "__main__":
    print("\n" + "="*60)
    print("Mock VLM Server (For Testing Without GPU)")
    print("="*60)
    print("This server simulates VLM responses for development/testing")
    print("For production use, please use actual VLM with GPU")
    print("="*60 + "\n")
    
    uvicorn.run(app, host="0.0.0.0", port=8000)