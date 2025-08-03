#!/usr/bin/env python3
"""
Fix for PDF upload processing in VLM server
Adds PDF-to-image conversion capability
"""

import base64
import io
from PIL import Image
import fitz  # PyMuPDF
from typing import List, Union

def convert_pdf_to_images(pdf_bytes: bytes) -> List[Image.Image]:
    """Convert PDF bytes to list of PIL Images (one per page)"""
    try:
        # Open PDF from bytes
        pdf_document = fitz.open(stream=pdf_bytes, filetype="pdf")
        images = []
        
        for page_num in range(len(pdf_document)):
            page = pdf_document[page_num]
            # Render page to image (2x scale for better quality)
            mat = fitz.Matrix(2, 2)  # 2x scaling
            pix = page.get_pixmap(matrix=mat)
            
            # Convert to PIL Image
            img_data = pix.tobytes("png")
            img = Image.open(io.BytesIO(img_data))
            images.append(img)
        
        pdf_document.close()
        return images
    except Exception as e:
        raise ValueError(f"Failed to convert PDF: {str(e)}")

def process_image_with_pdf_support(image_data: str) -> Union[Image.Image, List[Image.Image]]:
    """Process image from URL, base64, or file path - now with PDF support"""
    try:
        # Check if it's a URL
        if image_data.startswith(('http://', 'https://')):
            import requests
            response = requests.get(image_data, timeout=30)
            response.raise_for_status()
            content = response.content
            
            # Check if it's a PDF
            if content.startswith(b'%PDF'):
                return convert_pdf_to_images(content)
            else:
                return Image.open(io.BytesIO(content))
        
        # Check if it's base64 with data URI
        elif image_data.startswith('data:'):
            # Extract mime type and base64 data
            header, base64_data = image_data.split(',', 1)
            
            # Decode base64
            file_bytes = base64.b64decode(base64_data)
            
            # Check if it's a PDF
            if 'pdf' in header.lower() or file_bytes.startswith(b'%PDF'):
                return convert_pdf_to_images(file_bytes)
            else:
                return Image.open(io.BytesIO(file_bytes))
        
        # Try as base64 without prefix
        elif len(image_data) > 100:  # Likely base64
            try:
                file_bytes = base64.b64decode(image_data)
                # Check if it's a PDF
                if file_bytes.startswith(b'%PDF'):
                    return convert_pdf_to_images(file_bytes)
                else:
                    return Image.open(io.BytesIO(file_bytes))
            except:
                pass
        
        # Try as file path
        from pathlib import Path
        path = Path(image_data)
        if path.exists():
            if path.suffix.lower() == '.pdf':
                with open(path, 'rb') as f:
                    return convert_pdf_to_images(f.read())
            else:
                return Image.open(path)
        
        raise ValueError(f"Could not process file data: {image_data[:50]}...")
        
    except Exception as e:
        raise ValueError(f"Error processing file: {str(e)}")

# Improved process_image method for VLMServer class
IMPROVED_PROCESS_IMAGE = '''
    def process_image(self, image_data: str) -> Image.Image:
        """Process image from URL, base64, or file path - now with PDF support"""
        try:
            import fitz  # PyMuPDF
            
            # Check if it's a URL
            if image_data.startswith(('http://', 'https://')):
                response = requests.get(image_data, timeout=30)
                response.raise_for_status()
                content = response.content
                
                # Check if it's a PDF
                if content.startswith(b'%PDF'):
                    # Convert first page of PDF to image
                    pdf_document = fitz.open(stream=content, filetype="pdf")
                    page = pdf_document[0]
                    mat = fitz.Matrix(2, 2)  # 2x scaling for better quality
                    pix = page.get_pixmap(matrix=mat)
                    img_data = pix.tobytes("png")
                    pdf_document.close()
                    return Image.open(io.BytesIO(img_data))
                else:
                    return Image.open(io.BytesIO(content))
            
            # Check if it's base64 with data URI
            elif image_data.startswith('data:'):
                # Extract mime type and base64 data
                header, base64_data = image_data.split(',', 1)
                
                # Decode base64
                file_bytes = base64.b64decode(base64_data)
                
                # Check if it's a PDF
                if 'pdf' in header.lower() or file_bytes.startswith(b'%PDF'):
                    # Convert first page of PDF to image
                    pdf_document = fitz.open(stream=file_bytes, filetype="pdf")
                    page = pdf_document[0]
                    mat = fitz.Matrix(2, 2)  # 2x scaling
                    pix = page.get_pixmap(matrix=mat)
                    img_data = pix.tobytes("png")
                    pdf_document.close()
                    return Image.open(io.BytesIO(img_data))
                else:
                    return Image.open(io.BytesIO(file_bytes))
            
            # Try as base64 without prefix
            elif len(image_data) > 100:  # Likely base64
                try:
                    file_bytes = base64.b64decode(image_data)
                    # Check if it's a PDF
                    if file_bytes.startswith(b'%PDF'):
                        pdf_document = fitz.open(stream=file_bytes, filetype="pdf")
                        page = pdf_document[0]
                        mat = fitz.Matrix(2, 2)
                        pix = page.get_pixmap(matrix=mat)
                        img_data = pix.tobytes("png")
                        pdf_document.close()
                        return Image.open(io.BytesIO(img_data))
                    else:
                        return Image.open(io.BytesIO(file_bytes))
                except:
                    pass
                    
            # Try as file path
            path = Path(image_data)
            if path.exists():
                if path.suffix.lower() == '.pdf':
                    pdf_document = fitz.open(path)
                    page = pdf_document[0]
                    mat = fitz.Matrix(2, 2)
                    pix = page.get_pixmap(matrix=mat)
                    img_data = pix.tobytes("png")
                    pdf_document.close()
                    return Image.open(io.BytesIO(img_data))
                else:
                    return Image.open(path)
                
            raise ValueError(f"Could not process file data: {image_data[:50]}...")
            
        except ImportError:
            # If PyMuPDF not installed, provide helpful error
            if 'pdf' in image_data.lower() or (len(image_data) > 4 and image_data.startswith('JVBE')):
                raise ValueError("PDF support requires PyMuPDF. Install with: pip install PyMuPDF")
            raise
        except Exception as e:
            logger.error(f"Error processing image: {str(e)}")
            raise
'''

if __name__ == "__main__":
    print("PDF Upload Fix")
    print("=" * 60)
    print("\nThe issue: JavaScript sends PDF as 'data:application/pdf;base64,...'")
    print("but process_image() only handles 'data:image/...' formats.\n")
    print("Solution: Add PDF-to-image conversion using PyMuPDF\n")
    print("To apply this fix:")
    print("1. Install PyMuPDF: pip install PyMuPDF")
    print("2. Replace the process_image method in vlm_server.py with the improved version above")
    print("\nThe improved method will:")
    print("- Detect PDF files by header or MIME type")
    print("- Convert the first page of PDF to a high-quality PNG image")
    print("- Handle all existing image formats as before")