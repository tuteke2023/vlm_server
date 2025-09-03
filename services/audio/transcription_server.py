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
from transcript_storage import TranscriptStorage
from vector_storage import VectorTranscriptStorage, TranscriptRAG

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

# Initialize services
transcription_service = TranscriptionService()
transcript_storage = TranscriptStorage()
vector_storage = VectorTranscriptStorage()
transcript_rag = TranscriptRAG(vector_storage)

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
    model: Optional[str] = Form(None),
    save_transcript: bool = Form(True)
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
        
        # Save transcript if requested
        transcript_id = None
        vector_result = None
        if save_transcript:
            transcript_id = transcript_storage.save_transcript(
                content=result["text"],
                audio_filename=file.filename,
                language=result.get("language"),
                segments=result.get("segments"),
                metadata={
                    "model": transcription_service.current_model_name,
                    "file_size": len(content)
                }
            )
            
            # Also add to vector storage for semantic search
            if transcript_id and result["text"]:
                vector_result = vector_storage.add_transcript(
                    transcript_id=transcript_id,
                    text=result["text"],
                    metadata={
                        "filename": file.filename,
                        "language": result.get("language"),
                        "model": transcription_service.current_model_name
                    }
                )
        
        return JSONResponse(content={
            "filename": file.filename,
            "model": transcription_service.current_model_name,
            "transcription": result,
            "transcript_id": transcript_id
        })
        
    finally:
        # Clean up
        os.unlink(tmp_file_path)

@app.get("/transcripts")
async def list_transcripts(limit: int = 10, offset: int = 0):
    """List saved transcripts"""
    transcripts = transcript_storage.list_transcripts(limit, offset)
    return {"transcripts": transcripts}

@app.get("/transcripts/{transcript_id}")
async def get_transcript(transcript_id: str):
    """Get a specific transcript"""
    transcript = transcript_storage.get_transcript(transcript_id)
    if not transcript:
        raise HTTPException(status_code=404, detail="Transcript not found")
    return transcript

@app.delete("/transcripts/{transcript_id}")
async def delete_transcript(transcript_id: str):
    """Delete a transcript"""
    success = transcript_storage.delete_transcript(transcript_id)
    if not success:
        raise HTTPException(status_code=404, detail="Transcript not found")
    return {"status": "success", "message": "Transcript deleted"}

@app.post("/transcripts/{transcript_id}/to-chat")
async def send_transcript_to_chat(transcript_id: str):
    """Prepare transcript for chat integration"""
    transcript = transcript_storage.get_transcript(transcript_id)
    if not transcript:
        raise HTTPException(status_code=404, detail="Transcript not found")
    
    # Format transcript for chat context
    chat_context = {
        "type": "audio_transcript",
        "transcript_id": transcript_id,
        "content": transcript["content"],
        "metadata": {
            "filename": transcript.get("audio_filename", "Unknown"),
            "language": transcript.get("language", "Unknown"),
            "created_at": transcript.get("created_at"),
            "segments_available": bool(transcript.get("segments"))
        }
    }
    
    return chat_context

@app.post("/transcripts/search")
async def semantic_search(
    query: str = Form(...),
    n_results: int = Form(5),
    transcript_ids: Optional[str] = Form(None)
):
    """Semantic search across transcripts"""
    
    # Parse transcript IDs if provided
    ids_list = None
    if transcript_ids:
        ids_list = [id.strip() for id in transcript_ids.split(",")]
    
    # Perform semantic search
    results = vector_storage.search(
        query=query,
        n_results=n_results,
        transcript_ids=ids_list
    )
    
    # Enhance results with full transcript metadata
    enhanced_results = []
    for result in results:
        transcript = transcript_storage.get_transcript(result["transcript_id"])
        if transcript:
            result["transcript_metadata"] = {
                "filename": transcript.get("audio_filename"),
                "language": transcript.get("language"),
                "created_at": transcript.get("created_at")
            }
        enhanced_results.append(result)
    
    return {
        "query": query,
        "results": enhanced_results,
        "count": len(enhanced_results)
    }

@app.post("/transcripts/rag")
async def transcript_rag(
    query: str = Form(...),
    max_context_length: int = Form(2000),
    n_chunks: int = Form(5)
):
    """Get RAG context for a query"""
    
    # Get relevant context
    context, sources = transcript_rag.get_context_for_query(
        query=query,
        max_context_length=max_context_length,
        n_chunks=n_chunks
    )
    
    if not context:
        return {
            "query": query,
            "context": "",
            "sources": [],
            "prompt": "",
            "message": "No relevant context found"
        }
    
    # Format RAG prompt
    prompt = transcript_rag.format_rag_prompt(query, context)
    
    return {
        "query": query,
        "context": context,
        "sources": sources,
        "prompt": prompt,
        "context_length": len(context)
    }

@app.get("/transcripts/{transcript_id}/similar")
async def find_similar_transcripts(
    transcript_id: str,
    n_results: int = 3
):
    """Find transcripts similar to the given one"""
    
    # Check if transcript exists
    transcript = transcript_storage.get_transcript(transcript_id)
    if not transcript:
        raise HTTPException(status_code=404, detail="Transcript not found")
    
    # Find similar transcripts
    similar = vector_storage.find_similar_transcripts(
        transcript_id=transcript_id,
        n_results=n_results
    )
    
    # Enhance with metadata
    enhanced_similar = []
    for item in similar:
        similar_transcript = transcript_storage.get_transcript(item["transcript_id"])
        if similar_transcript:
            item["metadata"] = {
                "filename": similar_transcript.get("audio_filename"),
                "language": similar_transcript.get("language"),
                "created_at": similar_transcript.get("created_at"),
                "preview": similar_transcript.get("content", "")[:200]
            }
        enhanced_similar.append(item)
    
    return {
        "source_transcript": {
            "id": transcript_id,
            "filename": transcript.get("audio_filename")
        },
        "similar_transcripts": enhanced_similar
    }

@app.delete("/transcripts/{transcript_id}")
async def delete_transcript_enhanced(transcript_id: str):
    """Delete a transcript from both storages"""
    
    # Delete from vector storage
    vector_deleted = vector_storage.delete_transcript(transcript_id)
    
    # Delete from SQL storage
    sql_deleted = transcript_storage.delete_transcript(transcript_id)
    
    if not sql_deleted:
        raise HTTPException(status_code=404, detail="Transcript not found")
    
    return {
        "status": "success",
        "message": "Transcript deleted",
        "vector_storage_deleted": vector_deleted,
        "sql_storage_deleted": sql_deleted
    }

@app.get("/vector/stats")
async def get_vector_stats():
    """Get statistics about the vector store"""
    stats = vector_storage.get_statistics()
    return stats

if __name__ == "__main__":
    uvicorn.run(app, host=Config.HOST, port=Config.PORT)