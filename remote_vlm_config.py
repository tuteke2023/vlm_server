#!/usr/bin/env python3
"""Configuration for using remote VLM server with local vector database"""

# Option 1: Run VLM on another computer with more VRAM
# ====================================================

# On the computer with more VRAM (e.g., 16GB+ GPU):
VLM_SETUP = """
# 1. Clone the VLM server repository
git clone https://github.com/tuteke2023/vlm_server.git
cd vlm_server

# 2. Setup environment
python3 -m venv ~/pytorch-env
source ~/pytorch-env/bin/activate
pip install -r requirements.txt

# 3. Start VLM server (will use port 8000)
python vlm_server.py --host 0.0.0.0  # Allow external connections
"""

# On this computer (with vector database):
VECTOR_DB_CONFIG = """
# Edit services/audio/llm_qa_system.py
# Change the VLM URL to point to the remote computer:

vlm_url = "http://192.168.1.100:8000"  # Replace with actual IP
"""

# Option 2: Use cloud-based LLM (OpenAI, Anthropic, etc.)
# ========================================================

CLOUD_LLM_CONFIG = """
# 1. Install OpenAI client
pip install openai

# 2. Set API key
export OPENAI_API_KEY="your-key-here"

# 3. Modify llm_qa_system.py to use OpenAI
"""

# Option 3: Hybrid approach - Local embeddings, remote LLM
# =========================================================

class HybridConfig:
    """Configuration for hybrid deployment"""
    
    # Local services (this computer)
    LOCAL_SERVICES = {
        'vector_db': 'http://localhost:8001',  # Audio service with vector DB
        'embeddings': 'local',  # Uses sentence-transformers locally
    }
    
    # Remote services (other computer or cloud)
    REMOTE_SERVICES = {
        'vlm': 'http://192.168.1.100:8000',  # Computer with more VRAM
        'backup_llm': 'openai',  # Fallback to OpenAI if VLM unavailable
    }
    
    @staticmethod
    def get_optimal_setup(vram_available):
        """Recommend setup based on available VRAM"""
        if vram_available >= 16:
            return "Run everything locally - you have enough VRAM"
        elif vram_available >= 8:
            return "Run embeddings + vector DB locally, VLM on remote"
        else:
            return "Run vector DB locally, both embeddings and VLM remote"

# Deployment architectures
ARCHITECTURES = {
    "single_machine": {
        "description": "Everything on one powerful machine",
        "requirements": "16GB+ VRAM",
        "pros": ["Fast", "No network latency", "Simple"],
        "cons": ["Needs powerful hardware"]
    },
    
    "distributed": {
        "description": "Vector DB on one machine, VLM on another",
        "requirements": "8GB VRAM for DB, 16GB+ for VLM",
        "pros": ["Flexible", "Can use existing hardware", "Scalable"],
        "cons": ["Network latency", "More complex"]
    },
    
    "cloud_hybrid": {
        "description": "Local vector DB, cloud LLM (OpenAI/Anthropic)",
        "requirements": "Any computer, API credits",
        "pros": ["No GPU needed for LLM", "Always available", "Latest models"],
        "cons": ["API costs", "Internet required", "Privacy concerns"]
    }
}

def test_remote_connection(remote_url):
    """Test connection to remote VLM"""
    import requests
    
    try:
        response = requests.get(f"{remote_url}/health", timeout=5)
        if response.status_code == 200:
            print(f"✅ Connected to remote VLM at {remote_url}")
            return True
    except:
        pass
    
    print(f"❌ Cannot connect to {remote_url}")
    return False

def configure_for_remote_vlm(remote_ip, remote_port=8000):
    """Configure the system to use a remote VLM"""
    
    config = f"""
# Remote VLM Configuration
# Add this to your services/audio/llm_qa_system.py

class TranscriptQASystem:
    def __init__(self, 
                 vector_storage = None,
                 vlm_url: str = "http://{remote_ip}:{remote_port}",  # Remote VLM
                 vlm_model: str = "qwen2.5-vl-3b"):
        # ... rest of initialization
"""
    
    print("Configuration for remote VLM:")
    print(config)
    
    # Test the connection
    if test_remote_connection(f"http://{remote_ip}:{remote_port}"):
        print("\n✅ Remote VLM is accessible!")
    else:
        print("\n⚠️ Make sure to:")
        print(f"1. Start VLM server on {remote_ip}")
        print("2. Use --host 0.0.0.0 flag")
        print("3. Check firewall allows port", remote_port)

if __name__ == "__main__":
    import sys
    
    print("=" * 60)
    print("REMOTE VLM CONFIGURATION HELPER")
    print("=" * 60)
    
    if len(sys.argv) > 1:
        remote_ip = sys.argv[1]
        print(f"\nConfiguring for remote VLM at: {remote_ip}")
        configure_for_remote_vlm(remote_ip)
    else:
        print("\nUsage: python remote_vlm_config.py <remote-ip>")
        print("Example: python remote_vlm_config.py 192.168.1.100")
        
        print("\n" + "=" * 60)
        print("DEPLOYMENT OPTIONS:")
        print("=" * 60)
        
        for name, arch in ARCHITECTURES.items():
            print(f"\n{name.upper()}:")
            print(f"  {arch['description']}")
            print(f"  Requirements: {arch['requirements']}")
            print(f"  Pros: {', '.join(arch['pros'])}")
            print(f"  Cons: {', '.join(arch['cons'])}")