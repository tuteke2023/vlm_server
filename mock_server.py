#!/usr/bin/env python3
"""
Mock VLM server for testing quantization interface without model loading
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Optional, Union
import time
import uvicorn

app = FastAPI(title="Mock VLM Server", description="For testing quantization interface")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8080", "http://127.0.0.1:8080"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mock data
current_quantization = "none"
mock_vram_status = {
    "allocated_gb": 15.46,
    "reserved_gb": 15.55, 
    "free_gb": 0.47,
    "total_gb": 15.93,
    "usage_percentage": 97.06
}

class GenerateRequest(BaseModel):
    messages: List[Dict]
    max_new_tokens: Optional[int] = 512
    temperature: Optional[float] = 0.7
    top_p: Optional[float] = 0.9
    quantization: Optional[str] = None
    enable_safety_check: Optional[bool] = True

@app.get("/")
async def root():
    return {
        "service": "Mock VLM Server",
        "model": "Qwen/Qwen2.5-VL-7B-Instruct",
        "status": "running",
        "note": "Mock server for testing quantization interface",
        "endpoints": {
            "generate": "/api/v1/generate",
            "health": "/health",
            "vram_status": "/vram_status",
            "vram_prediction": "/vram_prediction",
            "quantization_options": "/quantization_options",
            "clear_vram": "/clear_vram",
            "reload_model": "/reload_model"
        }
    }

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "model_loaded": True,
        "device": "mock",
        "note": "Mock server - no real model loaded"
    }

@app.get("/vram_status")
async def get_vram_status():
    global current_quantization, mock_vram_status
    
    # Simulate quantization effects
    base_usage = 15.46
    if current_quantization == "8bit":
        mock_vram_status["allocated_gb"] = base_usage * 0.5
        mock_vram_status["usage_percentage"] = (mock_vram_status["allocated_gb"] / mock_vram_status["total_gb"]) * 100
    elif current_quantization == "4bit":
        mock_vram_status["allocated_gb"] = base_usage * 0.25
        mock_vram_status["usage_percentage"] = (mock_vram_status["allocated_gb"] / mock_vram_status["total_gb"]) * 100
    else:
        mock_vram_status["allocated_gb"] = base_usage
        mock_vram_status["usage_percentage"] = 97.06
    
    return mock_vram_status

@app.get("/vram_prediction")
async def predict_vram_usage(input_tokens: int = 512, output_tokens: int = 512):
    current_usage = mock_vram_status["allocated_gb"]
    additional_gb = (input_tokens + output_tokens) * 0.002 / 1024 + 0.5
    predicted_usage = current_usage + additional_gb
    predicted_percentage = (predicted_usage / mock_vram_status["total_gb"]) * 100
    
    return {
        "current_usage_gb": current_usage,
        "predicted_usage_gb": predicted_usage,
        "current_percentage": mock_vram_status["usage_percentage"],
        "predicted_percentage": predicted_percentage,
        "is_safe": predicted_percentage < 90,
        "margin_gb": mock_vram_status["total_gb"] * 0.9 - predicted_usage
    }

@app.get("/quantization_options")
async def get_quantization_options():
    base_usage = 15.46
    return [
        {
            "quantization_type": "none",
            "estimated_vram_reduction_gb": 0,
            "estimated_vram_usage_gb": base_usage
        },
        {
            "quantization_type": "8bit", 
            "estimated_vram_reduction_gb": base_usage * 0.5,
            "estimated_vram_usage_gb": base_usage * 0.5
        },
        {
            "quantization_type": "4bit",
            "estimated_vram_reduction_gb": base_usage * 0.75,
            "estimated_vram_usage_gb": base_usage * 0.25
        }
    ]

@app.post("/reload_model")
async def reload_model(request: dict = None):
    global current_quantization
    
    if request and "quantization" in request:
        new_quantization = request["quantization"] or "none"
        print(f"Mock: Changing quantization from {current_quantization} to {new_quantization}")
        current_quantization = new_quantization
        
        return {
            "status": "success",
            "quantization": current_quantization,
            "note": "Mock reload - no real model reloading",
            "vram_status": await get_vram_status()
        }
    
    return {"status": "success", "note": "Mock reload"}

@app.post("/api/v1/generate")
async def generate(request: GenerateRequest):
    # Mock processing delay
    time.sleep(2)
    
    # Check safety if enabled
    if request.enable_safety_check:
        prediction = await predict_vram_usage(512, request.max_new_tokens)
        if not prediction["is_safe"]:
            raise HTTPException(
                status_code=429, 
                detail=f"VRAM safety check failed. Predicted: {prediction['predicted_percentage']:.1f}%"
            )
    
    return {
        "response": f"Mock response for document analysis. (Processed with {request.quantization or 'no'} quantization)",
        "usage": {
            "input_tokens": 150,
            "output_tokens": 75,
            "total_tokens": 225
        },
        "processing_time": 2.0
    }

@app.post("/clear_vram")
async def clear_vram():
    return {"status": "success", "note": "Mock VRAM clear", "vram_status": await get_vram_status()}

if __name__ == "__main__":
    print("🎭 Starting Mock VLM Server")
    print("=" * 40)
    print("This server simulates the quantization features")
    print("✅ Web interface: http://localhost:8080")
    print("✅ API server: http://localhost:8000")
    print("⚡ All quantization controls will work")
    print("🎯 Use this to test the interface while fixing CUDA")
    print()
    
    uvicorn.run(app, host="0.0.0.0", port=8000)