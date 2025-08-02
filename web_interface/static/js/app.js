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
        if (document.getElementById('extractAmounts').checked) options.push('amounts (separate debit and credit)');
        if (document.getElementById('extractDescriptions').checked) options.push('descriptions');
        if (document.getElementById('extractBalances').checked) options.push('running balances');
        if (document.getElementById('categorizeTransactions').checked) options.push('transaction categories');
        if (document.getElementById('detectMerchants').checked) options.push('merchant names');
        
        return `Analyze this bank statement or transaction document and extract the following information: ${options.join(', ')}. 
                
                IMPORTANT: Format the output as a table with these exact headers:
                Date | Description | Debit | Credit | Balance
                
                Rules:
                - Use consistent date format (MM/DD/YYYY or DD/MM/YYYY)
                - Debit amounts should be positive numbers in the Debit column
                - Credit amounts should be positive numbers in the Credit column  
                - Leave empty cells blank (don't use 0.00 for empty cells)
                - Include all transactions found in the document
                - After the table, provide a summary with total debits and total credits
                
                Example format:
                Date       | Description              | Debit   | Credit  | Balance
                01/15/2024 | Grocery Store Purchase   | 45.32   |         | 1254.68
                01/16/2024 | Salary Deposit          |         | 2500.00 | 3754.68`;
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
        
        let totalTokens = 0;
        let totalTime = 0;
        
        // Check if this is a bank transaction processing
        const isBankTransaction = this.currentTool === 'bank-transactions';
        
        if (isBankTransaction && results.length > 0) {
            // Try to parse and display bank transactions in table format
            this.displayBankTransactionTable(results, resultsContent);
        } else {
            // Regular text display for other tools
            let combinedResults = '';
            results.forEach((result, index) => {
                combinedResults += `=== ${result.fileName} ===\n\n`;
                combinedResults += result.result.response;
                combinedResults += '\n\n';
            });
            resultsContent.textContent = combinedResults;
        }
        
        // Calculate totals
        results.forEach(result => {
            totalTokens += result.result.usage.total_tokens;
            totalTime += result.result.processing_time;
        });
        
        // Update processing info
        document.getElementById('processingTime').textContent = `${totalTime.toFixed(2)}s`;
        document.getElementById('tokensUsed').textContent = totalTokens.toString();
        
        // Scroll to results
        resultsSection.scrollIntoView({ behavior: 'smooth' });
    }

    displayBankTransactionTable(results, container) {
        // Store original response for reference
        this.originalBankData = results;
        
        // Parse transactions from AI response
        const transactions = this.parseBankTransactions(results);
        
        if (transactions.length === 0) {
            // Fallback to text display if parsing fails
            let combinedResults = '';
            results.forEach((result, index) => {
                combinedResults += `=== ${result.fileName} ===\n\n`;
                combinedResults += result.result.response;
                combinedResults += '\n\n';
            });
            container.textContent = combinedResults;
            return;
        }
        
        // Create table container
        container.innerHTML = `
            <div class="bank-table-container">
                <div class="table-actions">
                    <button class="btn btn-sm" onclick="app.addNewTransaction()">
                        <i class="fas fa-plus"></i> Add Row
                    </button>
                    <button class="btn btn-sm" onclick="app.exportToCSV()">
                        <i class="fas fa-file-csv"></i> Export CSV
                    </button>
                    <button class="btn btn-sm" onclick="app.exportToExcel()">
                        <i class="fas fa-file-excel"></i> Export Excel
                    </button>
                    <button class="btn btn-sm" onclick="app.saveModifications()">
                        <i class="fas fa-save"></i> Save Changes
                    </button>
                </div>
                <div class="table-wrapper">
                    <table id="bankTransactionTable" class="transaction-table">
                        <thead>
                            <tr>
                                <th>Date</th>
                                <th>Description</th>
                                <th>Category</th>
                                <th>Debit</th>
                                <th>Credit</th>
                                <th>Balance</th>
                                <th>Actions</th>
                            </tr>
                        </thead>
                        <tbody id="transactionTableBody">
                        </tbody>
                        <tfoot>
                            <tr class="summary-row">
                                <td colspan="3"><strong>Total</strong></td>
                                <td id="totalDebit"><strong>$0.00</strong></td>
                                <td id="totalCredit"><strong>$0.00</strong></td>
                                <td colspan="2"></td>
                            </tr>
                        </tfoot>
                    </table>
                </div>
                <div class="transaction-summary">
                    <div id="transactionSummary"></div>
                </div>
            </div>
        `;
        
        // Populate table
        this.populateTransactionTable(transactions);
        
        // Store transactions for export
        this.currentTransactions = transactions;
    }

    parseBankTransactions(results) {
        const transactions = [];
        
        results.forEach(result => {
            const text = result.result.response;
            
            // Try to extract transactions using various patterns
            // This is a flexible parser that handles different AI response formats
            const lines = text.split('\n');
            let inTable = false;
            
            lines.forEach(line => {
                // Skip empty lines and headers
                if (!line.trim() || line.includes('---') || line.includes('===')) return;
                
                // Detect table start
                if (line.toLowerCase().includes('date') && line.toLowerCase().includes('description')) {
                    inTable = true;
                    return;
                }
                
                if (inTable) {
                    // Try to parse transaction line
                    const transaction = this.parseTransactionLine(line);
                    if (transaction) {
                        transactions.push(transaction);
                    }
                }
            });
        });
        
        return transactions;
    }

    parseTransactionLine(line) {
        // Remove extra spaces and split by common delimiters
        const parts = line.trim().split(/\s{2,}|\t|\|/).filter(p => p.trim());
        
        if (parts.length < 3) return null;
        
        // Try to identify transaction components
        const transaction = {
            id: Date.now() + Math.random(),
            date: '',
            description: '',
            category: '',
            debit: 0,
            credit: 0,
            balance: 0
        };
        
        // Simple heuristic parsing
        let partIndex = 0;
        
        // First part is usually date
        if (parts[partIndex] && this.looksLikeDate(parts[partIndex])) {
            transaction.date = parts[partIndex];
            partIndex++;
        }
        
        // Description is usually the longest text part
        let descriptionParts = [];
        while (partIndex < parts.length && !this.looksLikeMoney(parts[partIndex])) {
            descriptionParts.push(parts[partIndex]);
            partIndex++;
        }
        transaction.description = descriptionParts.join(' ');
        
        // Look for money amounts
        while (partIndex < parts.length) {
            const part = parts[partIndex];
            if (this.looksLikeMoney(part)) {
                const amount = this.parseAmount(part);
                if (amount < 0 || part.includes('-') || part.toLowerCase().includes('debit')) {
                    transaction.debit = Math.abs(amount);
                } else {
                    transaction.credit = amount;
                }
                
                // Check if next part might be balance
                if (partIndex + 1 < parts.length && this.looksLikeMoney(parts[partIndex + 1])) {
                    transaction.balance = this.parseAmount(parts[partIndex + 1]);
                    partIndex++;
                }
            }
            partIndex++;
        }
        
        // Auto-categorize if not already done
        if (!transaction.category) {
            transaction.category = this.autoCategorizeTrans(transaction.description);
        }
        
        return transaction;
    }

    looksLikeDate(str) {
        return /\d{1,2}[\/\-\.]\d{1,2}[\/\-\.]\d{2,4}|\d{4}[\/\-]\d{1,2}[\/\-]\d{1,2}/.test(str);
    }

    looksLikeMoney(str) {
        return /[$£€]?\s*\d+[,.]?\d*|^\d+[,.]?\d*$/.test(str);
    }

    parseAmount(str) {
        return parseFloat(str.replace(/[$£€,]/g, '')) || 0;
    }

    autoCategorizeTrans(description) {
        const desc = description.toLowerCase();
        
        if (desc.includes('grocery') || desc.includes('food') || desc.includes('market')) return 'Groceries';
        if (desc.includes('gas') || desc.includes('fuel') || desc.includes('petrol')) return 'Transportation';
        if (desc.includes('restaurant') || desc.includes('cafe') || desc.includes('dining')) return 'Dining';
        if (desc.includes('amazon') || desc.includes('online') || desc.includes('ebay')) return 'Shopping';
        if (desc.includes('utility') || desc.includes('electric') || desc.includes('water')) return 'Utilities';
        if (desc.includes('rent') || desc.includes('mortgage')) return 'Housing';
        if (desc.includes('salary') || desc.includes('payroll') || desc.includes('wage')) return 'Income';
        if (desc.includes('transfer') || desc.includes('payment')) return 'Transfer';
        
        return 'Other';
    }

    populateTransactionTable(transactions) {
        const tbody = document.getElementById('transactionTableBody');
        tbody.innerHTML = '';
        
        let totalDebit = 0;
        let totalCredit = 0;
        
        transactions.forEach((trans, index) => {
            const row = document.createElement('tr');
            row.dataset.transactionId = trans.id;
            
            // Add modified class if transaction was edited
            if (trans.modified) {
                row.classList.add('modified');
            }
            
            row.innerHTML = `
                <td><input type="text" class="table-input" value="${trans.date}" data-field="date"></td>
                <td><input type="text" class="table-input" value="${trans.description}" data-field="description"></td>
                <td>
                    <select class="table-select" data-field="category">
                        <option value="Groceries" ${trans.category === 'Groceries' ? 'selected' : ''}>Groceries</option>
                        <option value="Transportation" ${trans.category === 'Transportation' ? 'selected' : ''}>Transportation</option>
                        <option value="Dining" ${trans.category === 'Dining' ? 'selected' : ''}>Dining</option>
                        <option value="Shopping" ${trans.category === 'Shopping' ? 'selected' : ''}>Shopping</option>
                        <option value="Utilities" ${trans.category === 'Utilities' ? 'selected' : ''}>Utilities</option>
                        <option value="Housing" ${trans.category === 'Housing' ? 'selected' : ''}>Housing</option>
                        <option value="Income" ${trans.category === 'Income' ? 'selected' : ''}>Income</option>
                        <option value="Transfer" ${trans.category === 'Transfer' ? 'selected' : ''}>Transfer</option>
                        <option value="Other" ${trans.category === 'Other' ? 'selected' : ''}>Other</option>
                    </select>
                </td>
                <td><input type="number" class="table-input amount" value="${trans.debit}" data-field="debit" step="0.01"></td>
                <td><input type="number" class="table-input amount" value="${trans.credit}" data-field="credit" step="0.01"></td>
                <td><input type="number" class="table-input amount" value="${trans.balance}" data-field="balance" step="0.01"></td>
                <td>
                    <button class="btn-icon" onclick="app.deleteTransaction('${trans.id}')" title="Delete">
                        <i class="fas fa-trash"></i>
                    </button>
                </td>
            `;
            
            tbody.appendChild(row);
            
            totalDebit += trans.debit;
            totalCredit += trans.credit;
        });
        
        // Update totals
        document.getElementById('totalDebit').innerHTML = `<strong>$${totalDebit.toFixed(2)}</strong>`;
        document.getElementById('totalCredit').innerHTML = `<strong>$${totalCredit.toFixed(2)}</strong>`;
        
        // Add change listeners
        tbody.querySelectorAll('input, select').forEach(input => {
            input.addEventListener('change', () => this.handleTransactionEdit(input));
        });
    }

    handleTransactionEdit(input) {
        const row = input.closest('tr');
        const transId = row.dataset.transactionId;
        const field = input.dataset.field;
        const value = input.type === 'number' ? parseFloat(input.value) || 0 : input.value;
        
        // Update transaction in memory
        const trans = this.currentTransactions.find(t => t.id == transId);
        if (trans) {
            trans[field] = value;
            trans.modified = true;
            
            // Add visual indicator that row was modified
            row.classList.add('modified');
            
            // Recalculate totals if amounts changed
            if (['debit', 'credit'].includes(field)) {
                this.updateTotals();
            }
        }
    }

    updateTotals() {
        let totalDebit = 0;
        let totalCredit = 0;
        
        this.currentTransactions.forEach(trans => {
            totalDebit += trans.debit || 0;
            totalCredit += trans.credit || 0;
        });
        
        document.getElementById('totalDebit').innerHTML = `<strong>$${totalDebit.toFixed(2)}</strong>`;
        document.getElementById('totalCredit').innerHTML = `<strong>$${totalCredit.toFixed(2)}</strong>`;
    }

    deleteTransaction(transId) {
        if (confirm('Are you sure you want to delete this transaction?')) {
            this.currentTransactions = this.currentTransactions.filter(t => t.id != transId);
            this.populateTransactionTable(this.currentTransactions);
        }
    }

    addNewTransaction() {
        const newTransaction = {
            id: Date.now() + Math.random(),
            date: new Date().toLocaleDateString('en-US'),
            description: 'New Transaction',
            category: 'Other',
            debit: 0,
            credit: 0,
            balance: 0,
            isNew: true,
            modified: true
        };
        
        this.currentTransactions.push(newTransaction);
        this.populateTransactionTable(this.currentTransactions);
        
        // Focus on the new row's description field
        setTimeout(() => {
            const newRow = document.querySelector(`tr[data-transaction-id="${newTransaction.id}"]`);
            if (newRow) {
                const descInput = newRow.querySelector('input[data-field="description"]');
                if (descInput) {
                    descInput.focus();
                    descInput.select();
                }
            }
        }, 100);
    }

    exportToCSV() {
        if (!this.currentTransactions || this.currentTransactions.length === 0) {
            this.showToast('No transactions to export', 'error');
            return;
        }
        
        let csv = 'Date,Description,Category,Debit,Credit,Balance\n';
        
        this.currentTransactions.forEach(trans => {
            csv += `"${trans.date}","${trans.description}","${trans.category}",${trans.debit},${trans.credit},${trans.balance}\n`;
        });
        
        const blob = new Blob([csv], { type: 'text/csv' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `bank_transactions_${new Date().toISOString().split('T')[0]}.csv`;
        a.click();
        URL.revokeObjectURL(url);
        
        this.showToast('Exported to CSV successfully', 'success');
    }

    exportToExcel() {
        if (!this.currentTransactions || this.currentTransactions.length === 0) {
            this.showToast('No transactions to export', 'error');
            return;
        }
        
        // Create a simple HTML table for Excel
        let html = `
            <html>
            <head>
                <meta charset="utf-8">
                <style>
                    table { border-collapse: collapse; }
                    th, td { border: 1px solid black; padding: 5px; }
                    th { background-color: #f0f0f0; font-weight: bold; }
                    .number { text-align: right; }
                </style>
            </head>
            <body>
                <table>
                    <tr>
                        <th>Date</th>
                        <th>Description</th>
                        <th>Category</th>
                        <th>Debit</th>
                        <th>Credit</th>
                        <th>Balance</th>
                    </tr>
        `;
        
        this.currentTransactions.forEach(trans => {
            html += `
                <tr>
                    <td>${trans.date}</td>
                    <td>${trans.description}</td>
                    <td>${trans.category}</td>
                    <td class="number">${trans.debit.toFixed(2)}</td>
                    <td class="number">${trans.credit.toFixed(2)}</td>
                    <td class="number">${trans.balance.toFixed(2)}</td>
                </tr>
            `;
        });
        
        html += '</table></body></html>';
        
        const blob = new Blob([html], { type: 'application/vnd.ms-excel' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `bank_transactions_${new Date().toISOString().split('T')[0]}.xls`;
        a.click();
        URL.revokeObjectURL(url);
        
        this.showToast('Exported to Excel successfully', 'success');
    }

    saveModifications() {
        if (!this.currentTransactions || this.currentTransactions.length === 0) {
            this.showToast('No transactions to save', 'error');
            return;
        }
        
        // Create training data object
        const trainingData = {
            timestamp: new Date().toISOString(),
            originalResponse: this.originalBankData,
            editedTransactions: this.currentTransactions,
            modifications: this.currentTransactions.filter(t => t.modified).length,
            userAgent: navigator.userAgent
        };
        
        // Convert to JSON
        const json = JSON.stringify(trainingData, null, 2);
        const blob = new Blob([json], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `bank_training_data_${new Date().toISOString().split('T')[0]}_${Date.now()}.json`;
        a.click();
        URL.revokeObjectURL(url);
        
        this.showToast('Training data saved successfully', 'success');
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