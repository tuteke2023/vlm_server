#!/bin/bash
# Fix CUDA compatibility for RTX 5060 Ti (sm_120)

echo "🔧 Fixing CUDA Compatibility for RTX 5060 Ti"
echo "=============================================="

echo "Current PyTorch version:"
python3 -c "import torch; print(f'PyTorch: {torch.__version__}')"
python3 -c "import torch; print(f'CUDA Available: {torch.cuda.is_available()}')"

echo -e "\n📦 Installing PyTorch with latest CUDA support..."
echo "This will install PyTorch nightly build that supports sm_120"

# Backup current environment
echo "💾 Backing up current environment..."
pip freeze > requirements_backup.txt

echo -e "\n🚀 Installing PyTorch nightly with CUDA 12.1 support..."
pip install --pre torch torchvision torchaudio --index-url https://download.pytorch.org/whl/nightly/cu121 --break-system-packages

echo -e "\n✅ Installation complete. Testing CUDA compatibility..."
python3 -c "
import torch
print(f'New PyTorch version: {torch.__version__}')
print(f'CUDA Available: {torch.cuda.is_available()}')
if torch.cuda.is_available():
    print(f'GPU: {torch.cuda.get_device_name(0)}')
    print(f'CUDA Capability: {torch.cuda.get_device_capability(0)}')
    try:
        # Test basic CUDA operation
        x = torch.tensor([1.0]).cuda()
        print('✅ CUDA operation successful!')
    except Exception as e:
        print(f'❌ CUDA operation failed: {e}')
else:
    print('❌ CUDA still not available')
"

echo -e "\n🎯 Next steps:"
echo "1. If successful, restart the VLM server: python3 vlm_server.py"
echo "2. Test quantization in the web interface"
echo "3. If failed, restore backup: pip install -r requirements_backup.txt --break-system-packages"