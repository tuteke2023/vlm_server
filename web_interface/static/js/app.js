/**
 * VLM Server Web Interface
 * Main application logic for the document intelligence platform
 */

class VLMApp {
    constructor() {
        this.serverUrl = 'http://localhost:8000';
        this.currentTool = 'bank-transactions';
        this.uploadedFiles = new Map();
        this.isProcessing = false;
        
        this.currentQuantization = 'none';
        this.init();
    }
    
    init() {
        this.setupEventListeners();
        this.checkServerStatus();
        this.updateVramStatus();
        this.updateDetailedVramStatus();
        this.loadAvailableModels();
        
        // Update server status every 30 seconds
        setInterval(() => {
            this.checkServerStatus();
            this.updateVramStatus();
            this.updateDetailedVramStatus();
        }, 30000);
    }
    
    setupEventListeners() {
        // Tool navigation
        document.querySelectorAll('.menu-item').forEach(item => {
            item.addEventListener('click', (e) => {
                const tool = e.currentTarget.dataset.tool;
                this.switchTool(tool);
            });
        });
        
        // Upload areas
        this.setupUploadHandlers();
        
        // Process button
        document.getElementById('processBtn').addEventListener('click', () => {
            this.processFiles();
        });
        
        // Quick actions
        document.getElementById('clearVramBtn').addEventListener('click', () => {
            this.clearVram();
        });
        
        document.getElementById('exportResultsBtn').addEventListener('click', () => {
            this.exportResults();
        });
        
        // Model settings
        document.getElementById('reloadModelBtn').addEventListener('click', () => {
            this.reloadModel();
        });
        
        // Quantization is disabled
        // document.getElementById('quantizationSelect').addEventListener('change', (e) => {
        //     this.updateQuantizationInfo(e.target.value);
        // });
        
        document.getElementById('modelSelect').addEventListener('change', (e) => {
            this.updateModelInfo(e.target.value);
        });
        
        // Result actions
        document.getElementById('copyResultBtn').addEventListener('click', () => {
            this.copyResults();
        });
        
        document.getElementById('downloadResultBtn').addEventListener('click', () => {
            this.downloadResults();
        });
        
        // Example query tags
        document.querySelectorAll('.example-tag').forEach(tag => {
            tag.addEventListener('click', (e) => {
                const query = e.target.dataset.query;
                document.getElementById('customQuery').value = query;
            });
        });
    }
    
    setupUploadHandlers() {
        const uploadAreas = [
            'bankUploadArea', 'docUploadArea', 'imageUploadArea', 
            'textUploadArea', 'customUploadArea'
        ];
        
        const fileInputs = [
            'bankFileInput', 'docFileInput', 'imageFileInput',
            'textFileInput', 'customFileInput'
        ];
        
        uploadAreas.forEach((areaId, index) => {
            const area = document.getElementById(areaId);
            const input = document.getElementById(fileInputs[index]);
            
            // Click to browse
            area.addEventListener('click', () => input.click());
            
            // Drag and drop
            area.addEventListener('dragover', (e) => {
                e.preventDefault();
                area.classList.add('dragover');
            });
            
            area.addEventListener('dragleave', () => {
                area.classList.remove('dragover');
            });
            
            area.addEventListener('drop', (e) => {
                e.preventDefault();
                area.classList.remove('dragover');
                this.handleFiles(e.dataTransfer.files, areaId);
            });
            
            // File input change
            input.addEventListener('change', (e) => {
                this.handleFiles(e.target.files, areaId);
            });
        });
    }
    
    switchTool(tool) {
        // Update navigation
        document.querySelectorAll('.menu-item').forEach(item => {
            item.classList.remove('active');
        });
        document.querySelector(`[data-tool="${tool}"]`).classList.add('active');
        
        // Update content
        document.querySelectorAll('.tool-panel').forEach(panel => {
            panel.classList.remove('active');
        });
        document.getElementById(tool).classList.add('active');
        
        this.currentTool = tool;
        this.clearFiles();
        this.hideResults();
    }
    
    async checkServerStatus() {
        try {
            const response = await fetch(`${this.serverUrl}/health`);
            const data = await response.json();
            
            const statusElement = document.getElementById('serverStatus');
            const statusDot = statusElement.querySelector('.status-dot');
            const statusText = statusElement.querySelector('.status-text');
            
            if (data.status === 'healthy') {
                statusDot.className = 'status-dot online';
                statusText.textContent = `Online (${data.device})`;
            } else {
                statusDot.className = 'status-dot offline';
                statusText.textContent = 'Server Error';
            }
        } catch (error) {
            const statusElement = document.getElementById('serverStatus');
            const statusDot = statusElement.querySelector('.status-dot');
            const statusText = statusElement.querySelector('.status-text');
            
            statusDot.className = 'status-dot offline';
            statusText.textContent = 'Offline';
        }
    }
    
    async updateVramStatus() {
        try {
            const response = await fetch(`${this.serverUrl}/vram_status`);
            const data = await response.json();
            
            const vramElement = document.getElementById('vramUsage');
            const usageText = `${data.usage_percentage.toFixed(1)}% (${data.allocated_gb.toFixed(1)}GB/${data.total_gb.toFixed(1)}GB)`;
            vramElement.querySelector('span').textContent = `VRAM: ${usageText}`;
        } catch (error) {
            console.error('Failed to update VRAM status:', error);
        }
    }
    
    async updateDetailedVramStatus() {
        try {
            const response = await fetch(`${this.serverUrl}/vram_status`);
            const data = await response.json();
            
            // Update VRAM bar
            const vramBar = document.getElementById('vramBar');
            const vramText = document.getElementById('vramText');
            const vramDetails = document.getElementById('vramDetails');
            
            vramBar.style.width = `${data.usage_percentage}%`;
            vramText.textContent = `${data.usage_percentage.toFixed(1)}%`;
            vramDetails.textContent = `${data.allocated_gb.toFixed(1)}GB / ${data.total_gb.toFixed(1)}GB allocated`;
            
            // Update color based on usage
            vramBar.className = 'vram-fill';
            if (data.usage_percentage >= 90) {
                vramBar.classList.add('danger');
            } else if (data.usage_percentage >= 75) {
                vramBar.classList.add('warning');
            }
            
        } catch (error) {
            console.error('Failed to update detailed VRAM status:', error);
            const vramDetails = document.getElementById('vramDetails');
            vramDetails.textContent = 'Failed to load VRAM status';
        }
    }
    
    // Quantization options removed - functionality disabled
    
    async loadAvailableModels() {
        try {
            const response = await fetch(`${this.serverUrl}/available_models`);
            const models = await response.json();
            
            const select = document.getElementById('modelSelect');
            select.innerHTML = '';
            
            models.forEach(model => {
                const option = document.createElement('option');
                option.value = model.model_id;
                option.textContent = `${model.size} - ${model.description} (~${model.vram_gb}GB VRAM)`;
                if (model.is_current) {
                    option.selected = true;
                    this.updateModelInfo(model.model_id, model);
                    // Update the results section model display
                    const currentModelDisplay = document.getElementById('currentModelDisplay');
                    if (currentModelDisplay) {
                        currentModelDisplay.textContent = model.name;
                    }
                }
                select.appendChild(option);
            });
            
        } catch (error) {
            console.error('Failed to load available models:', error);
        }
    }
    
    updateModelInfo(modelId, modelData = null) {
        const info = document.getElementById('modelInfo');
        
        if (modelData) {
            info.innerHTML = `<small>Current: ${modelData.size} (~${modelData.vram_gb}GB VRAM)</small>`;
        } else {
            // Find model info from select options
            const select = document.getElementById('modelSelect');
            const selectedOption = select.querySelector(`option[value="${modelId}"]`);
            if (selectedOption) {
                info.innerHTML = `<small>Selected: ${selectedOption.textContent}</small>`;
            }
        }
    }
    
    // Quantization info removed - functionality disabled
    
    async reloadModel() {
        const modelName = document.getElementById('modelSelect').value;
        const reloadBtn = document.getElementById('reloadModelBtn');
        
        try {
            reloadBtn.disabled = true;
            reloadBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Reloading...';
            
            this.showToast('Reloading model with new settings...', 'info');
            
            const response = await fetch(`${this.serverUrl}/reload_model`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    model_name: modelName
                })
            });
            
            if (response.ok) {
                const result = await response.json();
                this.showToast(`Model switched successfully to ${result.current_model.split('/').pop()}`, 'success');
                
                // Update current model display
                const currentModelDisplay = document.getElementById('currentModelDisplay');
                if (currentModelDisplay) {
                    currentModelDisplay.textContent = result.current_model.split('/').pop();
                }
                
                // Update VRAM status after reload
                setTimeout(() => {
                    this.updateVramStatus();
                    this.updateDetailedVramStatus();
                    this.loadAvailableModels(); // Refresh model selection
                }, 2000);
            } else {
                const error = await response.json();
                this.showToast(`Failed to reload model: ${error.detail}`, 'error');
            }
            
        } catch (error) {
            this.showToast(`Error reloading model: ${error.message}`, 'error');
        } finally {
            reloadBtn.disabled = false;
            reloadBtn.innerHTML = '<i class="fas fa-sync-alt"></i> Switch Model';
        }
    }
    
    async predictVramUsage(inputTokens, outputTokens) {
        try {
            const response = await fetch(`${this.serverUrl}/vram_prediction?input_tokens=${inputTokens}&output_tokens=${outputTokens}`);
            return await response.json();
        } catch (error) {
            console.error('Failed to predict VRAM usage:', error);
            return null;
        }
    }
    
    handleFiles(files, uploadAreaId) {
        const fileArray = Array.from(files);
        
        fileArray.forEach(file => {
            if (this.validateFile(file)) {
                this.uploadedFiles.set(file.name, {
                    file: file,
                    uploadArea: uploadAreaId
                });
            }
        });
        
        this.displayFiles();
        this.updateProcessButton();
    }
    
    validateFile(file) {
        const maxSize = 50 * 1024 * 1024; // 50MB
        const allowedTypes = [
            'application/pdf',
            'image/png', 'image/jpeg', 'image/jpg', 'image/gif',
            'text/plain'
        ];
        
        if (file.size > maxSize) {
            this.showToast('File too large. Maximum size is 50MB.', 'error');
            return false;
        }
        
        if (!allowedTypes.includes(file.type)) {
            this.showToast('Unsupported file type.', 'error');
            return false;
        }
        
        return true;
    }
    
    displayFiles() {
        const uploadArea = document.querySelector(`#${this.currentTool} .upload-area`);
        let previewContainer = uploadArea.parentNode.querySelector('.file-preview');
        
        if (!previewContainer) {
            previewContainer = document.createElement('div');
            previewContainer.className = 'file-preview';
            uploadArea.parentNode.insertBefore(previewContainer, uploadArea.nextSibling);
        }
        
        previewContainer.innerHTML = '';
        
        this.uploadedFiles.forEach((fileData, fileName) => {
            const fileItem = document.createElement('div');
            fileItem.className = 'file-item';
            
            const fileIcon = this.getFileIcon(fileData.file.type);
            const fileSize = this.formatFileSize(fileData.file.size);
            
            fileItem.innerHTML = `
                <div class="file-icon">
                    <i class="${fileIcon}"></i>
                </div>
                <div class="file-info">
                    <div class="file-name">${fileName}</div>
                    <div class="file-size">${fileSize}</div>
                </div>
                <button class="file-remove" onclick="app.removeFile('${fileName}')">
                    <i class="fas fa-times"></i>
                </button>
            `;
            
            previewContainer.appendChild(fileItem);
        });
    }
    
    getFileIcon(fileType) {
        if (fileType.includes('pdf')) return 'fas fa-file-pdf';
        if (fileType.includes('image')) return 'fas fa-file-image';
        if (fileType.includes('text')) return 'fas fa-file-alt';
        return 'fas fa-file';
    }
    
    formatFileSize(bytes) {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }
    
    removeFile(fileName) {
        this.uploadedFiles.delete(fileName);
        this.displayFiles();
        this.updateProcessButton();
    }
    
    updateProcessButton() {
        const processBtn = document.getElementById('processBtn');
        const hasFiles = this.uploadedFiles.size > 0;
        const hasQuery = this.currentTool === 'custom-query' && 
                        document.getElementById('customQuery').value.trim() !== '';
        
        if (this.currentTool === 'custom-query') {
            processBtn.disabled = !hasFiles || !hasQuery;
        } else {
            processBtn.disabled = !hasFiles;
        }
    }
    
    async processFiles() {
        if (this.isProcessing || this.uploadedFiles.size === 0) return;
        
        // VRAM safety check if enabled
        if (document.getElementById('enableSafetyCheck').checked) {
            const maxTokens = this.getMaxTokens();
            const prediction = await this.predictVramUsage(512, maxTokens);
            
            if (prediction && !prediction.is_safe) {
                const message = `VRAM safety check failed. Predicted usage: ${prediction.predicted_percentage.toFixed(1)}% (limit: 90%). Try switching to the 3B model for lower VRAM usage.`;
                this.showToast(message, 'warning');
                return;
            }
        }
        
        this.isProcessing = true;
        this.showProgress();
        
        try {
            const results = [];
            let fileIndex = 0;
            
            for (const [fileName, fileData] of this.uploadedFiles) {
                fileIndex++;
                this.updateProgress((fileIndex / this.uploadedFiles.size) * 100, 
                                  `Processing ${fileName}...`);
                
                const result = await this.processFile(fileData.file);
                results.push({
                    fileName: fileName,
                    result: result
                });
            }
            
            this.displayResults(results);
            this.showToast('Processing completed successfully!', 'success');
            
        } catch (error) {
            console.error('Processing error:', error);
            let errorMessage = error.message;
            
            // Handle VRAM safety errors specially
            if (error.message.includes('VRAM safety check failed')) {
                errorMessage = 'VRAM usage would be too high. Try switching to the 3B model or reducing max tokens.';
            }
            
            this.showToast(`Processing failed: ${errorMessage}`, 'error');
        } finally {
            this.isProcessing = false;
            this.hideProgress();
            
            // Update VRAM status after processing
            setTimeout(() => {
                this.updateVramStatus();
                this.updateDetailedVramStatus();
            }, 1000);
        }
    }
    
    async processFile(file) {
        const base64 = await this.fileToBase64(file);
        const prompt = this.generatePrompt();
        
        const messages = [{
            role: 'user',
            content: [
                {
                    type: 'image',
                    image: base64
                },
                {
                    type: 'text',
                    text: prompt
                }
            ]
        }];
        
        const response = await fetch(`${this.serverUrl}/api/v1/generate`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                messages: messages,
                max_new_tokens: this.getMaxTokens(),
                temperature: 0.7,
                enable_safety_check: document.getElementById('enableSafetyCheck').checked
            })
        });
        
        if (!response.ok) {
            throw new Error(`Server error: ${response.status}`);
        }
        
        return await response.json();
    }
    
    fileToBase64(file) {
        return new Promise((resolve, reject) => {
            const reader = new FileReader();
            reader.readAsDataURL(file);
            reader.onload = () => resolve(reader.result);
            reader.onerror = error => reject(error);
        });
    }
    
    generatePrompt() {
        switch (this.currentTool) {
            case 'bank-transactions':
                return this.generateBankTransactionPrompt();
            case 'document-summary':
                return this.generateDocumentSummaryPrompt();
            case 'image-analysis':
                return this.generateImageAnalysisPrompt();
            case 'text-extraction':
                return this.generateTextExtractionPrompt();
            case 'custom-query':
                return document.getElementById('customQuery').value;
            default:
                return 'Please analyze this document or image.';
        }
    }
    
    generateBankTransactionPrompt() {
        const options = [];
        if (document.getElementById('extractDates').checked) options.push('transaction dates');
        if (document.getElementById('extractAmounts').checked) options.push('amounts');
        if (document.getElementById('extractDescriptions').checked) options.push('descriptions');
        if (document.getElementById('extractBalances').checked) options.push('running balances');
        if (document.getElementById('categorizeTransactions').checked) options.push('transaction categories');
        if (document.getElementById('detectMerchants').checked) options.push('merchant names');
        
        return `Analyze this bank statement or transaction document and extract the following information in a structured format: ${options.join(', ')}. 
                Present the data in a clear table format with proper headers. 
                If you find multiple transactions, list each one separately. 
                Also provide a summary of total debits, credits, and account balance if available.`;
    }
    
    generateDocumentSummaryPrompt() {
        const length = document.getElementById('summaryLength').value;
        const style = document.getElementById('summaryStyle').value;
        const extractKeyPoints = document.getElementById('extractKeyPoints').checked;
        const identifyEntities = document.getElementById('identifyEntities').checked;
        
        let prompt = `Provide a ${length} summary of this document in ${style} style.`;
        
        if (extractKeyPoints) {
            prompt += ' Include key points and main topics.';
        }
        
        if (identifyEntities) {
            prompt += ' Identify important names, dates, locations, and organizations mentioned.';
        }
        
        return prompt;
    }
    
    generateImageAnalysisPrompt() {
        const options = [];
        if (document.getElementById('describeImage').checked) options.push('detailed description');
        if (document.getElementById('identifyObjects').checked) options.push('object identification');
        if (document.getElementById('readText').checked) options.push('text extraction (OCR)');
        if (document.getElementById('analyzeColors').checked) options.push('color analysis');
        if (document.getElementById('detectFaces').checked) options.push('face detection');
        if (document.getElementById('identifyLandmarks').checked) options.push('landmark recognition');
        
        return `Analyze this image and provide: ${options.join(', ')}. 
                Be comprehensive and detailed in your analysis.`;
    }
    
    generateTextExtractionPrompt() {
        const preserveFormatting = document.getElementById('preserveFormatting').checked;
        const detectTables = document.getElementById('detectTables').checked;
        const extractHeaders = document.getElementById('extractHeaders').checked;
        const cleanText = document.getElementById('cleanText').checked;
        
        let prompt = 'Extract all text from this image or document.';
        
        if (preserveFormatting) prompt += ' Preserve the original formatting and structure.';
        if (detectTables) prompt += ' Identify and properly format any tables.';
        if (extractHeaders) prompt += ' Highlight headers and section titles.';
        if (cleanText) prompt += ' Clean up and properly format the extracted text.';
        
        return prompt;
    }
    
    getMaxTokens() {
        switch (this.currentTool) {
            case 'bank-transactions':
                return 1000;
            case 'document-summary':
                const length = document.getElementById('summaryLength').value;
                return length === 'brief' ? 200 : length === 'medium' ? 500 : 1000;
            case 'image-analysis':
                return 800;
            case 'text-extraction':
                return 1500;
            case 'custom-query':
                return 1000;
            default:
                return 500;
        }
    }
    
    displayResults(results) {
        const resultsSection = document.getElementById('resultsSection');
        const resultsContent = document.getElementById('resultsContent');
        
        resultsSection.style.display = 'block';
        
        let combinedResults = '';
        let totalTokens = 0;
        let totalTime = 0;
        
        results.forEach((result, index) => {
            combinedResults += `=== ${result.fileName} ===\n\n`;
            combinedResults += result.result.response;
            combinedResults += '\n\n';
            
            totalTokens += result.result.usage.total_tokens;
            totalTime += result.result.processing_time;
        });
        
        resultsContent.textContent = combinedResults;
        
        // Update processing info
        document.getElementById('processingTime').textContent = `${totalTime.toFixed(2)}s`;
        document.getElementById('tokensUsed').textContent = totalTokens.toString();
        
        // Scroll to results
        resultsSection.scrollIntoView({ behavior: 'smooth' });
    }
    
    showProgress() {
        const processBtn = document.getElementById('processBtn');
        const progressContainer = document.getElementById('progressContainer');
        
        processBtn.disabled = true;
        processBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> <span>Processing...</span>';
        progressContainer.style.display = 'block';
    }
    
    hideProgress() {
        const processBtn = document.getElementById('processBtn');
        const progressContainer = document.getElementById('progressContainer');
        
        processBtn.disabled = false;
        processBtn.innerHTML = '<i class="fas fa-play"></i> <span>Start Processing</span>';
        progressContainer.style.display = 'none';
        
        this.updateProcessButton(); // Re-check if button should be disabled
    }
    
    updateProgress(percentage, text) {
        const progressFill = document.getElementById('progressFill');
        const progressText = document.getElementById('progressText');
        
        progressFill.style.width = `${percentage}%`;
        progressText.textContent = text;
    }
    
    hideResults() {
        document.getElementById('resultsSection').style.display = 'none';
    }
    
    clearFiles() {
        this.uploadedFiles.clear();
        
        // Clear file previews
        document.querySelectorAll('.file-preview').forEach(preview => {
            preview.remove();
        });
        
        // Reset file inputs
        document.querySelectorAll('input[type=\"file\"]').forEach(input => {
            input.value = '';
        });
        
        this.updateProcessButton();
    }
    
    async clearVram() {
        try {
            const response = await fetch(`${this.serverUrl}/clear_vram`, {
                method: 'POST'
            });
            
            if (response.ok) {
                this.showToast('VRAM cleared successfully', 'success');
                this.updateVramStatus();
            } else {
                this.showToast('Failed to clear VRAM', 'error');
            }
        } catch (error) {
            this.showToast('Error clearing VRAM', 'error');
        }
    }
    
    copyResults() {
        const resultsContent = document.getElementById('resultsContent');
        navigator.clipboard.writeText(resultsContent.textContent).then(() => {
            this.showToast('Results copied to clipboard', 'success');
        }).catch(() => {
            this.showToast('Failed to copy results', 'error');
        });
    }
    
    downloadResults() {
        const resultsContent = document.getElementById('resultsContent');
        const content = resultsContent.textContent;
        const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
        const filename = `vlm-results-${timestamp}.txt`;
        
        const blob = new Blob([content], { type: 'text/plain' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = filename;
        a.click();
        URL.revokeObjectURL(url);
        
        this.showToast('Results downloaded successfully', 'success');
    }
    
    exportResults() {
        if (document.getElementById('resultsSection').style.display === 'none') {
            this.showToast('No results to export', 'warning');
            return;
        }
        
        this.downloadResults();
    }
    
    showToast(message, type = 'info') {
        const toastContainer = document.getElementById('toastContainer');
        const toast = document.createElement('div');
        toast.className = `toast ${type}`;
        
        const icon = type === 'success' ? 'fa-check-circle' :
                    type === 'error' ? 'fa-exclamation-circle' :
                    type === 'warning' ? 'fa-exclamation-triangle' : 'fa-info-circle';
        
        toast.innerHTML = `
            <i class="fas ${icon}"></i>
            <span>${message}</span>
        `;
        
        toastContainer.appendChild(toast);
        
        // Auto remove after 5 seconds
        setTimeout(() => {
            if (toast.parentNode) {
                toast.parentNode.removeChild(toast);
            }
        }, 5000);
    }
}

// Initialize the app when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.app = new VLMApp();
    
    // Update process button when custom query changes
    document.getElementById('customQuery').addEventListener('input', () => {
        window.app.updateProcessButton();
    });
});