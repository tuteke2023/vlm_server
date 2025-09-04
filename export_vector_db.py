#!/usr/bin/env python3
"""Export vector database and transcripts for transfer to another computer"""

import os
import shutil
import tarfile
from datetime import datetime
from pathlib import Path

def create_portable_package():
    """Create a portable package of the vector database and transcripts"""
    
    print("=" * 60)
    print("CREATING PORTABLE VECTOR DATABASE PACKAGE")
    print("=" * 60)
    
    # Define what to include
    components = {
        'vector_db': 'services/audio/transcript_vectors',
        'sqlite_db': 'services/audio/transcripts.db',
        'audio_service': 'services/audio/',
        'batch_tools': [
            'batch_transcribe.py',
            'batch_transcribe_filtered.py', 
            'transcribe_truncated.py',
            'transcribe_single.py'
        ],
        'web_interface': 'services/audio/web_interface/'
    }
    
    # Create export directory
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    export_dir = f"vector_db_export_{timestamp}"
    os.makedirs(export_dir, exist_ok=True)
    
    print(f"\n📁 Creating export in: {export_dir}/")
    
    # 1. Copy vector database
    if os.path.exists(components['vector_db']):
        print("📊 Copying vector database...")
        shutil.copytree(
            components['vector_db'], 
            f"{export_dir}/transcript_vectors",
            dirs_exist_ok=True
        )
        print("   ✅ Vector database copied")
    else:
        print("   ⚠️ Vector database not found")
    
    # 2. Copy SQLite database
    if os.path.exists(components['sqlite_db']):
        print("💾 Copying SQLite database...")
        shutil.copy2(components['sqlite_db'], f"{export_dir}/transcripts.db")
        print("   ✅ SQLite database copied")
    else:
        print("   ⚠️ SQLite database not found")
    
    # 3. Copy essential Python files
    print("🐍 Copying essential Python files...")
    os.makedirs(f"{export_dir}/audio_service", exist_ok=True)
    
    # Copy core service files
    for file in ['transcription_server.py', 'vector_storage.py', 
                 'transcript_storage.py', 'llm_qa_system.py']:
        src = f"services/audio/{file}"
        if os.path.exists(src):
            shutil.copy2(src, f"{export_dir}/audio_service/{file}")
            print(f"   ✅ {file}")
    
    # Copy batch processing tools
    for tool in components['batch_tools']:
        if os.path.exists(tool):
            shutil.copy2(tool, f"{export_dir}/{tool}")
            print(f"   ✅ {tool}")
    
    # 4. Copy web interface
    if os.path.exists(components['web_interface']):
        print("🌐 Copying web interface...")
        shutil.copytree(
            components['web_interface'],
            f"{export_dir}/web_interface",
            dirs_exist_ok=True
        )
        print("   ✅ Web interface copied")
    
    # 5. Create requirements file
    print("📋 Creating requirements file...")
    requirements = """# Audio Service Requirements
fastapi==0.104.1
uvicorn[standard]==0.24.0
openai-whisper==20230918
python-multipart==0.0.6
chromadb==0.4.20
sentence-transformers==2.2.2
sqlalchemy==2.0.23

# Optional for enhanced Q&A
openai==1.3.8  # If using OpenAI API
transformers==4.36.0  # If using local LLM
"""
    
    with open(f"{export_dir}/requirements.txt", 'w') as f:
        f.write(requirements)
    print("   ✅ requirements.txt created")
    
    # 6. Create setup script
    print("🔧 Creating setup script...")
    setup_script = """#!/bin/bash
# Setup script for vector database on new computer

echo "Setting up Vector Database and Audio Service..."

# Create virtual environment
python3 -m venv audio-env
source audio-env/bin/activate

# Install requirements
pip install --upgrade pip
pip install -r requirements.txt

echo "✅ Setup complete!"
echo ""
echo "To start the service:"
echo "1. source audio-env/bin/activate"
echo "2. cd audio_service"
echo "3. python transcription_server.py"
echo ""
echo "Access at:"
echo "- Search UI: http://localhost:8002/search.html"
echo "- Q&A UI: http://localhost:8002/qa_interface.html"
"""
    
    with open(f"{export_dir}/setup.sh", 'w') as f:
        f.write(setup_script)
    os.chmod(f"{export_dir}/setup.sh", 0o755)
    print("   ✅ setup.sh created")
    
    # 7. Create README
    print("📝 Creating README...")
    readme = f"""# Exported Vector Database Package

Created: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Contents:
- Vector database (ChromaDB) with all transcript embeddings
- SQLite database with transcript metadata
- Audio transcription service
- Web search interfaces
- Batch processing tools

## Quick Setup on New Computer:

### Option 1: Automatic Setup (Linux/Mac)
```bash
./setup.sh
```

### Option 2: Manual Setup
```bash
# Create virtual environment
python3 -m venv audio-env
source audio-env/bin/activate  # On Windows: audio-env\\Scripts\\activate

# Install dependencies
pip install -r requirements.txt

# Start the service
cd audio_service
python transcription_server.py
```

## Access Points:
- Search UI: http://localhost:8002/search.html
- Q&A Interface: http://localhost:8002/qa_interface.html
- API: http://localhost:8001

## Database Stats:
- Check current stats with: curl http://localhost:8001/vector/stats

## For Better Q&A Performance:
If the new computer has more VRAM (>8GB), you can run the VLM server alongside:
1. Install the main VLM server from the full repository
2. Configure llm_qa_system.py to point to the VLM endpoint
"""
    
    with open(f"{export_dir}/README.md", 'w') as f:
        f.write(readme)
    print("   ✅ README.md created")
    
    # 8. Create compressed archive
    print("\n📦 Creating compressed archive...")
    archive_name = f"{export_dir}.tar.gz"
    
    with tarfile.open(archive_name, "w:gz") as tar:
        tar.add(export_dir, arcname=os.path.basename(export_dir))
    
    archive_size = os.path.getsize(archive_name) / (1024 * 1024)
    print(f"   ✅ Archive created: {archive_name} ({archive_size:.1f} MB)")
    
    # Get database statistics
    print("\n📊 Database Statistics:")
    try:
        import requests
        response = requests.get("http://localhost:8001/vector/stats")
        if response.status_code == 200:
            stats = response.json()
            print(f"   - Transcripts: {stats.get('total_transcripts', 'Unknown')}")
            print(f"   - Chunks: {stats.get('total_chunks', 'Unknown')}")
    except:
        pass
    
    print("\n" + "=" * 60)
    print("✅ EXPORT COMPLETE!")
    print("=" * 60)
    print(f"\n📦 Package ready: {archive_name}")
    print(f"📏 Size: {archive_size:.1f} MB")
    print("\nTransfer this file to your other computer and extract with:")
    print(f"   tar -xzf {archive_name}")
    print("\nThen run ./setup.sh in the extracted directory")
    
    return archive_name

if __name__ == "__main__":
    create_portable_package()