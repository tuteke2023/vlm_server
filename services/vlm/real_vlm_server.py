#!/usr/bin/env python3
"""
Real VLM Server using Qwen2.5-VL-7B model
No shortcuts - actual visual understanding
"""

import torch
from transformers import AutoModelForVision2Seq, AutoProcessor
from qwen_vl_utils import process_vision_info
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import uvicorn
import base64
from PIL import Image
import io
import json
import gc

app = FastAPI(title="Real VLM Server - Qwen2.5-VL-7B", version="1.0.0")

# Global model variables
model = None
processor = None
device = None

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

def load_model():
    """Load the Qwen2.5-VL-7B model"""
    global model, processor, device
    
    print("🚀 Loading Qwen2.5-VL-7B model...")
    print("  This is the REAL model, not a mock!")
    
    # Use GPU
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"  Using device: {device}")
    if device.type == "cuda":
        print(f"  GPU: {torch.cuda.get_device_name(0)}")
        print(f"  VRAM available: {torch.cuda.get_device_properties(0).total_memory / 1024**3:.1f} GB")
    
    # Load the 7B model
    model_name = "Qwen/Qwen2.5-VL-7B-Instruct"
    print(f"  Loading model: {model_name}")
    
    try:
        # Load processor
        processor = AutoProcessor.from_pretrained(
            model_name,
            trust_remote_code=True
        )
        
        # Load model with automatic device mapping
        model = AutoModelForVision2Seq.from_pretrained(
            model_name,
            torch_dtype=torch.bfloat16,  # Use bfloat16 for better performance
            device_map="auto",  # Automatically use GPU
            trust_remote_code=True
        )
        
        print(f"  ✅ Model loaded successfully!")
        
        # Check VRAM usage
        if device.type == "cuda":
            allocated = torch.cuda.memory_allocated() / 1024**3
            print(f"  VRAM used: {allocated:.1f} GB")
            
    except Exception as e:
        print(f"  ❌ Error loading model: {e}")
        raise

@app.on_event("startup")
async def startup_event():
    """Load model on startup"""
    load_model()

@app.get("/")
async def root():
    return {
        "service": "Real VLM Server",
        "model": "Qwen2.5-VL-7B-Instruct",
        "status": "running",
        "device": str(device),
        "real_model": True,
        "no_shortcuts": True
    }

@app.get("/model_info")
async def model_info():
    if device.type == "cuda":
        vram_used = torch.cuda.memory_allocated() / 1024**3
        vram_total = torch.cuda.get_device_properties(0).total_memory / 1024**3
    else:
        vram_used = 0
        vram_total = 0
    
    return {
        "model_name": "Qwen2.5-VL-7B-Instruct",
        "model_size": "7B",
        "status": "ready" if model is not None else "not_loaded",
        "device": str(device),
        "vram_used_gb": f"{vram_used:.1f}",
        "vram_total_gb": f"{vram_total:.1f}",
        "real_model": True
    }

@app.post("/api/v1/generate_unified")
async def generate_unified(request: GenerateRequest):
    """Real VLM generation endpoint - actually analyzes images"""
    
    if model is None:
        raise HTTPException(status_code=503, detail="Model not loaded")
    
    try:
        # Parse the messages to extract text and images
        messages = []
        for msg in request.messages:
            role = msg.role
            
            if isinstance(msg.content, list):
                content_parts = []
                for item in msg.content:
                    if isinstance(item, dict):
                        if item.get("type") == "text":
                            content_parts.append({
                                "type": "text",
                                "text": item.get("text", "")
                            })
                        elif item.get("type") == "image_url":
                            image_url = item.get("image_url", {}).get("url", "")
                            # Handle base64 encoded images
                            if image_url.startswith("data:image"):
                                # Extract base64 data
                                base64_str = image_url.split(",")[1]
                                image_data = base64.b64decode(base64_str)
                                image = Image.open(io.BytesIO(image_data))
                                content_parts.append({
                                    "type": "image",
                                    "image": image
                                })
                
                messages.append({
                    "role": role,
                    "content": content_parts
                })
            else:
                messages.append({
                    "role": role,
                    "content": msg.content
                })
        
        # Process with the real VLM model
        text = processor.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=True
        )
        
        image_inputs, video_inputs = process_vision_info(messages)
        
        inputs = processor(
            text=[text],
            images=image_inputs,
            videos=video_inputs,
            padding=True,
            return_tensors="pt"
        ).to(device)
        
        # Generate response
        with torch.no_grad():
            generated_ids = model.generate(
                **inputs,
                max_new_tokens=request.max_tokens,
                temperature=request.temperature,
                do_sample=True if request.temperature > 0 else False
            )
        
        # Decode the response
        generated_ids_trimmed = [
            out_ids[len(in_ids):] for in_ids, out_ids in zip(inputs.input_ids, generated_ids)
        ]
        output_text = processor.batch_decode(
            generated_ids_trimmed,
            skip_special_tokens=True,
            clean_up_tokenization_spaces=False
        )[0]
        
        # Return in OpenAI-compatible format
        return GenerateResponse(
            choices=[{
                "message": {
                    "role": "assistant",
                    "content": output_text
                },
                "index": 0,
                "finish_reason": "stop"
            }],
            usage={
                "prompt_tokens": len(inputs.input_ids[0]),
                "completion_tokens": len(generated_ids_trimmed[0]),
                "total_tokens": len(inputs.input_ids[0]) + len(generated_ids_trimmed[0])
            }
        )
        
    except Exception as e:
        print(f"Error in generate_unified: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/analyze_frame")
async def analyze_frame(image_path: str, question: str):
    """Analyze a specific frame with a question"""
    
    if model is None:
        raise HTTPException(status_code=503, detail="Model not loaded")
    
    try:
        # Load the image
        image = Image.open(image_path)
        
        messages = [{
            "role": "user",
            "content": [
                {"type": "text", "text": question},
                {"type": "image", "image": image}
            ]
        }]
        
        # Process with model
        text = processor.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=True
        )
        
        image_inputs, video_inputs = process_vision_info(messages)
        
        inputs = processor(
            text=[text],
            images=image_inputs,
            videos=video_inputs,
            padding=True,
            return_tensors="pt"
        ).to(device)
        
        # Generate
        with torch.no_grad():
            generated_ids = model.generate(
                **inputs,
                max_new_tokens=512,
                temperature=0.1,  # Low temperature for factual analysis
                do_sample=False
            )
        
        # Decode
        generated_ids_trimmed = [
            out_ids[len(in_ids):] for in_ids, out_ids in zip(inputs.input_ids, generated_ids)
        ]
        output_text = processor.batch_decode(
            generated_ids_trimmed,
            skip_special_tokens=True,
            clean_up_tokenization_spaces=False
        )[0]
        
        return {"analysis": output_text, "image": image_path}
        
    except Exception as e:
        print(f"Error analyzing frame: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/vram_status")
async def vram_status():
    """Get current VRAM usage"""
    if device.type == "cuda":
        allocated = torch.cuda.memory_allocated() / 1024**3
        reserved = torch.cuda.memory_reserved() / 1024**3
        total = torch.cuda.get_device_properties(0).total_memory / 1024**3
        
        return {
            "allocated_gb": f"{allocated:.2f}",
            "reserved_gb": f"{reserved:.2f}",
            "total_gb": f"{total:.2f}",
            "free_gb": f"{total - allocated:.2f}",
            "usage_percent": f"{(allocated / total * 100):.1f}%"
        }
    else:
        return {"message": "Not using GPU"}

@app.post("/clear_cache")
async def clear_cache():
    """Clear GPU cache to free memory"""
    if device.type == "cuda":
        torch.cuda.empty_cache()
        gc.collect()
        return {"message": "GPU cache cleared"}
    return {"message": "Not using GPU"}

if __name__ == "__main__":
    print("\n" + "="*60)
    print("🚀 Starting REAL Qwen2.5-VL-7B Server")
    print("="*60)
    print("This is NOT a mock - using actual 7B model with GPU")
    print("No shortcuts!")
    print("="*60 + "\n")
    
    uvicorn.run(app, host="0.0.0.0", port=8000)