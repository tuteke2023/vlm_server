import torch
import gc
import asyncio
import logging
import base64
import io
import traceback
from typing import List, Dict, Optional, Union
from datetime import datetime
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from transformers import Qwen2_5_VLForConditionalGeneration, AutoProcessor
from qwen_vl_utils import process_vision_info
from PIL import Image
import requests
import uvicorn

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuration
class Config:
    MODEL_NAME = "Qwen/Qwen2.5-VL-7B-Instruct"
    MAX_NEW_TOKENS = 512
    VRAM_THRESHOLD = 0.85  # Clear cache when VRAM usage exceeds 85%
    MAX_QUEUE_SIZE = 100
    REQUEST_TIMEOUT = 300  # 5 minutes
    HOST = "0.0.0.0"
    PORT = 8000

# Request/Response models
class ContentItem(BaseModel):
    type: str = Field(..., description="Type of content: 'text', 'image', or 'video'")
    text: Optional[str] = Field(None, description="Text content (required if type is 'text')")
    image: Optional[str] = Field(None, description="Image data - can be URL, base64, or file path")
    video: Optional[str] = Field(None, description="Video data - can be URL or file path")

class Message(BaseModel):
    role: str = Field(..., description="Message role: 'user' or 'assistant'")
    content: Union[str, List[ContentItem]] = Field(..., description="Message content")

class GenerateRequest(BaseModel):
    messages: List[Message] = Field(..., description="Conversation messages")
    max_new_tokens: Optional[int] = Field(512, description="Maximum tokens to generate")
    temperature: Optional[float] = Field(0.7, description="Sampling temperature")
    top_p: Optional[float] = Field(0.9, description="Top-p sampling parameter")
    
class GenerateResponse(BaseModel):
    response: str = Field(..., description="Generated response")
    usage: Dict = Field(..., description="Token usage statistics")
    processing_time: float = Field(..., description="Processing time in seconds")

class VRAMStatus(BaseModel):
    allocated_gb: float
    reserved_gb: float
    free_gb: float
    total_gb: float
    usage_percentage: float

# VLM Server class
class VLMServer:
    def __init__(self):
        self.model = None
        self.processor = None
        self.device = None
        self.processing_lock = asyncio.Lock()
        self.request_queue = asyncio.Queue(maxsize=Config.MAX_QUEUE_SIZE)
        self.is_processing = False
        
    async def initialize(self):
        """Initialize the model and processor"""
        try:
            logger.info(f"Loading model: {Config.MODEL_NAME}")
            
            # Determine device
            if torch.cuda.is_available():
                self.device = "cuda"
                logger.info(f"Using GPU: {torch.cuda.get_device_name(0)}")
            else:
                self.device = "cpu"
                logger.warning("CUDA not available, using CPU (will be slow)")
            
            # Load model with automatic device mapping
            self.model = Qwen2_5_VLForConditionalGeneration.from_pretrained(
                Config.MODEL_NAME,
                torch_dtype=torch.float16 if self.device == "cuda" else torch.float32,
                device_map="auto"
            )
            
            # Load processor
            self.processor = AutoProcessor.from_pretrained(Config.MODEL_NAME)
            
            logger.info("Model loaded successfully")
            
            # Log initial VRAM status
            if self.device == "cuda":
                vram_status = self.get_vram_status()
                logger.info(f"Initial VRAM status: {vram_status}")
                
        except Exception as e:
            logger.error(f"Failed to initialize model: {str(e)}")
            raise
            
    def get_vram_status(self) -> VRAMStatus:
        """Get current VRAM usage statistics"""
        if not torch.cuda.is_available():
            return VRAMStatus(
                allocated_gb=0,
                reserved_gb=0,
                free_gb=0,
                total_gb=0,
                usage_percentage=0
            )
            
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
        
    def clear_vram(self):
        """Clear VRAM by running garbage collection and emptying cache"""
        if torch.cuda.is_available():
            logger.info("Clearing VRAM...")
            gc.collect()
            torch.cuda.empty_cache()
            vram_status = self.get_vram_status()
            logger.info(f"VRAM after clearing: {vram_status}")
            
    def check_and_clear_vram(self):
        """Check VRAM usage and clear if necessary"""
        if not torch.cuda.is_available():
            return
            
        vram_status = self.get_vram_status()
        if vram_status.usage_percentage > Config.VRAM_THRESHOLD * 100:
            logger.warning(f"VRAM usage high ({vram_status.usage_percentage}%), clearing cache")
            self.clear_vram()
            
    def process_image(self, image_data: str) -> Image.Image:
        """Process image from URL, base64, or file path"""
        try:
            # Check if it's a URL
            if image_data.startswith(('http://', 'https://')):
                response = requests.get(image_data, timeout=30)
                response.raise_for_status()
                return Image.open(io.BytesIO(response.content))
                
            # Check if it's base64
            elif image_data.startswith('data:image'):
                # Extract base64 data
                base64_data = image_data.split(',')[1]
                image_bytes = base64.b64decode(base64_data)
                return Image.open(io.BytesIO(image_bytes))
                
            # Try as base64 without prefix
            elif len(image_data) > 100:  # Likely base64
                try:
                    image_bytes = base64.b64decode(image_data)
                    return Image.open(io.BytesIO(image_bytes))
                except:
                    pass
                    
            # Try as file path
            path = Path(image_data)
            if path.exists():
                return Image.open(path)
                
            raise ValueError(f"Could not process image data: {image_data[:50]}...")
            
        except Exception as e:
            logger.error(f"Error processing image: {str(e)}")
            raise
            
    def prepare_messages(self, messages: List[Message]) -> List[Dict]:
        """Convert API messages to model format"""
        formatted_messages = []
        
        for msg in messages:
            formatted_msg = {"role": msg.role}
            
            if isinstance(msg.content, str):
                formatted_msg["content"] = msg.content
            else:
                content_list = []
                for item in msg.content:
                    if item.type == "text":
                        content_list.append({"type": "text", "text": item.text})
                    elif item.type == "image":
                        content_list.append({"type": "image", "image": item.image})
                    elif item.type == "video":
                        content_list.append({"type": "video", "video": item.video})
                        
                formatted_msg["content"] = content_list
                
            formatted_messages.append(formatted_msg)
            
        return formatted_messages
        
    async def generate(self, request: GenerateRequest) -> GenerateResponse:
        """Generate response for the given messages"""
        start_time = datetime.now()
        
        async with self.processing_lock:
            try:
                # Check VRAM before processing
                self.check_and_clear_vram()
                
                # Prepare messages
                formatted_messages = self.prepare_messages(request.messages)
                
                # Apply chat template
                text = self.processor.apply_chat_template(
                    formatted_messages, 
                    tokenize=False, 
                    add_generation_prompt=True
                )
                
                # Process vision inputs
                image_inputs, video_inputs = process_vision_info(formatted_messages)
                
                # Prepare inputs
                inputs = self.processor(
                    text=[text],
                    images=image_inputs,
                    videos=video_inputs,
                    padding=True,
                    return_tensors="pt"
                )
                
                # Move to device
                inputs = inputs.to(self.device)
                
                # Generate
                with torch.no_grad():
                    generated_ids = self.model.generate(
                        **inputs,
                        max_new_tokens=request.max_new_tokens,
                        temperature=request.temperature,
                        top_p=request.top_p,
                        do_sample=True
                    )
                
                # Decode output
                generated_ids_trimmed = [
                    out_ids[len(in_ids):] for in_ids, out_ids in zip(inputs.input_ids, generated_ids)
                ]
                output_text = self.processor.batch_decode(
                    generated_ids_trimmed,
                    skip_special_tokens=True,
                    clean_up_tokenization_spaces=False
                )[0]
                
                # Calculate usage
                input_tokens = inputs.input_ids.shape[1]
                output_tokens = generated_ids_trimmed[0].shape[0]
                
                processing_time = (datetime.now() - start_time).total_seconds()
                
                # Check VRAM after processing
                self.check_and_clear_vram()
                
                return GenerateResponse(
                    response=output_text,
                    usage={
                        "input_tokens": input_tokens,
                        "output_tokens": output_tokens,
                        "total_tokens": input_tokens + output_tokens
                    },
                    processing_time=processing_time
                )
                
            except Exception as e:
                logger.error(f"Error during generation: {str(e)}")
                logger.error(traceback.format_exc())
                raise HTTPException(status_code=500, detail=str(e))

# Global server instance
vlm_server = VLMServer()

# FastAPI app with lifespan management
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await vlm_server.initialize()
    yield
    # Shutdown
    logger.info("Shutting down server...")
    vlm_server.clear_vram()

app = FastAPI(
    title="VLM Server API",
    description="Vision Language Model server based on Qwen2.5-VL-7B-Instruct",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware for web interface
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8080", "http://127.0.0.1:8080"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API Endpoints
@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "VLM Server",
        "model": Config.MODEL_NAME,
        "status": "running",
        "endpoints": {
            "generate": "/api/v1/generate",
            "health": "/health",
            "vram_status": "/vram_status"
        }
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "model_loaded": vlm_server.model is not None,
        "device": vlm_server.device
    }

@app.get("/vram_status", response_model=VRAMStatus)
async def get_vram_status():
    """Get current VRAM usage statistics"""
    return vlm_server.get_vram_status()

@app.post("/api/v1/generate", response_model=GenerateResponse)
async def generate(request: GenerateRequest):
    """Generate response from the VLM model"""
    if vlm_server.model is None:
        raise HTTPException(status_code=503, detail="Model not loaded")
        
    return await vlm_server.generate(request)

@app.post("/clear_vram")
async def clear_vram():
    """Manually trigger VRAM clearing"""
    vlm_server.clear_vram()
    return {"status": "success", "vram_status": vlm_server.get_vram_status()}

# Error handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail}
    )

@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    logger.error(f"Unhandled exception: {str(exc)}")
    logger.error(traceback.format_exc())
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )

if __name__ == "__main__":
    uvicorn.run(
        "vlm_server:app",
        host=Config.HOST,
        port=Config.PORT,
        reload=False,
        log_level="info"
    )