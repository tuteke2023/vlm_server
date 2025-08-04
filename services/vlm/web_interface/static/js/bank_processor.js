// Bank Processor JavaScript - JSON-first workflow for bank statement processing

class BankProcessor {
    constructor() {
        this.currentFile = null;
        this.extractedData = null;
        this.savedFiles = [];
        this.initializeEventListeners();
        this.loadSavedFiles();
    }

    initializeEventListeners() {
        // File upload
        const dropZone = document.getElementById('dropZone');
        const fileInput = document.getElementById('fileInput');

        dropZone.addEventListener('click', () => fileInput.click());
        dropZone.addEventListener('dragover', (e) => {
            e.preventDefault();
            dropZone.classList.add('drag-over');
        });
        dropZone.addEventListener('dragleave', () => {
            dropZone.classList.remove('drag-over');
        });
        dropZone.addEventListener('drop', (e) => {
            e.preventDefault();
            dropZone.classList.remove('drag-over');
            const files = e.dataTransfer.files;
            if (files.length > 0) {
                this.handleFileUpload(files[0]);
            }
        });

        fileInput.addEventListener('change', (e) => {
            if (e.target.files.length > 0) {
                this.handleFileUpload(e.target.files[0]);
            }
        });
    }

    handleFileUpload(file) {
        // Validate file type
        const validTypes = ['application/pdf', 'image/png', 'image/jpeg', 'image/jpg'];
        if (!validTypes.includes(file.type)) {
            this.showError('Please upload a PDF or image file (PNG, JPG, JPEG)');
            return;
        }

        this.currentFile = file;
        
        // Show extraction options
        document.getElementById('extractionOptions').style.display = 'block';
        
        // Update UI
        const dropZone = document.getElementById('dropZone');
        dropZone.innerHTML = `
            <i class="fas fa-file-alt"></i>
            <p>${file.name}</p>
            <p class="file-size">${this.formatFileSize(file.size)}</p>
        `;
        
        // Update progress tracker
        this.updateProgressStep('upload', true);
    }

    async extractStatement() {
        if (!this.currentFile) {
            this.showError('Please upload a file first');
            return;
        }

        const format = document.querySelector('input[name="format"]:checked').value;
        
        // Show progress
        document.getElementById('progressBar').style.display = 'block';
        this.updateProgressBar(20);

        try {
            // Convert file to base64
            const base64Data = await this.fileToBase64(this.currentFile);
            
            console.log('Base64 data length:', base64Data.length);
            console.log('Base64 data preview:', base64Data.substring(0, 100));
            
            this.updateProgressBar(40);

            // Prepare the request
            const messages = [{
                role: "user",
                content: [
                    {
                        type: "text",
                        text: format === 'json' 
                            ? "Extract all transactions from this bank statement in JSON format with fields: date, description, debit, credit, balance. IMPORTANT: Include ALL transactions including small amounts like 6.77"
                            : "Extract ALL transactions from this bank statement in a table format with columns: Date | Description | Reference | Withdrawals/Debit | Deposits/Credit | Balance. Include EVERY transaction."
                    },
                    {
                        type: "image",
                        image: base64Data
                    }
                ]
            }];

            this.updateProgressBar(60);

            // Call the appropriate endpoint based on format
            const endpoint = format === 'json' 
                ? 'http://localhost:8000/api/v1/bank_extract_json'
                : 'http://localhost:8000/api/v1/generate';
                
            const response = await fetch(endpoint, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    messages: messages,
                    max_new_tokens: 2048,  // Increased for complete extraction
                    temperature: 0.1
                })
            });

            this.updateProgressBar(80);

            if (!response.ok) {
                throw new Error(`Server error: ${response.status}`);
            }

            const result = await response.json();
            this.updateProgressBar(100);

            // Process the extraction result
            console.log('Extraction result:', result);
            
            if (format === 'json' && result.data) {
                // Direct JSON response from new endpoint
                console.log('Using result.data:', result.data);
                this.extractedData = result.data;
                this.displayExtractionResult(result.data);
                
                // Show process section
                document.getElementById('process-section').style.display = 'block';
                document.getElementById('export-section').style.display = 'block';
            } else if (format === 'json') {
                console.log('Processing JSON from response text');
                this.processJSONExtraction(result.response);
            } else {
                console.log('Processing table extraction');
                this.processTableExtraction(result.response);
            }

            // Update progress tracker
            this.updateProgressStep('extract', true);
            
            // Hide progress bar after a delay
            setTimeout(() => {
                document.getElementById('progressBar').style.display = 'none';
            }, 500);

        } catch (error) {
            console.error('Extraction error:', error);
            this.showError(`Failed to extract statement: ${error.message}`);
            document.getElementById('progressBar').style.display = 'none';
        }
    }

    processJSONExtraction(responseText) {
        try {
            // Try to extract JSON from the response
            let jsonData;
            
            // First try: direct JSON parse
            try {
                jsonData = JSON.parse(responseText);
            } catch (e) {
                // Second try: extract JSON from markdown code block
                const jsonMatch = responseText.match(/```(?:json)?\s*([\s\S]*?)```/);
                if (jsonMatch) {
                    jsonData = JSON.parse(jsonMatch[1]);
                } else {
                    // Third try: find JSON object in text
                    const jsonStart = responseText.indexOf('{');
                    const jsonEnd = responseText.lastIndexOf('}') + 1;
                    if (jsonStart !== -1 && jsonEnd > jsonStart) {
                        jsonData = JSON.parse(responseText.substring(jsonStart, jsonEnd));
                    } else {
                        throw new Error('No JSON found in response');
                    }
                }
            }

            this.extractedData = jsonData;
            this.displayExtractionResult(jsonData);
            
            // Show process section
            document.getElementById('process-section').style.display = 'block';
            document.getElementById('export-section').style.display = 'block';

        } catch (error) {
            console.error('JSON parsing error:', error);
            // Fallback to table parsing
            this.processTableExtraction(responseText);
        }
    }

    processTableExtraction(responseText) {
        // Convert table text to JSON structure
        const transactions = this.parseTableToJSON(responseText);
        
        this.extractedData = {
            statement_date: new Date().toISOString().split('T')[0],
            transactions: transactions,
            extracted_at: new Date().toISOString()
        };

        this.displayExtractionResult(this.extractedData);
        
        // Show process section
        document.getElementById('process-section').style.display = 'block';
        document.getElementById('export-section').style.display = 'block';
    }

    parseTableToJSON(tableText) {
        const transactions = [];
        const lines = tableText.split('\n');
        
        for (const line of lines) {
            // Skip headers and empty lines
            if (line.includes('Date') || line.includes('---') || line.trim() === '') {
                continue;
            }
            
            // Parse pipe-delimited format
            if (line.includes('|')) {
                const parts = line.split('|').map(p => p.trim()).filter(p => p);
                if (parts.length >= 4) {
                    transactions.push({
                        date: parts[0],
                        description: parts[1],
                        debit: parseFloat(parts[2]) || 0,
                        credit: parseFloat(parts[3]) || 0,
                        balance: parseFloat(parts[4]) || 0
                    });
                }
            }
        }
        
        return transactions;
    }

    displayExtractionResult(data) {
        // Update summary
        const transactions = data.transactions || [];
        const totalDebits = transactions.reduce((sum, t) => sum + (t.debit || 0), 0);
        const totalCredits = transactions.reduce((sum, t) => sum + (t.credit || 0), 0);
        
        document.getElementById('transactionCount').textContent = transactions.length;
        document.getElementById('totalDebits').textContent = `$${totalDebits.toFixed(2)}`;
        document.getElementById('totalCredits').textContent = `$${totalCredits.toFixed(2)}`;
        
        // Show JSON preview
        const jsonPreview = document.getElementById('jsonPreview');
        jsonPreview.textContent = JSON.stringify(data, null, 2);
        
        // Show result section
        document.getElementById('extractionResult').style.display = 'block';
        document.getElementById('preview-section').style.display = 'block';
        document.getElementById('preview-section').classList.add('active');
        
        // Update all workflow steps to be visible
        document.querySelectorAll('.workflow-step').forEach(step => {
            step.classList.add('active');
        });
    }

    async saveJSON() {
        if (!this.extractedData) {
            this.showError('No data to save');
            return;
        }

        try {
            const filename = `bank_statement_${new Date().toISOString().split('T')[0]}_${Date.now()}.json`;
            const blob = new Blob([JSON.stringify(this.extractedData, null, 2)], { type: 'application/json' });
            
            // Save to local storage (simulating server save)
            const savedFile = {
                filename: filename,
                timestamp: new Date().toISOString(),
                data: this.extractedData,
                size: blob.size
            };
            
            this.savedFiles.push(savedFile);
            localStorage.setItem('savedBankStatements', JSON.stringify(this.savedFiles));
            
            // Download the file
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = filename;
            a.click();
            URL.revokeObjectURL(url);
            
            this.showSuccess('JSON file saved successfully');
            this.updateSavedFilesList();
            
        } catch (error) {
            this.showError(`Failed to save JSON: ${error.message}`);
        }
    }

    viewTransactions() {
        if (!this.extractedData || !this.extractedData.transactions) {
            this.showError('No transactions to display');
            return;
        }

        const transactionList = document.getElementById('transactionList');
        transactionList.innerHTML = '';
        
        this.extractedData.transactions.forEach((trans, index) => {
            const row = document.createElement('tr');
            row.innerHTML = `
                <td>${trans.date}</td>
                <td>${trans.description}</td>
                <td class="expense">${trans.debit > 0 ? `$${trans.debit.toFixed(2)}` : ''}</td>
                <td class="income">${trans.credit > 0 ? `$${trans.credit.toFixed(2)}` : ''}</td>
                <td>$${trans.balance.toFixed(2)}</td>
            `;
            transactionList.appendChild(row);
        });

        document.getElementById('transactionModal').style.display = 'flex';
    }

    closeModal() {
        document.getElementById('transactionModal').style.display = 'none';
    }

    async addGSTCoding() {
        if (!this.extractedData) {
            this.showError('Please extract statement first');
            return;
        }

        this.showInfo('Adding GST coding to transactions...');
        
        // Update progress
        this.updateProgressStep('process', true);
        
        // In a real implementation, this would call an AI endpoint
        // For now, we'll simulate the process
        setTimeout(() => {
            this.extractedData.transactions = this.extractedData.transactions.map(trans => ({
                ...trans,
                gst_applicable: trans.description.toLowerCase().includes('service') || 
                               trans.description.toLowerCase().includes('purchase'),
                gst_amount: trans.debit * 0.1, // 10% GST
                gst_category: 'Standard Rate'
            }));
            
            this.showSuccess('GST coding added successfully');
            this.displayExtractionResult(this.extractedData);
        }, 1000);
    }

    async classifyTransactions() {
        if (!this.extractedData) {
            this.showError('Please extract statement first');
            return;
        }

        this.showInfo('Classifying transactions...');
        
        // Simulate classification
        setTimeout(() => {
            const categories = ['Operating Expenses', 'Revenue', 'Capital Expenses', 'Personal'];
            this.extractedData.transactions = this.extractedData.transactions.map(trans => ({
                ...trans,
                category: categories[Math.floor(Math.random() * categories.length)],
                tax_deductible: Math.random() > 0.5
            }));
            
            this.showSuccess('Transactions classified successfully');
            this.displayExtractionResult(this.extractedData);
        }, 1000);
    }

    async businessPersonal() {
        if (!this.extractedData) {
            this.showError('Please extract statement first');
            return;
        }

        this.showInfo('Splitting business/personal transactions...');
        
        setTimeout(() => {
            this.extractedData.transactions = this.extractedData.transactions.map(trans => ({
                ...trans,
                business_percentage: Math.random() > 0.3 ? 100 : 0,
                transaction_type: Math.random() > 0.3 ? 'business' : 'personal'
            }));
            
            this.showSuccess('Business/Personal split completed');
            this.displayExtractionResult(this.extractedData);
        }, 1000);
    }

    async addNotes() {
        if (!this.extractedData) {
            this.showError('Please extract statement first');
            return;
        }

        // In a real app, this would open a UI for adding notes
        this.showInfo('Note editing feature coming soon!');
    }

    async exportCSV() {
        if (!this.extractedData) {
            this.showError('No data to export');
            return;
        }

        // Convert to CSV
        const csv = this.convertToCSV(this.extractedData.transactions);
        const blob = new Blob([csv], { type: 'text/csv' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `bank_statement_${new Date().toISOString().split('T')[0]}.csv`;
        a.click();
        URL.revokeObjectURL(url);
        
        this.showSuccess('CSV exported successfully');
        this.updateProgressStep('export', true);
    }

    convertToCSV(transactions) {
        const headers = Object.keys(transactions[0] || {});
        const csvHeaders = headers.join(',');
        const csvRows = transactions.map(trans => 
            headers.map(header => {
                const value = trans[header];
                return typeof value === 'string' && value.includes(',') 
                    ? `"${value}"` 
                    : value;
            }).join(',')
        );
        
        return [csvHeaders, ...csvRows].join('\n');
    }

    async exportQuickBooks() {
        this.showInfo('QuickBooks export format coming soon!');
    }

    async exportXero() {
        this.showInfo('Xero export format coming soon!');
    }

    async exportTaxReport() {
        this.showInfo('Tax report generation coming soon!');
    }

    loadSavedFiles() {
        const saved = localStorage.getItem('savedBankStatements');
        if (saved) {
            this.savedFiles = JSON.parse(saved);
            this.updateSavedFilesList();
        }
    }

    updateSavedFilesList() {
        const container = document.getElementById('savedFiles');
        
        if (this.savedFiles.length === 0) {
            container.innerHTML = '<p class="text-muted">No saved statements yet</p>';
            return;
        }

        container.innerHTML = this.savedFiles.map((file, index) => `
            <div class="file-item">
                <div>
                    <strong>${file.filename}</strong>
                    <br>
                    <small>${new Date(file.timestamp).toLocaleString()} - ${this.formatFileSize(file.size)}</small>
                </div>
                <div>
                    <button class="secondary-button" onclick="bankProcessor.loadSavedFile(${index})">
                        <i class="fas fa-folder-open"></i> Load
                    </button>
                </div>
            </div>
        `).join('');
    }

    loadSavedFile(index) {
        const file = this.savedFiles[index];
        if (file && file.data) {
            this.extractedData = file.data;
            this.displayExtractionResult(file.data);
            
            // Update UI
            document.getElementById('process-section').style.display = 'block';
            document.getElementById('export-section').style.display = 'block';
            this.updateProgressStep('extract', true);
            
            this.showSuccess(`Loaded ${file.filename}`);
        }
    }

    updateProgressStep(step, completed) {
        const stepElement = document.getElementById(`step-${step}`);
        if (stepElement && completed) {
            stepElement.classList.add('completed');
        }
    }

    updateProgressBar(percentage) {
        const fill = document.querySelector('.progress-fill');
        if (fill) {
            fill.style.width = `${percentage}%`;
        }
    }

    fileToBase64(file) {
        return new Promise((resolve, reject) => {
            const reader = new FileReader();
            reader.readAsDataURL(file);
            reader.onload = () => resolve(reader.result);
            reader.onerror = error => reject(error);
        });
    }

    formatFileSize(bytes) {
        if (bytes < 1024) return bytes + ' B';
        if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
        return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
    }

    showError(message) {
        this.showNotification(message, 'error');
    }

    showSuccess(message) {
        this.showNotification(message, 'success');
    }

    showInfo(message) {
        this.showNotification(message, 'info');
    }

    showNotification(message, type) {
        const notification = document.createElement('div');
        notification.className = `notification ${type}`;
        notification.innerHTML = `
            <i class="fas fa-${type === 'error' ? 'exclamation-circle' : type === 'success' ? 'check-circle' : 'info-circle'}"></i>
            <span>${message}</span>
        `;
        
        document.body.appendChild(notification);
        
        setTimeout(() => {
            notification.classList.add('show');
        }, 10);
        
        setTimeout(() => {
            notification.classList.remove('show');
            setTimeout(() => notification.remove(), 300);
        }, 3000);
    }
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    window.bankProcessor = new BankProcessor();
});

// Add notification styles
const style = document.createElement('style');
style.textContent = `
    .notification {
        position: fixed;
        top: 20px;
        right: -300px;
        background: white;
        padding: 15px 20px;
        border-radius: 8px;
        box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        display: flex;
        align-items: center;
        gap: 10px;
        transition: right 0.3s ease;
        z-index: 1000;
        max-width: 300px;
    }
    
    .notification.show {
        right: 20px;
    }
    
    .notification.error {
        border-left: 4px solid #ef4444;
    }
    
    .notification.error i {
        color: #ef4444;
    }
    
    .notification.success {
        border-left: 4px solid #10b981;
    }
    
    .notification.success i {
        color: #10b981;
    }
    
    .notification.info {
        border-left: 4px solid #3b82f6;
    }
    
    .notification.info i {
        color: #3b82f6;
    }
    
    .drag-over {
        border-color: var(--primary-color) !important;
        background: rgba(99, 102, 241, 0.05) !important;
    }
    
    .progress-fill {
        height: 100%;
        background: var(--primary-color);
        border-radius: 4px;
        transition: width 0.3s ease;
    }
    
    .progress-bar {
        height: 8px;
        background: var(--border-color);
        border-radius: 4px;
        overflow: hidden;
        margin: 15px 0;
    }
`;
document.head.appendChild(style);