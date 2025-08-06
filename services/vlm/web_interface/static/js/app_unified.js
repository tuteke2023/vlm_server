/**
 * Unified VLM Interface Application
 * Consolidates functionality from app.js and bank_processor.js
 */

class VLMInterface {
    constructor() {
        // Initialize API client
        this.api = new UnifiedAPIClient('http://localhost:8000');
        
        // UI elements
        this.elements = {};
        this.initializeElements();
        
        // State
        this.currentMode = 'general';
        this.isProcessing = false;
        this.currentProvider = 'local';
        this.hasShownPrivacyWarning = false;
        
        // Initialize
        this.initialize();
    }

    initializeElements() {
        // Main containers
        this.elements.dropZone = document.getElementById('dropZone');
        this.elements.imagePreview = document.getElementById('imagePreview');
        this.elements.imagePreviewImg = document.getElementById('imagePreviewImg');
        this.elements.fileInput = document.getElementById('fileInput');
        
        // Mode selection
        this.elements.modeButtons = document.querySelectorAll('.mode-btn');
        
        // Input/Output
        this.elements.promptInput = document.getElementById('promptInput');
        this.elements.analyzeBtn = document.getElementById('analyzeBtn');
        this.elements.clearBtn = document.getElementById('clearBtn');
        this.elements.resultDiv = document.getElementById('result');
        
        // Bank specific
        this.elements.exportCsvBtn = document.getElementById('exportCsvBtn');
        this.elements.exportJsonBtn = document.getElementById('exportJsonBtn');
        
        // Provider selection
        this.elements.providerSelect = document.getElementById('providerSelect');
        this.elements.providerStatus = document.getElementById('providerStatus');
        
        // Status
        this.elements.statusBar = document.getElementById('statusBar');
        this.elements.vramStatus = document.getElementById('vramStatus');
        
        // Modals
        this.elements.privacyModal = document.getElementById('privacyWarningModal');
        this.elements.fallbackModal = document.getElementById('fallbackConfirmModal');
    }

    async initialize() {
        // Set up event listeners
        this.setupEventListeners();
        
        // Load providers
        await this.loadProviders();
        
        // Start monitoring
        this.startHealthCheck();
        this.startVRAMMonitoring();
        
        // Set default mode
        this.setMode('general');
    }

    setupEventListeners() {
        // Drag and drop
        this.elements.dropZone.addEventListener('click', () => this.elements.fileInput.click());
        this.elements.fileInput.addEventListener('change', (e) => this.handleFileSelect(e));
        
        this.elements.dropZone.addEventListener('dragover', (e) => {
            e.preventDefault();
            this.elements.dropZone.classList.add('drag-over');
        });
        
        this.elements.dropZone.addEventListener('dragleave', () => {
            this.elements.dropZone.classList.remove('drag-over');
        });
        
        this.elements.dropZone.addEventListener('drop', (e) => {
            e.preventDefault();
            this.elements.dropZone.classList.remove('drag-over');
            if (e.dataTransfer.files.length > 0) {
                this.handleFile(e.dataTransfer.files[0]);
            }
        });

        // Mode buttons
        this.elements.modeButtons.forEach(btn => {
            btn.addEventListener('click', () => this.setMode(btn.dataset.mode));
        });

        // Action buttons
        this.elements.analyzeBtn.addEventListener('click', () => this.processImage());
        this.elements.clearBtn.addEventListener('click', () => this.clearAll());
        
        // Export buttons
        if (this.elements.exportCsvBtn) {
            this.elements.exportCsvBtn.addEventListener('click', () => this.exportResults('csv'));
        }
        if (this.elements.exportJsonBtn) {
            this.elements.exportJsonBtn.addEventListener('click', () => this.exportResults('json'));
        }

        // Provider selection
        if (this.elements.providerSelect) {
            this.elements.providerSelect.addEventListener('change', (e) => this.switchProvider(e.target.value));
        }

        // Enter key in prompt
        this.elements.promptInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                this.processImage();
            }
        });
    }

    async loadProviders() {
        try {
            const providers = await this.api.getProviders();
            
            if (this.elements.providerSelect) {
                this.elements.providerSelect.innerHTML = '';
                
                for (const [key, info] of Object.entries(providers)) {
                    const option = document.createElement('option');
                    option.value = key;
                    option.textContent = info.display_name;
                    option.disabled = !info.available;
                    if (!info.available) {
                        option.textContent += ' (Unavailable)';
                    }
                    this.elements.providerSelect.appendChild(option);
                }
            }
        } catch (error) {
            console.error('Failed to load providers:', error);
        }
    }

    async switchProvider(provider) {
        // Show privacy warning for OpenAI if not shown
        if (provider === 'openai' && !this.hasShownPrivacyWarning) {
            const proceed = await this.showPrivacyWarning();
            if (!proceed) {
                this.elements.providerSelect.value = this.currentProvider;
                return;
            }
            this.hasShownPrivacyWarning = true;
        }

        try {
            const result = await this.api.switchProvider(provider);
            
            if (result.status === 'success') {
                this.currentProvider = provider;
                this.updateProviderStatus(provider);
                this.showStatus(`Switched to ${provider}`, 'success');
            } else {
                throw new Error(result.message || 'Failed to switch provider');
            }
        } catch (error) {
            console.error('Provider switch failed:', error);
            this.showStatus(`Failed to switch provider: ${error.message}`, 'error');
            this.elements.providerSelect.value = this.currentProvider;
        }
    }

    updateProviderStatus(provider) {
        if (this.elements.providerStatus) {
            const statusText = provider === 'openai' ? 'Using OpenAI GPT-4V' : 'Using Local VLM';
            this.elements.providerStatus.textContent = statusText;
            this.elements.providerStatus.className = `provider-status ${provider}`;
        }
    }

    setMode(mode) {
        this.currentMode = mode;
        
        // Update button states
        this.elements.modeButtons.forEach(btn => {
            btn.classList.toggle('active', btn.dataset.mode === mode);
        });

        // Update prompt placeholder
        const prompts = {
            general: 'Describe this image or ask a question...',
            'bank-extraction': 'Bank statement will be automatically extracted',
            document: 'Ask about this document...',
            technical: 'Analyze technical aspects of this image...'
        };
        
        this.elements.promptInput.placeholder = prompts[mode] || prompts.general;
        
        // Auto-fill for bank mode
        if (mode === 'bank-extraction') {
            this.elements.promptInput.value = 'Extract all transactions from this bank statement';
        }

        // Show/hide export buttons
        const showExport = mode === 'bank-extraction';
        if (this.elements.exportCsvBtn) {
            this.elements.exportCsvBtn.style.display = showExport ? 'inline-block' : 'none';
        }
        if (this.elements.exportJsonBtn) {
            this.elements.exportJsonBtn.style.display = showExport ? 'inline-block' : 'none';
        }
    }

    handleFileSelect(event) {
        const file = event.target.files[0];
        if (file) {
            this.handleFile(file);
        }
    }

    handleFile(file) {
        if (!file.type.startsWith('image/')) {
            this.showStatus('Please select an image file', 'error');
            return;
        }

        const reader = new FileReader();
        reader.onload = (e) => {
            this.currentImage = e.target.result;
            this.displayImage(this.currentImage);
        };
        reader.readAsDataURL(file);
    }

    displayImage(imageSrc) {
        this.elements.imagePreviewImg.src = imageSrc;
        this.elements.imagePreview.style.display = 'block';
        this.elements.dropZone.style.display = 'none';
        this.elements.analyzeBtn.disabled = false;
    }

    async processImage() {
        if (!this.currentImage) {
            this.showStatus('Please select an image first', 'error');
            return;
        }

        if (this.isProcessing) return;
        
        this.isProcessing = true;
        this.elements.analyzeBtn.disabled = true;
        this.elements.analyzeBtn.textContent = 'Processing...';
        this.showStatus('Processing image...', 'info');

        try {
            const prompt = this.elements.promptInput.value || this.getDefaultPrompt();
            const imageBase64 = this.currentImage.split(',')[1];
            
            const messages = [{
                role: 'user',
                content: [
                    { type: 'text', text: prompt },
                    { type: 'image', image: imageBase64 }
                ]
            }];

            let result;
            
            if (this.currentMode === 'bank-extraction') {
                // Use bank extraction endpoint
                result = await this.api.extractBankStatement(messages, {
                    maxTokens: 4000
                });
                
                if (result.status === 'success' && result.data) {
                    this.displayBankResults(result.data);
                    this.lastBankData = result.data;
                } else {
                    throw new Error('No data extracted');
                }
            } else {
                // Use general generation endpoint
                result = await this.api.generate(messages, {
                    temperature: 0.7,
                    maxTokens: 2048
                });
                
                this.displayTextResult(result.response);
            }

            // Show metadata if available
            if (result.metadata) {
                const metaText = `Provider: ${result.metadata.provider}, Model: ${result.metadata.model || 'N/A'}`;
                this.showStatus(`Success! ${metaText}`, 'success');
            } else {
                this.showStatus('Analysis complete!', 'success');
            }

        } catch (error) {
            console.error('Processing error:', error);
            
            // Check if it's a fallback situation
            if (error.message?.includes('fallback') && this.currentProvider === 'openai') {
                const useFallback = await this.showFallbackConfirmation();
                if (useFallback) {
                    // Retry with local provider
                    await this.switchProvider('local');
                    await this.processImage();
                    return;
                }
            }
            
            this.showStatus(`Error: ${error.message}`, 'error');
            this.displayTextResult(`Error: ${error.message}`);
        } finally {
            this.isProcessing = false;
            this.elements.analyzeBtn.disabled = false;
            this.elements.analyzeBtn.textContent = 'Analyze Image';
        }
    }

    getDefaultPrompt() {
        const prompts = {
            general: 'Describe this image in detail',
            'bank-extraction': 'Extract all transactions from this bank statement',
            document: 'Analyze this document and summarize its contents',
            technical: 'Provide technical analysis of this image'
        };
        return prompts[this.currentMode] || prompts.general;
    }

    displayTextResult(text) {
        // Convert markdown to HTML for better display
        const html = this.markdownToHtml(text);
        this.elements.resultDiv.innerHTML = `<div class="result-content">${html}</div>`;
    }

    displayBankResults(data) {
        let html = '<div class="bank-results">';
        
        // Summary
        html += '<div class="bank-summary">';
        if (data.bank_name) {
            html += `<h3>${data.bank_name}</h3>`;
        }
        if (data.statement_period) {
            html += `<p>Period: ${data.statement_period}</p>`;
        }
        if (data.account_number) {
            html += `<p>Account: ${data.account_number}</p>`;
        }
        html += `<p>Total Transactions: ${data.transaction_count || data.transactions?.length || 0}</p>`;
        html += `<p>Total Debits: $${(data.total_debits || 0).toFixed(2)}</p>`;
        html += `<p>Total Credits: $${(data.total_credits || 0).toFixed(2)}</p>`;
        html += '</div>';
        
        // Transactions table
        if (data.transactions && data.transactions.length > 0) {
            html += '<table class="transactions-table">';
            html += '<thead><tr>';
            html += '<th>Date</th><th>Description</th><th>Category</th>';
            html += '<th>Debit</th><th>Credit</th><th>Balance</th>';
            html += '</tr></thead><tbody>';
            
            data.transactions.forEach(txn => {
                html += '<tr>';
                html += `<td>${txn.date}</td>`;
                html += `<td>${txn.description}</td>`;
                html += `<td>${txn.category || 'Other'}</td>`;
                html += `<td class="amount">${txn.debit ? '$' + txn.debit.toFixed(2) : '-'}</td>`;
                html += `<td class="amount">${txn.credit ? '$' + txn.credit.toFixed(2) : '-'}</td>`;
                html += `<td class="amount">$${(txn.balance || 0).toFixed(2)}</td>`;
                html += '</tr>';
            });
            
            html += '</tbody></table>';
        } else {
            html += '<p>No transactions found</p>';
        }
        
        html += '</div>';
        
        this.elements.resultDiv.innerHTML = html;
    }

    async exportResults(format) {
        if (!this.lastBankData) {
            this.showStatus('No data to export', 'error');
            return;
        }

        try {
            if (format === 'csv') {
                const csv = this.convertToCSV(this.lastBankData);
                this.downloadFile(csv, 'bank_transactions.csv', 'text/csv');
            } else {
                const json = JSON.stringify(this.lastBankData, null, 2);
                this.downloadFile(json, 'bank_transactions.json', 'application/json');
            }
            this.showStatus(`Exported as ${format.toUpperCase()}`, 'success');
        } catch (error) {
            console.error('Export error:', error);
            this.showStatus('Export failed', 'error');
        }
    }

    convertToCSV(data) {
        const headers = ['Date', 'Description', 'Category', 'Debit', 'Credit', 'Balance'];
        const rows = [headers];
        
        if (data.transactions) {
            data.transactions.forEach(txn => {
                rows.push([
                    txn.date,
                    `"${txn.description.replace(/"/g, '""')}"`,
                    txn.category || 'Other',
                    txn.debit || '',
                    txn.credit || '',
                    txn.balance || ''
                ]);
            });
        }
        
        return rows.map(row => row.join(',')).join('\n');
    }

    downloadFile(content, filename, mimeType) {
        const blob = new Blob([content], { type: mimeType });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
    }

    clearAll() {
        this.currentImage = null;
        this.lastBankData = null;
        this.elements.imagePreview.style.display = 'none';
        this.elements.dropZone.style.display = 'flex';
        this.elements.promptInput.value = '';
        this.elements.resultDiv.innerHTML = '';
        this.elements.analyzeBtn.disabled = true;
        this.showStatus('Cleared', 'info');
    }

    showStatus(message, type = 'info') {
        if (this.elements.statusBar) {
            this.elements.statusBar.textContent = message;
            this.elements.statusBar.className = `status-bar ${type}`;
            
            if (type !== 'error') {
                setTimeout(() => {
                    this.elements.statusBar.textContent = '';
                    this.elements.statusBar.className = 'status-bar';
                }, 5000);
            }
        }
    }

    async showPrivacyWarning() {
        return new Promise((resolve) => {
            if (!this.elements.privacyModal) {
                resolve(true);
                return;
            }

            const modal = this.elements.privacyModal;
            modal.style.display = 'block';
            
            const proceedBtn = modal.querySelector('.proceed-btn');
            const cancelBtn = modal.querySelector('.cancel-btn');
            
            const handleProceed = () => {
                modal.style.display = 'none';
                cleanup();
                resolve(true);
            };
            
            const handleCancel = () => {
                modal.style.display = 'none';
                cleanup();
                resolve(false);
            };
            
            const cleanup = () => {
                proceedBtn.removeEventListener('click', handleProceed);
                cancelBtn.removeEventListener('click', handleCancel);
            };
            
            proceedBtn.addEventListener('click', handleProceed);
            cancelBtn.addEventListener('click', handleCancel);
        });
    }

    async showFallbackConfirmation() {
        return new Promise((resolve) => {
            if (!this.elements.fallbackModal) {
                resolve(true);
                return;
            }

            const modal = this.elements.fallbackModal;
            modal.style.display = 'block';
            
            const yesBtn = modal.querySelector('.yes-btn');
            const noBtn = modal.querySelector('.no-btn');
            
            const handleYes = () => {
                modal.style.display = 'none';
                cleanup();
                resolve(true);
            };
            
            const handleNo = () => {
                modal.style.display = 'none';
                cleanup();
                resolve(false);
            };
            
            const cleanup = () => {
                yesBtn.removeEventListener('click', handleYes);
                noBtn.removeEventListener('click', handleNo);
            };
            
            yesBtn.addEventListener('click', handleYes);
            noBtn.addEventListener('click', handleNo);
        });
    }

    markdownToHtml(markdown) {
        // Simple markdown to HTML conversion
        let html = markdown
            .replace(/^### (.*$)/gim, '<h3>$1</h3>')
            .replace(/^## (.*$)/gim, '<h2>$1</h2>')
            .replace(/^# (.*$)/gim, '<h1>$1</h1>')
            .replace(/^\* (.+)/gim, '<li>$1</li>')
            .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
            .replace(/\*(.+?)\*/g, '<em>$1</em>')
            .replace(/\n\n/g, '</p><p>')
            .replace(/\n/g, '<br>');
        
        // Wrap lists
        html = html.replace(/(<li>.*<\/li>)/s, '<ul>$1</ul>');
        
        // Wrap in paragraphs
        if (!html.startsWith('<')) {
            html = '<p>' + html + '</p>';
        }
        
        return html;
    }

    startHealthCheck() {
        // Check health every 30 seconds
        setInterval(async () => {
            const isHealthy = await this.api.checkHealth();
            if (!isHealthy && !this.isProcessing) {
                this.showStatus('Server connection lost', 'error');
            }
        }, 30000);
    }

    startVRAMMonitoring() {
        // Update VRAM status every 10 seconds
        const updateVRAM = async () => {
            if (this.elements.vramStatus) {
                const status = await this.api.getVRAMStatus();
                if (status) {
                    this.elements.vramStatus.textContent = 
                        `VRAM: ${status.allocated_gb.toFixed(1)}GB / ${status.total_gb.toFixed(1)}GB (${status.usage_percentage.toFixed(0)}%)`;
                }
            }
        };
        
        updateVRAM();
        setInterval(updateVRAM, 10000);
    }
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    window.vlmInterface = new VLMInterface();
});