#!/usr/bin/env python3
"""Create a test bank statement image for debugging amount extraction"""

from PIL import Image, ImageDraw, ImageFont
import os

# Create a simple bank statement image
width, height = 800, 600
image = Image.new('RGB', (width, height), 'white')
draw = ImageDraw.Draw(image)

# Try to use a monospace font
try:
    font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf", 14)
    header_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 16)
except:
    font = ImageFont.load_default()
    header_font = font

# Draw header
draw.text((50, 30), "Bank Statement", font=header_font, fill='black')
draw.text((50, 60), "Account: 123456789", font=font, fill='black')
draw.text((50, 80), "Period: 01 Apr 2025 - 30 Jun 2025", font=font, fill='black')

# Draw table headers
y = 120
draw.text((50, y), "Date", font=header_font, fill='black')
draw.text((150, y), "Description", font=header_font, fill='black')
draw.text((450, y), "Debit", font=header_font, fill='black')
draw.text((550, y), "Credit", font=header_font, fill='black')
draw.text((650, y), "Balance", font=header_font, fill='black')

# Draw line
y += 25
draw.line([(50, y), (750, y)], fill='black', width=1)

# Add transactions with full amounts
transactions = [
    ("04-Apr-25", "Direct Credit 400937 DB RESULTS", "", "1,750.00", "1,750.00"),
    ("05-Apr-25", "Transfer to xx5330 CommBank app Loan", "850.00", "", "900.00"),
    ("05-Apr-25", "Transfer to CBA A/c CommBank app", "900.00", "", "0.00"),
    ("22-Apr-25", "Transfer from CommBank app BAS Q125", "", "2,200.00", "2,200.00"),
    ("22-Apr-25", "TT ACCOUNTANCY", "2,200.00", "", "0.00"),
    ("02-May-25", "Direct Credit 400937 DB RESULTS", "", "1,450.50", "1,450.50"),
    ("02-May-25", "Transfer to xx5330 CommBank app Loan", "850.00", "", "600.50"),
    ("02-May-25", "Transfer to CBA A/c CommBank app", "600.50", "", "0.00"),
]

# Draw transactions
for date, desc, debit, credit, balance in transactions:
    y += 30
    draw.text((50, y), date, font=font, fill='black')
    draw.text((150, y), desc[:40], font=font, fill='black')  # Truncate long descriptions
    draw.text((450, y), debit, font=font, fill='black')
    draw.text((550, y), credit, font=font, fill='black')
    draw.text((650, y), balance, font=font, fill='black')

# Add summary section to test filtering
y += 60
draw.line([(50, y), (750, y)], fill='black', width=1)
y += 10
draw.text((50, y), "Transaction Summary", font=header_font, fill='black')
y += 25
draw.text((50, y), "Total Debits: $4,550.50", font=font, fill='black')
y += 20
draw.text((50, y), "Total Credits: $5,400.50", font=font, fill='black')

# Save the image
output_path = "/home/teke/projects/vlm_server/test_bank_statement.png"
image.save(output_path)
print(f"Test bank statement saved to: {output_path}")