#!/usr/bin/env python3
"""Audio Transcription Service using OpenAI Whisper"""

import os
import logging
import tempfile
import torch
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, File, UploadFile, HTTPException, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import whisper
import uvicorn

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class Config:
    HOST = "0.0.0.0"
    PORT = 8001
    DEFAULT_MODEL = "base"  # tiny, base, small, medium, large
    DEVICE = "cuda" if torch.cuda.is_available() else "cpu"

class TranscriptionService:
    def __init__(self):
        self.model = None
        self.current_model_name = None
        self.device = Config.DEVICE
        logger.info(f"Using device: {self.device}")
        
    def load_model(self, model_name: str = Config.DEFAULT_MODEL):
        """Load Whisper model"""
        try:
            logger.info(f"Loading Whisper model: {model_name}")
            if self.model and self.current_model_name == model_name:
                logger.info("Model already loaded")
                return
                
            # Clear previous model
            if self.model:
                del self.model
                if self.device == "cuda":
                    torch.cuda.empty_cache()
            
            # Load new model
            self.model = whisper.load_model(model_name, device=self.device)
            self.current_model_name = model_name
            logger.info(f"Model {model_name} loaded successfully")
            
        except Exception as e:
            logger.error(f"Failed to load model: {str(e)}")
            raise
            
    def transcribe(self, audio_path: str, language: Optional[str] = None) -> dict:
        """Transcribe audio file"""
        if not self.model:
            raise HTTPException(status_code=503, detail="Model not loaded")
            
        try:
            # Transcribe
            options = {}
            if language:
                options['language'] = language
                
            result = self.model.transcribe(audio_path, **options)
            
            return {
                "text": result["text"],
                "language": result.get("language", "unknown"),
                "segments": result.get("segments", [])
            }
            
        except Exception as e:
            logger.error(f"Transcription failed: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))

# Initialize service
transcription_service = TranscriptionService()

# Create FastAPI app
app = FastAPI(title="Audio Transcription Service")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup_event():
    """Load default model on startup"""
    transcription_service.load_model()

@app.get("/")
async def root():
    return {
        "service": "Audio Transcription Service",
        "model": transcription_service.current_model_name,
        "status": "running",
        "device": transcription_service.device,
        "endpoints": {
            "transcribe": "/transcribe",
            "health": "/health",
            "models": "/models",
            "load_model": "/load_model"
        }
    }

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "model_loaded": transcription_service.model is not None,
        "current_model": transcription_service.current_model_name,
        "device": transcription_service.device
    }

@app.get("/models")
async def get_available_models():
    """Get list of available Whisper models"""
    return {
        "models": ["tiny", "base", "small", "medium", "large"],
        "current": transcription_service.current_model_name,
        "descriptions": {
            "tiny": "39M parameters, fastest, lower accuracy",
            "base": "74M parameters, good balance",
            "small": "244M parameters, better accuracy",
            "medium": "769M parameters, high accuracy",
            "large": "1550M parameters, best accuracy"
        }
    }

@app.post("/load_model")
async def load_model(model_name: str = Form(...)):
    """Load a specific Whisper model"""
    valid_models = ["tiny", "base", "small", "medium", "large"]
    if model_name not in valid_models:
        raise HTTPException(status_code=400, detail=f"Invalid model. Choose from: {valid_models}")
    
    try:
        transcription_service.load_model(model_name)
        return {"status": "success", "model": model_name}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/transcribe")
async def transcribe_audio(
    file: UploadFile = File(...),
    language: Optional[str] = Form(None),
    model: Optional[str] = Form(None)
):
    """Transcribe an audio file"""
    
    # Validate file type
    allowed_extensions = {'.wav', '.mp3', '.mp4', '.m4a', '.flac', '.ogg'}
    file_ext = Path(file.filename).suffix.lower()
    if file_ext not in allowed_extensions:
        raise HTTPException(
            status_code=400, 
            detail=f"Invalid file type. Allowed: {', '.join(allowed_extensions)}"
        )
    
    # Load different model if requested
    if model and model != transcription_service.current_model_name:
        transcription_service.load_model(model)
    
    # Save uploaded file temporarily
    with tempfile.NamedTemporaryFile(delete=False, suffix=file_ext) as tmp_file:
        content = await file.read()
        tmp_file.write(content)
        tmp_file_path = tmp_file.name
    
    try:
        # Transcribe
        result = transcription_service.transcribe(tmp_file_path, language)
        
        return JSONResponse(content={
            "filename": file.filename,
            "model": transcription_service.current_model_name,
            "transcription": result
        })
        
    finally:
        # Clean up
        os.unlink(tmp_file_path)

if __name__ == "__main__":
    uvicorn.run(app, host=Config.HOST, port=Config.PORT)