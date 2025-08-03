#!/usr/bin/env python3
"""
Multi-page PDF handling strategies for VLM processing
"""

import fitz  # PyMuPDF
from PIL import Image
import io
from typing import List, Union

def concatenate_pdf_pages_vertically(pdf_bytes: bytes, max_height: int = 8000) -> Image.Image:
    """
    Convert all PDF pages to a single vertical image.
    
    Args:
        pdf_bytes: PDF file as bytes
        max_height: Maximum height of concatenated image (to avoid memory issues)
        
    Returns:
        Single PIL Image with all pages concatenated vertically
    """
    pdf_document = fitz.open(stream=pdf_bytes, filetype="pdf")
    images = []
    total_height = 0
    max_width = 0
    
    # First pass: convert pages and calculate dimensions
    for page_num in range(len(pdf_document)):
        page = pdf_document[page_num]
        # 2x scaling for better quality
        mat = fitz.Matrix(2, 2)
        pix = page.get_pixmap(matrix=mat)
        
        # Convert to PIL Image
        img_data = pix.tobytes("png")
        img = Image.open(io.BytesIO(img_data))
        
        images.append(img)
        total_height += img.height
        max_width = max(max_width, img.width)
        
        # Check if we're exceeding height limit
        if total_height > max_height:
            break
    
    pdf_document.close()
    
    # Create concatenated image
    concatenated = Image.new('RGB', (max_width, total_height), 'white')
    
    # Paste all pages vertically
    y_offset = 0
    for img in images:
        # Center images horizontally if needed
        x_offset = (max_width - img.width) // 2
        concatenated.paste(img, (x_offset, y_offset))
        y_offset += img.height
    
    return concatenated

def create_pdf_grid(pdf_bytes: bytes, grid_cols: int = 2) -> Image.Image:
    """
    Convert PDF pages to a grid layout (e.g., 2x2, 2x3).
    Better for preserving aspect ratios and readability.
    
    Args:
        pdf_bytes: PDF file as bytes
        grid_cols: Number of columns in the grid
        
    Returns:
        Single PIL Image with pages arranged in a grid
    """
    pdf_document = fitz.open(stream=pdf_bytes, filetype="pdf")
    images = []
    
    # Convert all pages
    for page_num in range(len(pdf_document)):
        page = pdf_document[page_num]
        # 1.5x scaling (balance between quality and size)
        mat = fitz.Matrix(1.5, 1.5)
        pix = page.get_pixmap(matrix=mat)
        
        img_data = pix.tobytes("png")
        img = Image.open(io.BytesIO(img_data))
        images.append(img)
    
    pdf_document.close()
    
    if not images:
        raise ValueError("No pages found in PDF")
    
    # Calculate grid dimensions
    num_pages = len(images)
    grid_rows = (num_pages + grid_cols - 1) // grid_cols
    
    # Find max dimensions for each cell
    max_width = max(img.width for img in images)
    max_height = max(img.height for img in images)
    
    # Add padding between pages
    padding = 20
    grid_width = grid_cols * max_width + (grid_cols - 1) * padding
    grid_height = grid_rows * max_height + (grid_rows - 1) * padding
    
    # Create grid image
    grid_image = Image.new('RGB', (grid_width, grid_height), 'white')
    
    # Place images in grid
    for idx, img in enumerate(images):
        row = idx // grid_cols
        col = idx % grid_cols
        
        x = col * (max_width + padding) + (max_width - img.width) // 2
        y = row * (max_height + padding) + (max_height - img.height) // 2
        
        grid_image.paste(img, (x, y))
    
    return grid_image

def extract_text_focused_pages(pdf_bytes: bytes, target_keywords: List[str] = None) -> Image.Image:
    """
    For bank statements, extract only pages containing transaction data.
    Skip cover pages, disclaimers, etc.
    
    Args:
        pdf_bytes: PDF file as bytes
        target_keywords: Keywords to identify relevant pages (e.g., ["transaction", "balance", "date"])
        
    Returns:
        Concatenated image of relevant pages only
    """
    if target_keywords is None:
        target_keywords = ["transaction", "balance", "date", "debit", "credit", "withdrawal", "deposit"]
    
    pdf_document = fitz.open(stream=pdf_bytes, filetype="pdf")
    relevant_images = []
    
    for page_num in range(len(pdf_document)):
        page = pdf_document[page_num]
        # Extract text to check relevance
        text = page.get_text().lower()
        
        # Check if page contains relevant keywords
        is_relevant = any(keyword in text for keyword in target_keywords)
        
        if is_relevant:
            # Convert to image
            mat = fitz.Matrix(2, 2)
            pix = page.get_pixmap(matrix=mat)
            img_data = pix.tobytes("png")
            img = Image.open(io.BytesIO(img_data))
            relevant_images.append(img)
    
    pdf_document.close()
    
    if not relevant_images:
        # If no relevant pages found, return first page as fallback
        return convert_first_page_only(pdf_bytes)
    
    # Concatenate relevant pages
    total_height = sum(img.height for img in relevant_images)
    max_width = max(img.width for img in relevant_images)
    
    concatenated = Image.new('RGB', (max_width, total_height), 'white')
    
    y_offset = 0
    for img in relevant_images:
        x_offset = (max_width - img.width) // 2
        concatenated.paste(img, (x_offset, y_offset))
        y_offset += img.height
    
    return concatenated

def convert_first_page_only(pdf_bytes: bytes) -> Image.Image:
    """Current implementation - converts only first page"""
    pdf_document = fitz.open(stream=pdf_bytes, filetype="pdf")
    page = pdf_document[0]
    mat = fitz.Matrix(2, 2)
    pix = page.get_pixmap(matrix=mat)
    img_data = pix.tobytes("png")
    pdf_document.close()
    return Image.open(io.BytesIO(img_data))

# Improved process_image method for multi-page PDF support
IMPROVED_MULTIPAGE_PROCESS_IMAGE = '''
    def process_image(self, image_data: str) -> Image.Image:
        """Process image from URL, base64, or file path - with multi-page PDF support"""
        try:
            import fitz  # PyMuPDF
            
            # Helper function to handle PDF conversion
            def convert_pdf_to_image(pdf_bytes: bytes) -> Image.Image:
                """Convert PDF to image using appropriate strategy"""
                pdf_document = fitz.open(stream=pdf_bytes, filetype="pdf")
                num_pages = len(pdf_document)
                pdf_document.close()
                
                if num_pages == 1:
                    # Single page - simple conversion
                    return convert_first_page_only(pdf_bytes)
                elif num_pages <= 4:
                    # Few pages - use grid layout
                    return create_pdf_grid(pdf_bytes, grid_cols=2)
                else:
                    # Many pages - extract relevant pages only
                    # For bank statements, this is most efficient
                    return extract_text_focused_pages(pdf_bytes)
            
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
            
            # Rest of the implementation remains the same...
'''

if __name__ == "__main__":
    print("Multi-page PDF Handling Strategies")
    print("=" * 60)
    print("\n1. Vertical Concatenation:")
    print("   - Stacks all pages vertically into one tall image")
    print("   - Good for sequential reading (like bank statements)")
    print("   - May create very tall images")
    print("\n2. Grid Layout:")
    print("   - Arranges pages in a 2x2 or 2x3 grid")
    print("   - Better aspect ratio for VLM processing")
    print("   - Good for 2-6 page documents")
    print("\n3. Smart Extraction:")
    print("   - Analyzes page content and extracts only relevant pages")
    print("   - Skips cover pages, legal disclaimers, etc.")
    print("   - Most efficient for long documents")
    print("\n4. Adaptive Strategy (Recommended):")
    print("   - 1 page: Direct conversion")
    print("   - 2-4 pages: Grid layout")
    print("   - 5+ pages: Smart extraction of transaction pages")