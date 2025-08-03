#!/usr/bin/env python3
"""
Improved PDF processor that handles multi-page bank statements better
"""

import fitz  # PyMuPDF
from PIL import Image, ImageDraw, ImageFont
import io
import base64

def create_bank_statement_image(pdf_bytes: bytes) -> Image.Image:
    """
    Create an optimized image for bank statement processing
    Focuses on transaction pages only and ensures all content is visible
    """
    pdf_document = fitz.open(stream=pdf_bytes, filetype="pdf")
    num_pages = len(pdf_document)
    
    # First, identify which pages have transactions
    transaction_pages = []
    
    for page_num in range(num_pages):
        page = pdf_document[page_num]
        text = page.get_text().lower()
        
        # Check if this page has transaction data (not just headers/footers)
        has_transactions = any([
            "withdrawals" in text and "deposits" in text and "balance" in text,
            "debit" in text or "credit" in text,
            any(month in text for month in ['jan', 'feb', 'mar', 'apr', 'may', 'jun', 
                                           'jul', 'aug', 'sep', 'oct', 'nov', 'dec'])
        ])
        
        # Skip first page if it's just a cover page
        is_cover_page = page_num == 0 and "transaction details" not in text
        
        if has_transactions and not is_cover_page:
            transaction_pages.append(page_num)
    
    if not transaction_pages:
        # Fallback: use all pages except blank ones
        transaction_pages = [i for i in range(num_pages) if len(pdf_document[i].get_text().strip()) > 100]
    
    print(f"Processing pages with transactions: {[p+1 for p in transaction_pages]}")
    
    # Convert transaction pages to images with optimal settings
    images = []
    for page_num in transaction_pages:
        page = pdf_document[page_num]
        
        # Use high quality but not excessive resolution
        # 1.5x is usually enough for text clarity without making image too large
        mat = fitz.Matrix(1.5, 1.5)
        pix = page.get_pixmap(matrix=mat)
        img_data = pix.tobytes("png")
        img = Image.open(io.BytesIO(img_data))
        
        # Crop whitespace if significant
        img = crop_whitespace(img)
        images.append(img)
    
    pdf_document.close()
    
    if len(images) == 1:
        return images[0]
    
    # For multiple pages, create a single image with clear page boundaries
    # Calculate total dimensions
    total_height = sum(img.height for img in images)
    max_width = max(img.width for img in images)
    
    # Add small padding between pages
    page_gap = 30
    total_height += page_gap * (len(images) - 1)
    
    # Add header space for instructions
    header_height = 100
    total_height += header_height
    
    # Create combined image
    combined = Image.new('RGB', (max_width, total_height), 'white')
    draw = ImageDraw.Draw(combined)
    
    # Add instruction header
    instruction_text = f"BANK STATEMENT - {len(images)} PAGES - EXTRACT ALL TRANSACTIONS"
    try:
        # Try to use a better font if available
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 24)
    except:
        font = ImageFont.load_default()
    
    text_bbox = draw.textbbox((0, 0), instruction_text, font=font)
    text_width = text_bbox[2] - text_bbox[0]
    text_x = (max_width - text_width) // 2
    draw.text((text_x, 30), instruction_text, fill='red', font=font)
    
    # Add pages with separators
    y_offset = header_height
    for idx, img in enumerate(images):
        # Center image horizontally
        x_offset = (max_width - img.width) // 2
        combined.paste(img, (x_offset, y_offset))
        
        # Add page number
        page_text = f"PAGE {transaction_pages[idx] + 1}"
        draw.text((10, y_offset + 10), page_text, fill='blue', font=font)
        
        y_offset += img.height
        
        # Add separator between pages
        if idx < len(images) - 1:
            separator_y = y_offset + page_gap // 2
            draw.line([(50, separator_y), (max_width - 50, separator_y)], 
                     fill='red', width=3)
            draw.text((max_width//2 - 100, separator_y - 15), 
                     "--- CONTINUE TO NEXT PAGE ---", fill='red')
            y_offset += page_gap
    
    # Add footer reminder
    draw.text((10, total_height - 30), 
             "IMPORTANT: Include ALL transactions from ALL pages above", 
             fill='red', font=font)
    
    return combined

def crop_whitespace(img: Image.Image, margin: int = 20) -> Image.Image:
    """Crop excessive whitespace from image"""
    # Convert to grayscale for analysis
    gray = img.convert('L')
    
    # Get bounding box of non-white pixels
    bbox = gray.getbbox()
    
    if bbox:
        # Add small margin
        left = max(0, bbox[0] - margin)
        top = max(0, bbox[1] - margin)
        right = min(img.width, bbox[2] + margin)
        bottom = min(img.height, bbox[3] + margin)
        
        return img.crop((left, top, right, bottom))
    
    return img

# Improved process_image method for VLMServer
IMPROVED_PROCESS_IMAGE = '''
def process_image(self, image_data: str) -> Image.Image:
    """Process image from URL, base64, or file path - with improved bank statement handling"""
    try:
        import fitz  # PyMuPDF
        
        def convert_pdf_to_image(pdf_bytes: bytes) -> Image.Image:
            """Convert PDF to image using improved bank statement handling"""
            from improved_pdf_processor import create_bank_statement_image
            return create_bank_statement_image(pdf_bytes)
        
        # Rest of the implementation remains the same...
        # Check if it's a URL
        if image_data.startswith(('http://', 'https://')):
            response = requests.get(image_data, timeout=30)
            response.raise_for_status()
            content = response.content
            
            if content.startswith(b'%PDF'):
                return convert_pdf_to_image(content)
            else:
                return Image.open(io.BytesIO(content))
        
        # ... rest of the method
'''

if __name__ == "__main__":
    # Test with the bank statement
    import os
    
    pdf_path = "/home/teke/projects/vlm_server/test_data/SMSF Bank Statements 82855cf1-8bb3-4a0a-8ed5-f7bbe12893c1.pdf"
    
    if os.path.exists(pdf_path):
        with open(pdf_path, 'rb') as f:
            pdf_bytes = f.read()
        
        # Create optimized image
        result_image = create_bank_statement_image(pdf_bytes)
        result_image.save("test_optimized_bank_statement.png")
        
        print(f"\nOptimized image saved: test_optimized_bank_statement.png")
        print(f"Size: {result_image.width}x{result_image.height} pixels")