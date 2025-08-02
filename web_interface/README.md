# VLM Server Web Interface

A modern, responsive web interface for the VLM Server that provides document intelligence capabilities through an intuitive user interface.

## Features

### 🏦 **Bank Transaction Extraction**
- Upload bank statements (PDF, images)
- Extract transaction dates, amounts, descriptions
- Detect merchants and categorize transactions
- Generate structured transaction tables
- Calculate totals and balances

### 📄 **Document Summarization**
- AI-powered document summaries
- Multiple summary styles (executive, technical, simple, bullet points)
- Adjustable summary length
- Key point extraction
- Named entity recognition

### 🖼️ **Image Analysis**
- Detailed image descriptions
- Object detection and identification
- Text extraction (OCR)
- Color analysis
- Face detection
- Landmark recognition

### 📝 **Text Extraction (OCR)**
- Extract text from images and scanned documents
- Preserve formatting and structure
- Table detection and formatting
- Header extraction
- Text cleaning and formatting

### ❓ **Custom Queries**
- Ask specific questions about uploaded documents
- Natural language queries
- Context-aware responses
- Example query templates

## Quick Start

### Prerequisites

1. **VLM Server Running**: Make sure your VLM server is running on `http://localhost:8000`
2. **Python 3.6+**: For the development web server

### Installation

1. **Navigate to the web interface directory**:
   ```bash
   cd web_interface
   ```

2. **Start the web server**:
   ```bash
   python server.py
   ```

3. **Open in browser**:
   - The interface will automatically open at `http://localhost:8080`
   - Or manually navigate to `http://localhost:8080`

## Usage Guide

### 1. **Server Status**
- **Green dot**: VLM server is online and ready
- **Orange dot**: Connecting to server
- **Red dot**: Server offline or error
- **VRAM Usage**: Real-time GPU memory monitoring

### 2. **File Upload**
- **Drag & Drop**: Drag files directly onto upload areas
- **Click to Browse**: Click upload areas to select files
- **Supported Formats**: PDF, PNG, JPG, JPEG, GIF, TXT
- **File Size Limit**: 50MB per file
- **Multiple Files**: Upload multiple files for batch processing

### 3. **Processing Options**

#### Bank Transactions
- ✅ **Transaction Dates**: Extract all transaction dates
- ✅ **Amounts**: Extract debit/credit amounts
- ✅ **Descriptions**: Extract transaction descriptions
- ✅ **Running Balances**: Extract account balances
- ☐ **Categorize Transactions**: Auto-categorize by type
- ☐ **Detect Merchants**: Identify merchant names

#### Document Summary
- **Length**: Brief (1-2 sentences), Medium (1 paragraph), Detailed (multiple paragraphs)
- **Style**: Executive Summary, Technical Summary, Simple Language, Bullet Points
- **Options**: Extract key points, Identify named entities

#### Image Analysis
- **Description**: Detailed image description
- **Objects**: Identify objects in the image
- **Text (OCR)**: Extract any text from the image
- **Colors**: Analyze color palette
- **Faces**: Detect faces (if any)
- **Landmarks**: Recognize famous landmarks

#### Text Extraction
- **Formatting**: Preserve original document formatting
- **Tables**: Detect and format tables properly
- **Headers**: Extract and highlight headers
- **Clean Text**: Auto-format and clean extracted text

#### Custom Queries
- **Free-form Questions**: Ask anything about uploaded documents
- **Example Templates**: Pre-built query examples
- **Context-aware**: Understands document context

### 4. **Results & Export**
- **Copy**: Copy results to clipboard
- **Download**: Save results as text file
- **Share**: Export results for sharing
- **Processing Info**: View processing time, tokens used, model info

### 5. **Quick Actions**
- **Clear VRAM**: Manually clear GPU memory
- **Export Results**: Quick export of current results

## Example Use Cases

### 📊 **Financial Analysis**
```
Upload: Bank statement PDF
Tool: Bank Transactions
Options: ✅ All extraction options
Result: Structured table of all transactions with categories and totals
```

### 📋 **Document Review**
```
Upload: Contract PDF
Tool: Document Summary
Style: Executive Summary
Length: Medium
Result: Key terms, important dates, and summary of obligations
```

### 🔍 **Receipt Processing**
```
Upload: Receipt images
Tool: Custom Query
Query: "Extract merchant name, date, total amount, and itemized purchases"
Result: Structured receipt data
```

### 🖥️ **Image Understanding**
```
Upload: Screenshot or diagram
Tool: Image Analysis
Options: ✅ Description, ✅ Text extraction, ✅ Objects
Result: Complete analysis of visual content
```

## API Integration

The web interface communicates with the VLM server through REST API calls:

- **Health Check**: `GET /health`
- **VRAM Status**: `GET /vram_status`
- **Text Generation**: `POST /api/v1/generate`
- **VRAM Clear**: `POST /clear_vram`

## Customization

### Adding New Tools

1. **Add HTML panel** in `index.html`:
   ```html
   <div class="tool-panel" id="my-new-tool">
       <!-- Tool content -->
   </div>
   ```

2. **Add navigation item**:
   ```html
   <li class="menu-item" data-tool="my-new-tool">
       <i class="fas fa-icon"></i>
       <span>My New Tool</span>
   </li>
   ```

3. **Add JavaScript logic** in `app.js`:
   ```javascript
   generateMyNewToolPrompt() {
       return "Custom prompt for my new tool";
   }
   ```

### Styling

- **CSS Framework**: Custom CSS with modern design
- **Responsive**: Mobile and tablet friendly
- **Themes**: Easy to customize colors and layout
- **Icons**: Font Awesome icons included

## Architecture

```
web_interface/
├── index.html          # Main HTML structure
├── static/
│   ├── css/
│   │   └── style.css   # Styles and responsive design
│   └── js/
│       └── app.js      # Application logic and API calls
├── server.py           # Development web server
└── README.md           # Documentation
```

## Browser Support

- ✅ **Chrome/Chromium** 80+
- ✅ **Firefox** 75+
- ✅ **Safari** 13+
- ✅ **Edge** 80+

## Troubleshooting

### Server Connection Issues
1. Verify VLM server is running: `curl http://localhost:8000/health`
2. Check server logs for errors
3. Ensure no firewall blocking ports 8000 or 8080

### File Upload Problems
1. Check file size (must be < 50MB)
2. Verify file format is supported
3. Try different browser if drag & drop fails

### Processing Errors
1. Check VLM server logs
2. Verify GPU memory availability
3. Try smaller files or simpler queries

### Performance Issues
1. Use GPU acceleration for faster processing
2. Clear VRAM if memory usage is high
3. Process files individually for large documents

## Development

### Local Development
```bash
# Start VLM server
source ~/pytorch-env/bin/activate
python vlm_server.py

# Start web interface (separate terminal)
cd web_interface
python server.py
```

### Production Deployment
For production, use a proper web server like Nginx or Apache to serve static files, and ensure HTTPS is enabled.

## Contributing

1. **Fork the repository**
2. **Create feature branch**: `git checkout -b feature/my-feature`
3. **Make changes** to HTML, CSS, or JavaScript
4. **Test thoroughly** with different file types
5. **Submit pull request**

## License

This web interface is part of the VLM Server project and follows the same license terms.

## Support

- **Issues**: Report bugs and feature requests on GitHub
- **Documentation**: See main VLM Server documentation
- **Examples**: Check the example use cases above

---

**Built with ❤️ for the VLM Server community**