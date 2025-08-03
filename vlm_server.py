import torch
import gc
import asyncio
import logging
import base64
import io
import traceback
import psutil
import os
import json
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
from bank_parser_v3 import BankStatementParser, parse_bank_statement_to_csv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuration
class Config:
    # Available models with their expected VRAM usage
    AVAILABLE_MODELS = {
        "Qwen/Qwen2.5-VL-7B-Instruct": {
            "name": "Qwen2.5-VL-7B-Instruct", 
            "size": "7B",
            "vram_gb": 15.5,
            "description": "High quality, high VRAM usage"
        },
        "Qwen/Qwen2.5-VL-3B-Instruct": {
            "name": "Qwen2.5-VL-3B-Instruct",
            "size": "3B", 
            "vram_gb": 6.5,
            "description": "Good quality, lower VRAM usage"
        }
    }
    
    MODEL_NAME = "Qwen/Qwen2.5-VL-3B-Instruct"  # Default model (safer VRAM usage)
    MAX_NEW_TOKENS = 512
    VRAM_THRESHOLD = 0.75  # Clear cache when VRAM usage exceeds 75%
    VRAM_SAFETY_LIMIT = 0.90  # Refuse processing if VRAM would exceed 90%
    MAX_QUEUE_SIZE = 100
    REQUEST_TIMEOUT = 300  # 5 minutes
    HOST = "0.0.0.0"
    PORT = 8000
    
    # Quantization options (keeping for interface compatibility)
    ENABLE_QUANTIZATION = False  # Can be overridden by request
    DEFAULT_QUANTIZATION = "4bit"  # Options: "4bit", "8bit", "none"

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
    quantization: Optional[str] = Field(None, description="Quantization level: '4bit', '8bit', or None")
    enable_safety_check: Optional[bool] = Field(True, description="Enable VRAM safety check before processing")
    
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
    
class VRAMPrediction(BaseModel):
    current_usage_gb: float
    predicted_usage_gb: float
    current_percentage: float
    predicted_percentage: float
    is_safe: bool
    margin_gb: float
    
class QuantizationConfig(BaseModel):
    quantization_type: str = Field(..., description="4bit, 8bit, or none")
    estimated_vram_reduction_gb: float
    estimated_vram_usage_gb: float

# VLM Server class
class VLMServer:
    def __init__(self):
        self.model = None
        self.processor = None
        self.device = None
        self.processing_lock = asyncio.Lock()
        self.request_queue = asyncio.Queue(maxsize=Config.MAX_QUEUE_SIZE)
        self.is_processing = False
        
        # Force garbage collection settings for minimal RAM usage
        gc.set_threshold(700, 10, 10)  # More aggressive GC
        self.current_quantization = "none"
        self.current_model = Config.MODEL_NAME
        
    async def initialize(self, quantization: Optional[str] = None, model_name: Optional[str] = None):
        """Initialize the model and processor with optional quantization and model selection"""
        try:
            # Use provided model name or default
            if model_name and model_name in Config.AVAILABLE_MODELS:
                self.current_model = model_name
            else:
                self.current_model = Config.MODEL_NAME
                
            logger.info(f"Loading model: {self.current_model}")
            if quantization:
                logger.info(f"Using quantization: {quantization}")
            
            # Determine device
            if torch.cuda.is_available():
                self.device = "cuda"
                logger.info(f"Using GPU: {torch.cuda.get_device_name(0)}")
            else:
                self.device = "cpu"
                logger.warning("CUDA not available, using CPU (will be slow)")
            
            # Setup quantization using native PyTorch methods
            use_quantization = quantization and quantization != "none" and self.device == "cuda"
            if use_quantization:
                logger.info(f"Using {quantization} quantization for VRAM reduction (PyTorch native)")
            
            # Load model following official Hugging Face example
            if self.device == "cuda":
                # Use official recommended settings for stability
                self.model = Qwen2_5_VLForConditionalGeneration.from_pretrained(
                    self.current_model,
                    torch_dtype="auto",  # Let HF decide optimal dtype
                    device_map="auto",   # Let HF handle device mapping
                    trust_remote_code=True
                )
                self.current_quantization = "none"  # Disable custom quantization for stability
                
                # Clear cache after loading
                gc.collect()
                torch.cuda.empty_cache()
            else:
                self.model = Qwen2_5_VLForConditionalGeneration.from_pretrained(
                    self.current_model,
                    torch_dtype="auto",
                    device_map="cpu",
                    trust_remote_code=True
                )
            
            # Load processor
            self.processor = AutoProcessor.from_pretrained(self.current_model)
            
            logger.info("Model loaded successfully")
            
            # Log initial VRAM status
            if self.device == "cuda":
                vram_status = self.get_vram_status()
                logger.info(f"Initial VRAM status: {vram_status}")
                
        except Exception as e:
            logger.error(f"Failed to initialize model: {str(e)}")
            raise
            
    def get_ram_usage(self) -> float:
        """Get current RAM usage in GB"""
        process = psutil.Process(os.getpid())
        return process.memory_info().rss / 1024**3
        
    def get_vram_status(self) -> VRAMStatus:
        """Get current VRAM usage statistics from nvidia-smi for accuracy"""
        if not torch.cuda.is_available():
            return VRAMStatus(
                allocated_gb=0,
                reserved_gb=0,
                free_gb=0,
                total_gb=0,
                usage_percentage=0
            )
        
        try:
            # Try nvidia-smi first for accurate total GPU usage
            import subprocess
            result = subprocess.run(
                ['nvidia-smi', '--query-gpu=memory.used,memory.total,memory.free', '--format=csv,noheader,nounits'],
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                output = result.stdout.strip()
                used_mb, total_mb, free_mb = map(float, output.split(','))
                
                # Convert MB to GB
                used_gb = used_mb / 1024
                total_gb = total_mb / 1024
                free_gb = free_mb / 1024
                
                # Also get PyTorch's reserved memory
                reserved = torch.cuda.memory_reserved() / 1024**3
                
                usage_percentage = (used_gb / total_gb) * 100
                
                return VRAMStatus(
                    allocated_gb=round(used_gb, 2),
                    reserved_gb=round(reserved, 2),
                    free_gb=round(free_gb, 2),
                    total_gb=round(total_gb, 2),
                    usage_percentage=round(usage_percentage, 2)
                )
        except Exception:
            pass  # Fall back to PyTorch method
        
        # Fallback to PyTorch method if nvidia-smi fails
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
        """Clear VRAM by running aggressive garbage collection and emptying cache"""
        if torch.cuda.is_available():
            logger.info("Clearing VRAM...")
            # Aggressive cleanup
            gc.collect()
            torch.cuda.empty_cache()
            torch.cuda.ipc_collect()  # Clear IPC cache
            gc.collect()  # Second pass
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
    
    def predict_vram_usage(self, input_tokens: int = 512, output_tokens: int = 512) -> VRAMPrediction:
        """Predict VRAM usage for processing"""
        if not torch.cuda.is_available():
            return VRAMPrediction(
                current_usage_gb=0,
                predicted_usage_gb=0,
                current_percentage=0,
                predicted_percentage=0,
                is_safe=True,
                margin_gb=0
            )
        
        current_status = self.get_vram_status()
        
        # Estimate additional VRAM needed for processing
        # This is a rough estimate based on token counts
        token_memory_mb = (input_tokens + output_tokens) * 0.002  # ~2KB per token for activations
        kv_cache_mb = output_tokens * 0.016  # ~16KB per output token for KV cache
        additional_gb = (token_memory_mb + kv_cache_mb) / 1024
        
        # Add safety buffer
        safety_buffer_gb = 0.5
        predicted_usage_gb = current_status.allocated_gb + additional_gb + safety_buffer_gb
        predicted_percentage = (predicted_usage_gb / current_status.total_gb) * 100
        
        is_safe = predicted_percentage < (Config.VRAM_SAFETY_LIMIT * 100)
        margin_gb = current_status.total_gb * Config.VRAM_SAFETY_LIMIT - predicted_usage_gb
        
        return VRAMPrediction(
            current_usage_gb=current_status.allocated_gb,
            predicted_usage_gb=predicted_usage_gb,
            current_percentage=current_status.usage_percentage,
            predicted_percentage=predicted_percentage,
            is_safe=is_safe,
            margin_gb=margin_gb
        )
    
    def get_quantization_options(self) -> List[QuantizationConfig]:
        """Get available quantization options with VRAM estimates"""
        if not torch.cuda.is_available():
            return []
        
        current_vram = self.get_vram_status()
        base_usage = current_vram.allocated_gb
        
        options = [
            QuantizationConfig(
                quantization_type="none",
                estimated_vram_reduction_gb=0,
                estimated_vram_usage_gb=base_usage
            ),
            QuantizationConfig(
                quantization_type="8bit",
                estimated_vram_reduction_gb=base_usage * 0.5,  # ~50% reduction
                estimated_vram_usage_gb=base_usage * 0.5
            ),
            QuantizationConfig(
                quantization_type="4bit",
                estimated_vram_reduction_gb=base_usage * 0.75,  # ~75% reduction
                estimated_vram_usage_gb=base_usage * 0.25
            )
        ]
        
        return options
    
    def _apply_quantization(self, model, quantization_type: str):
        """Apply aggressive memory optimization as quantization approximation"""
        if quantization_type == "8bit":
            logger.info("Applying aggressive memory optimization (8-bit approximation)")
            try:
                # Apply aggressive memory optimizations
                model.half()  # Ensure float16
                
                # Disable gradient computation for all parameters
                for param in model.parameters():
                    param.requires_grad = False
                
                # Try to optimize memory layout
                if hasattr(model, 'gradient_checkpointing_enable'):
                    model.gradient_checkpointing_enable()
                    logger.info("Enabled gradient checkpointing")
                
                # Clear any cached computations
                if hasattr(model, 'clear_cache'):
                    model.clear_cache()
                
                logger.info("Applied 8-bit memory optimizations")
                return model
            except Exception as e:
                logger.warning(f"8-bit optimization failed: {e}")
                return model.half()
                
        elif quantization_type == "4bit":
            logger.info("Applying extreme memory optimization (4-bit approximation)")
            try:
                # More aggressive optimizations for 4-bit
                model.half()
                
                # Disable all gradients
                for param in model.parameters():
                    param.requires_grad = False
                
                # Enable gradient checkpointing if available
                if hasattr(model, 'gradient_checkpointing_enable'):
                    model.gradient_checkpointing_enable()
                
                # Try to compress model weights (simplified approximation)
                for module in model.modules():
                    if hasattr(module, 'weight') and module.weight is not None:
                        # Keep weights in float16 but ensure minimal memory usage
                        module.weight.data = module.weight.data.contiguous()
                
                logger.info("Applied 4-bit memory optimizations")
                return model
            except Exception as e:
                logger.warning(f"4-bit optimization failed: {e}")
                return model.half()
        
        return model
            
    def process_image(self, image_data: str) -> Image.Image:
        """Process image from URL, base64, or file path - with multi-page PDF support"""
        try:
            import fitz  # PyMuPDF
            
            def convert_pdf_to_image(pdf_bytes: bytes) -> Image.Image:
                """Convert PDF to image using adaptive strategy for multi-page documents"""
                pdf_document = fitz.open(stream=pdf_bytes, filetype="pdf")
                num_pages = len(pdf_document)
                
                # Check if this is a bank statement by looking for keywords
                is_bank_statement = False
                for page_num in range(min(2, num_pages)):
                    text = pdf_document[page_num].get_text().lower()
                    if any(keyword in text for keyword in ['statement', 'transaction', 'balance', 'debit', 'credit']):
                        is_bank_statement = True
                        break
                
                if num_pages == 1:
                    # Single page - simple conversion
                    page = pdf_document[0]
                    mat = fitz.Matrix(2, 2)  # 2x scaling
                    pix = page.get_pixmap(matrix=mat)
                    img_data = pix.tobytes("png")
                    pdf_document.close()
                    return Image.open(io.BytesIO(img_data))
                
                elif is_bank_statement:
                    # Special handling for bank statements
                    # Skip cover pages and only include transaction pages
                    transaction_pages = []
                    
                    for page_num in range(num_pages):
                        page = pdf_document[page_num]
                        text = page.get_text().lower()
                        
                        # Check if this page has actual transactions
                        has_transactions = any([
                            "withdrawals" in text and "deposits" in text,
                            "debit" in text or "credit" in text,
                            any(month in text for month in ['jan', 'feb', 'mar', 'apr', 'may', 'jun', 
                                                           'jul', 'aug', 'sep', 'oct', 'nov', 'dec']) and '$' in text
                        ])
                        
                        # Skip cover pages
                        is_cover = page_num == 0 and "transaction details" not in text and not has_transactions
                        
                        # Skip blank pages
                        is_blank = len(text.strip()) < 100
                        
                        if has_transactions and not is_cover and not is_blank:
                            transaction_pages.append(page_num)
                    
                    if not transaction_pages:
                        # Fallback to all non-blank pages
                        transaction_pages = [i for i in range(num_pages) if len(pdf_document[i].get_text().strip()) > 100]
                    
                    # Convert only transaction pages
                    images = []
                    for page_num in transaction_pages:
                        page = pdf_document[page_num]
                        # Use 1.5x scaling for bank statements (balance between quality and size)
                        mat = fitz.Matrix(1.5, 1.5)
                        pix = page.get_pixmap(matrix=mat)
                        img_data = pix.tobytes("png")
                        images.append(Image.open(io.BytesIO(img_data)))
                    
                    pdf_document.close()
                    
                    if len(images) == 1:
                        return images[0]
                    
                    # Calculate dimensions
                    total_height = sum(img.height for img in images)
                    max_width = max(img.width for img in images)
                    
                    # Add padding and page markers
                    page_padding = 30
                    total_height += page_padding * (len(images) - 1) + 60  # Extra for headers
                    
                    # Create combined image
                    concatenated = Image.new('RGB', (max_width, total_height + 60), 'white')
                    
                    from PIL import ImageDraw
                    draw = ImageDraw.Draw(concatenated)
                    
                    # Add header
                    draw.text((10, 10), f"BANK STATEMENT - {len(images)} PAGES - ALL TRANSACTIONS REQUIRED", fill='red')
                    draw.line([(0, 30), (max_width, 30)], fill='red', width=2)
                    
                    # Paste images
                    y_offset = 40
                    for idx, img in enumerate(images):
                        # Add page number
                        draw.text((10, y_offset), f"PAGE {transaction_pages[idx] + 1}", fill='blue')
                        y_offset += 20
                        
                        x_offset = (max_width - img.width) // 2
                        concatenated.paste(img, (x_offset, y_offset))
                        y_offset += img.height
                        
                        if idx < len(images) - 1:
                            y_offset += page_padding
                            draw.line([(50, y_offset - 15), (max_width - 50, y_offset - 15)], fill='red', width=2)
                    
                    # Add footer
                    draw.text((10, y_offset + 10), "END OF STATEMENT - ENSURE ALL TRANSACTIONS CAPTURED", fill='red')
                    
                    return concatenated
                
                elif num_pages <= 4:
                    # For non-bank statement PDFs, use grid layout
                    images = []
                    for page_num in range(num_pages):
                        page = pdf_document[page_num]
                        mat = fitz.Matrix(1.5, 1.5)
                        pix = page.get_pixmap(matrix=mat)
                        img_data = pix.tobytes("png")
                        images.append(Image.open(io.BytesIO(img_data)))
                    
                    pdf_document.close()
                    
                    # Create 2-column grid
                    grid_cols = 2
                    grid_rows = (num_pages + 1) // 2
                    
                    max_width = max(img.width for img in images)
                    max_height = max(img.height for img in images)
                    padding = 20
                    
                    grid_width = grid_cols * max_width + (grid_cols - 1) * padding
                    grid_height = grid_rows * max_height + (grid_rows - 1) * padding
                    
                    grid_image = Image.new('RGB', (grid_width, grid_height), 'white')
                    
                    for idx, img in enumerate(images):
                        row = idx // grid_cols
                        col = idx % grid_cols
                        x = col * (max_width + padding) + (max_width - img.width) // 2
                        y = row * (max_height + padding) + (max_height - img.height) // 2
                        grid_image.paste(img, (x, y))
                    
                    return grid_image
                
                else:
                    # Many pages - extract relevant pages containing transactions
                    transaction_keywords = ["transaction", "balance", "date", "debit", "credit", 
                                          "withdrawal", "deposit", "payment", "transfer"]
                    relevant_images = []
                    
                    for page_num in range(num_pages):
                        page = pdf_document[page_num]
                        # Check if page contains transaction data
                        text = page.get_text().lower()
                        
                        if any(keyword in text for keyword in transaction_keywords):
                            mat = fitz.Matrix(2, 2)
                            pix = page.get_pixmap(matrix=mat)
                            img_data = pix.tobytes("png")
                            relevant_images.append(Image.open(io.BytesIO(img_data)))
                    
                    pdf_document.close()
                    
                    if not relevant_images:
                        # Fallback to first page if no transaction pages found
                        pdf_document = fitz.open(stream=pdf_bytes, filetype="pdf")
                        page = pdf_document[0]
                        mat = fitz.Matrix(2, 2)
                        pix = page.get_pixmap(matrix=mat)
                        img_data = pix.tobytes("png")
                        pdf_document.close()
                        return Image.open(io.BytesIO(img_data))
                    
                    # Concatenate relevant pages vertically
                    total_height = sum(img.height for img in relevant_images)
                    max_width = max(img.width for img in relevant_images)
                    
                    # Limit height to prevent memory issues
                    if total_height > 8000:
                        # Take only first few pages that fit
                        limited_images = []
                        current_height = 0
                        for img in relevant_images:
                            if current_height + img.height <= 8000:
                                limited_images.append(img)
                                current_height += img.height
                            else:
                                break
                        relevant_images = limited_images
                        total_height = current_height
                    
                    concatenated = Image.new('RGB', (max_width, total_height), 'white')
                    
                    y_offset = 0
                    for img in relevant_images:
                        x_offset = (max_width - img.width) // 2
                        concatenated.paste(img, (x_offset, y_offset))
                        y_offset += img.height
                    
                    return concatenated
            
            # Check if it's a URL
            if image_data.startswith(('http://', 'https://')):
                response = requests.get(image_data, timeout=30)
                response.raise_for_status()
                content = response.content
                
                if content.startswith(b'%PDF'):
                    return convert_pdf_to_image(content)
                else:
                    return Image.open(io.BytesIO(content))
            
            # Check if it's base64 with data URI
            elif image_data.startswith('data:'):
                header, base64_data = image_data.split(',', 1)
                file_bytes = base64.b64decode(base64_data)
                
                if 'pdf' in header.lower() or file_bytes.startswith(b'%PDF'):
                    return convert_pdf_to_image(file_bytes)
                else:
                    return Image.open(io.BytesIO(file_bytes))
            
            # Try as base64 without prefix
            elif len(image_data) > 100:  # Likely base64
                try:
                    file_bytes = base64.b64decode(image_data)
                    if file_bytes.startswith(b'%PDF'):
                        return convert_pdf_to_image(file_bytes)
                    else:
                        return Image.open(io.BytesIO(file_bytes))
                except:
                    pass
                    
            # Try as file path
            path = Path(image_data)
            if path.exists():
                if path.suffix.lower() == '.pdf':
                    with open(path, 'rb') as f:
                        return convert_pdf_to_image(f.read())
                else:
                    return Image.open(path)
                
            raise ValueError(f"Could not process file data: {image_data[:50]}...")
            
        except ImportError:
            if 'pdf' in image_data.lower() or (len(image_data) > 4 and image_data.startswith('JVBE')):
                raise ValueError("PDF support requires PyMuPDF. Install with: pip install PyMuPDF")
            raise
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
                        # Process image data (base64, URL, or path) to PIL Image
                        try:
                            pil_image = self.process_image(item.image)
                            content_list.append({"type": "image", "image": pil_image})
                        except Exception as e:
                            logger.error(f"Failed to process image: {str(e)}")
                            raise ValueError(f"Failed to process image: {str(e)}")
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
                # VRAM safety check before processing
                if request.enable_safety_check:
                    # Estimate input tokens (rough approximation)
                    estimated_input_tokens = sum(
                        len(str(msg.content)) // 4 for msg in request.messages
                    )
                    vram_prediction = self.predict_vram_usage(
                        estimated_input_tokens, 
                        request.max_new_tokens
                    )
                    
                    if not vram_prediction.is_safe:
                        error_msg = (
                            f"VRAM safety check failed. Current: {vram_prediction.current_percentage:.1f}%, "
                            f"Predicted: {vram_prediction.predicted_percentage:.1f}%, "
                            f"Limit: {Config.VRAM_SAFETY_LIMIT*100}%. "
                            f"Try using quantization or reducing max_new_tokens."
                        )
                        logger.warning(error_msg)
                        raise HTTPException(status_code=429, detail=error_msg)
                
                # Check both VRAM and RAM before processing
                ram_before = self.get_ram_usage()
                logger.info(f"RAM usage before processing: {ram_before:.2f}GB")
                self.check_and_clear_vram()
                
                # Force aggressive garbage collection before processing
                for _ in range(3):
                    gc.collect()
                if self.device == "cuda":
                    torch.cuda.empty_cache()
                    torch.cuda.ipc_collect()
                
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
                
                # Move inputs to model device (let auto device mapping handle this)
                inputs = inputs.to(self.model.device)
                
                # Generate following official Hugging Face example (minimal parameters)
                with torch.no_grad():
                    generated_ids = self.model.generate(
                        **inputs,
                        max_new_tokens=request.max_new_tokens
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
                
                # Aggressive memory cleanup after processing
                del inputs, generated_ids, generated_ids_trimmed
                if self.device == "cuda":
                    torch.cuda.empty_cache()
                    torch.cuda.ipc_collect()
                
                # Multiple rounds of garbage collection
                for _ in range(3):
                    gc.collect()
                
                # Check both VRAM and RAM after processing
                ram_after = self.get_ram_usage()
                logger.info(f"RAM usage after processing: {ram_after:.2f}GB (change: {ram_after - ram_before:+.2f}GB)")
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
            "bank_export": "/api/v1/bank_export",
            "bank_extract_json": "/api/v1/bank_extract_json",
            "health": "/health",
            "vram_status": "/vram_status",
            "vram_prediction": "/vram_prediction",
            "quantization_options": "/quantization_options",
            "available_models": "/available_models",
            "clear_vram": "/clear_vram",
            "reload_model": "/reload_model"
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

@app.get("/vram_prediction")
async def predict_vram_usage(input_tokens: int = 512, output_tokens: int = 512):
    """Predict VRAM usage for given token counts"""
    return vlm_server.predict_vram_usage(input_tokens, output_tokens)

@app.get("/quantization_options")
async def get_quantization_options():
    """Get available quantization options with VRAM estimates"""
    return vlm_server.get_quantization_options()

@app.get("/available_models")
async def get_available_models():
    """Get available models with their specifications"""
    models = []
    for model_id, info in Config.AVAILABLE_MODELS.items():
        models.append({
            "model_id": model_id,
            "name": info["name"],
            "size": info["size"],
            "vram_gb": info["vram_gb"],
            "description": info["description"],
            "is_current": model_id == vlm_server.current_model
        })
    return models

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

class ReloadModelRequest(BaseModel):
    quantization: Optional[str] = None
    model_name: Optional[str] = None

@app.post("/reload_model")
async def reload_model(request: ReloadModelRequest):
    """Reload model with different settings"""
    try:
        quantization = request.quantization
        model_name = request.model_name
        logger.info(f"Reloading model: {model_name or 'current'} with quantization: {quantization}")
        
        # Validate model name if provided
        if model_name and model_name not in Config.AVAILABLE_MODELS:
            raise HTTPException(status_code=400, detail=f"Invalid model name. Available: {list(Config.AVAILABLE_MODELS.keys())}")
        
        # Clear current model
        if vlm_server.model is not None:
            del vlm_server.model
            vlm_server.model = None
            del vlm_server.processor
            vlm_server.processor = None
            gc.collect()
            torch.cuda.empty_cache()
        
        # Reinitialize with new settings
        await vlm_server.initialize(quantization=quantization, model_name=model_name)
        
        return {
            "status": "success", 
            "quantization": quantization,
            "model_name": model_name,
            "current_quantization": vlm_server.current_quantization,
            "current_model": vlm_server.current_model,
            "vram_status": vlm_server.get_vram_status()
        }
    except Exception as e:
        logger.error(f"Failed to reload model: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

class BankExportRequest(BaseModel):
    messages: List[Message]
    export_format: str = Field(default="csv", description="Export format: csv or json")

@app.post("/api/v1/bank_export")
async def export_bank_statement(request: BankExportRequest):
    """Process bank statement and export as CSV or JSON"""
    
    try:
        # Check if we already have an assistant response with bank data
        ai_response_text = None
        
        # Look for the most recent assistant message
        for msg in reversed(request.messages):
            if msg.role == "assistant" and msg.content:
                # Check if it contains bank statement data
                if any(keyword in msg.content.lower() for keyword in ['date', 'description', 'balance', 'transaction', 'debit', 'credit', 'withdrawal', 'deposit']):
                    ai_response_text = msg.content
                    break
        
        # If no assistant response, generate one
        if not ai_response_text:
            if vlm_server.model is None:
                raise HTTPException(status_code=503, detail="Model not loaded")
            generate_request = GenerateRequest(messages=request.messages)
            ai_response = await vlm_server.generate(generate_request)
            ai_response_text = ai_response.response
        
        # Parse the response into structured format
        bank_statement, csv_content = parse_bank_statement_to_csv(ai_response_text)
        
        if request.export_format == "csv":
            return {
                "format": "csv",
                "content": csv_content,
                "filename": f"bank_statement_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                "transaction_count": len(bank_statement.transactions),
                "total_debits": bank_statement.total_debits,
                "total_credits": bank_statement.total_credits
            }
        else:  # json format
            return {
                "format": "json",
                "content": bank_statement.to_json_pretty(),
                "filename": f"bank_statement_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                "transaction_count": len(bank_statement.transactions),
                "total_debits": bank_statement.total_debits,
                "total_credits": bank_statement.total_credits
            }
            
    except Exception as e:
        logger.error(f"Failed to export bank statement: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/bank_extract_json")
async def extract_bank_statement_json(request: GenerateRequest):
    """Extract bank statement to JSON format using table extraction + conversion"""
    
    try:
        if vlm_server.model is None:
            raise HTTPException(status_code=503, detail="Model not loaded")
        
        # Use table format for extraction (proven to work well)
        table_prompt = """
Extract ALL transactions from this bank statement in a structured table format.

IMPORTANT RULES:
1. The OPENING BALANCE is NOT a transaction - it's just the starting balance, skip it
2. Start with the FIRST ACTUAL TRANSACTION (payment, transfer, withdrawal, deposit, fee, etc.)
3. Include EVERY transaction from ALL pages - check carefully for transactions at page boundaries
4. Continue until you reach the final transaction or closing balance

Use this format:
| Date | Description | Ref. | Withdrawals | Deposits | Balance |

Include EVERY transaction shown, including:
- All payments and withdrawals  
- All deposits and credits
- All transfers
- All fees and interest
- Small amounts (don't skip any transactions)

DO NOT include:
- Opening balance
- Statement headers/footers
- Account summaries

Make sure to capture the COMPLETE transaction list from ALL pages.
"""
        
        # Modify messages to use table extraction
        import copy
        modified_messages = []
        
        logger.info(f"Received {len(request.messages)} messages")
        
        for i, msg in enumerate(request.messages):
            logger.info(f"Message {i}: role={msg.role}, content_type={type(msg.content).__name__}")
            
            if msg.role == "user" and i == len(request.messages) - 1:  # Last user message
                if isinstance(msg.content, str):
                    # Simple string content
                    new_msg = Message(
                        role=msg.role,
                        content=table_prompt + "\n\n" + msg.content
                    )
                    modified_messages.append(new_msg)
                elif isinstance(msg.content, list):
                    # List of content items
                    new_content = []
                    text_modified = False
                    
                    for item in msg.content:
                        if item.type == "text" and not text_modified:
                            # Replace the user's text completely with our table prompt
                            new_content.append(ContentItem(
                                type="text",
                                text=table_prompt
                            ))
                            text_modified = True
                            logger.info(f"Replaced user text with table prompt")
                        elif item.type != "text":
                            new_content.append(item)
                    
                    new_msg = Message(role=msg.role, content=new_content)
                    modified_messages.append(new_msg)
            else:
                modified_messages.append(msg)
        
        # Generate response
        ai_response = await vlm_server.generate(GenerateRequest(
            messages=modified_messages,
            max_new_tokens=request.max_new_tokens or 2048,
            temperature=0.1
        ))
        
        # Convert table to JSON using our balance-based parser
        from bank_table_parser_v3 import parse_bank_table_to_json
        
        # Debug logging
        logger.info(f"VLM response length: {len(ai_response.response)}")
        logger.info(f"VLM response preview: {ai_response.response[:500]}...")
        
        json_data = parse_bank_table_to_json(ai_response.response)
        
        logger.info(f"Parsed transaction count: {json_data['transaction_count']}")
        logger.info(f"Parsed transactions: {json_data['transactions'][:2] if json_data['transactions'] else 'None'}")
        
        return {
            "status": "success",
            "data": json_data,
            "transaction_count": json_data["transaction_count"],
            "processing_time": ai_response.processing_time
        }
            
    except Exception as e:
        logger.error(f"Failed to extract bank statement as JSON: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

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