/**
 * Unified VLM Interface - Styled Version
 * Maintains the beautiful block-based UI while using unified API
 */

class UnifiedVLMInterface {
    constructor() {
        // Initialize API client
        this.api = new UnifiedAPIClient('http://localhost:8000');
        
        // State
        this.currentMode = 'bank-extraction';
        this.currentImage = null;
        this.lastResults = null;
        this.hasShownPrivacyWarning = false;
        this.isProcessing = false;
        
        // Mode configurations
        this.modeConfigs = {
            'bank-extraction': {
                title: 'Bank Statement Extraction',
                icon: 'fa-credit-card',
                description: 'Upload bank statements to extract and analyze transaction data',
                prompt: 'Extract all transactions from this bank statement',
                showExport: true,
                options: `
                    <h4>Extraction Options</h4>
                    <div class="options-grid">
                        <label class="option-item">
                            <input type="checkbox" id="extractDates" checked>
                            <span>Transaction Dates</span>
                        </label>
                        <label class="option-item">
                            <input type="checkbox" id="extractAmounts" checked>
                            <span>Amounts & Balances</span>
                        </label>
                        <label class="option-item">
                            <input type="checkbox" id="categorizeTransactions" checked>
                            <span>Auto-Categorize</span>
                        </label>
                        <label class="option-item">
                            <input type="checkbox" id="detectMerchants" checked>
                            <span>Detect Merchants</span>
                        </label>
                    </div>
                `,
                suggestions: [
                    'Include transaction categories',
                    'Group by merchant',
                    'Calculate monthly totals',
                    'Identify recurring payments'
                ]
            },
            'general': {
                title: 'General Image Analysis',
                icon: 'fa-image',
                description: 'Analyze and describe any image with AI',
                prompt: 'Describe this image in detail',
                showExport: false,
                options: `
                    <h4>Analysis Options</h4>
                    <div class="options-grid">
                        <label class="option-item">
                            <input type="checkbox" id="detailedAnalysis" checked>
                            <span>Detailed Description</span>
                        </label>
                        <label class="option-item">
                            <input type="checkbox" id="detectObjects" checked>
                            <span>Object Detection</span>
                        </label>
                        <label class="option-item">
                            <input type="checkbox" id="analyzeColors">
                            <span>Color Analysis</span>
                        </label>
                        <label class="option-item">
                            <input type="checkbox" id="extractText">
                            <span>Extract Any Text</span>
                        </label>
                    </div>
                `,
                suggestions: [
                    'What objects are in this image?',
                    'Describe the mood or atmosphere',
                    'What is the main subject?',
                    'Analyze the composition'
                ]
            },
            'document': {
                title: 'Document Summarization',
                icon: 'fa-file-alt',
                description: 'Get AI-powered summaries and insights from documents',
                prompt: 'Summarize this document',
                showExport: false,
                options: `
                    <h4>Summary Options</h4>
                    <div class="options-grid">
                        <label class="option-item">
                            <input type="checkbox" id="executiveSummary" checked>
                            <span>Executive Summary</span>
                        </label>
                        <label class="option-item">
                            <input type="checkbox" id="keyPoints" checked>
                            <span>Key Points</span>
                        </label>
                        <label class="option-item">
                            <input type="checkbox" id="actionItems">
                            <span>Action Items</span>
                        </label>
                        <label class="option-item">
                            <input type="checkbox" id="sentiment">
                            <span>Sentiment Analysis</span>
                        </label>
                    </div>
                `,
                suggestions: [
                    'What are the main points?',
                    'Extract key dates and deadlines',
                    'Who are the stakeholders?',
                    'What decisions need to be made?'
                ]
            },
            'technical': {
                title: 'Technical Analysis',
                icon: 'fa-code',
                description: 'Analyze technical diagrams, code screenshots, and architecture',
                prompt: 'Analyze the technical aspects of this image',
                showExport: false,
                options: `
                    <h4>Analysis Options</h4>
                    <div class="options-grid">
                        <label class="option-item">
                            <input type="checkbox" id="codeAnalysis" checked>
                            <span>Code Analysis</span>
                        </label>
                        <label class="option-item">
                            <input type="checkbox" id="architecture" checked>
                            <span>Architecture Review</span>
                        </label>
                        <label class="option-item">
                            <input type="checkbox" id="suggestions">
                            <span>Improvement Suggestions</span>
                        </label>
                        <label class="option-item">
                            <input type="checkbox" id="security">
                            <span>Security Considerations</span>
                        </label>
                    </div>
                `,
                suggestions: [
                    'Explain this code',
                    'What design pattern is this?',
                    'Identify potential issues',
                    'Suggest optimizations'
                ]
            },
            'custom': {
                title: 'Custom Query',
                icon: 'fa-question-circle',
                description: 'Ask anything about the uploaded image',
                prompt: '',
                showExport: false,
                options: `
                    <h4>Query Type</h4>
                    <div class="options-grid">
                        <label class="option-item">
                            <input type="radio" name="queryType" value="analysis" checked>
                            <span>Analysis</span>
                        </label>
                        <label class="option-item">
                            <input type="radio" name="queryType" value="extraction">
                            <span>Data Extraction</span>
                        </label>
                        <label class="option-item">
                            <input type="radio" name="queryType" value="comparison">
                            <span>Comparison</span>
                        </label>
                        <label class="option-item">
                            <input type="radio" name="queryType" value="creative">
                            <span>Creative</span>
                        </label>
                    </div>
                `,
                suggestions: [
                    'What questions can I answer about this image?',
                    'Extract specific information',
                    'Compare with best practices',
                    'Generate ideas based on this'
                ]
            }
        };
        
        // Initialize
        this.init();
    }

    async init() {
        // Cache DOM elements
        this.cacheElements();
        
        // Set up event listeners
        this.setupEventListeners();
        
        // Initialize mode
        this.setMode(this.currentMode);
        
        // Load providers
        await this.loadProviders();
        
        // Start monitoring
        this.startMonitoring();
        
        // Update audio link
        this.updateAudioLink();
    }

    cacheElements() {
        // Menu items
        this.menuItems = document.querySelectorAll('.menu-item');
        
        // Mode elements
        this.modeIcon = document.getElementById('modeIcon');
        this.modeTitle = document.getElementById('modeTitle');
        this.modeDescription = document.getElementById('modeDescription');
        this.processingOptions = document.getElementById('processingOptions');
        this.promptSuggestions = document.getElementById('promptSuggestions');
        
        // Upload elements
        this.uploadArea = document.getElementById('unifiedUploadArea');
        this.fileInput = document.getElementById('fileInput');
        this.imagePreview = document.getElementById('imagePreview');
        this.imagePreviewImg = document.getElementById('imagePreviewImg');
        
        // Input elements
        this.promptInput = document.getElementById('promptInput');
        this.analyzeBtn = document.getElementById('analyzeBtn');
        
        // Results
        this.resultsSection = document.getElementById('resultsSection');
        this.resultsContent = document.getElementById('resultsContent');
        
        // Export buttons
        this.exportButtons = document.getElementById('exportButtons');
        this.exportCsvBtn = document.getElementById('exportCsvBtn');
        this.exportJsonBtn = document.getElementById('exportJsonBtn');
        this.exportResultsBtn = document.getElementById('exportResultsBtn');
        
        // Provider elements
        this.providerSelect = document.getElementById('providerSelect');
        this.providerIndicator = document.getElementById('providerIndicator');
        this.activeProviderName = document.getElementById('activeProviderName');
        this.activeProviderModel = document.getElementById('activeProviderModel');
        
        // Status elements
        this.serverStatus = document.getElementById('serverStatus');
        this.vramBar = document.getElementById('vramBar');
        this.vramText = document.getElementById('vramText');
        this.vramDetails = document.getElementById('vramDetails');
        this.statusMessage = document.getElementById('statusMessage');
        
        // Modals
        this.privacyModal = document.getElementById('privacyWarningModal');
        this.fallbackModal = document.getElementById('fallbackConfirmModal');
        
        // Buttons
        this.clearAllBtn = document.getElementById('clearAllBtn');
        this.changeImageBtn = document.getElementById('changeImageBtn');
        this.clearResultsBtn = document.getElementById('clearResultsBtn');
    }

    setupEventListeners() {
        // Mode selection
        this.menuItems.forEach(item => {
            item.addEventListener('click', () => {
                const mode = item.dataset.mode;
                if (mode) this.setMode(mode);
            });
        });

        // File upload
        this.uploadArea.addEventListener('click', () => this.fileInput.click());
        this.fileInput.addEventListener('change', (e) => this.handleFileSelect(e));
        
        // Drag and drop
        this.uploadArea.addEventListener('dragover', (e) => {
            e.preventDefault();
            this.uploadArea.classList.add('drag-over');
        });
        
        this.uploadArea.addEventListener('dragleave', () => {
            this.uploadArea.classList.remove('drag-over');
        });
        
        this.uploadArea.addEventListener('drop', (e) => {
            e.preventDefault();
            this.uploadArea.classList.remove('drag-over');
            if (e.dataTransfer.files.length > 0) {
                this.handleFile(e.dataTransfer.files[0]);
            }
        });

        // Buttons
        this.analyzeBtn.addEventListener('click', () => this.analyzeImage());
        this.clearAllBtn.addEventListener('click', () => this.clearAll());
        if (this.changeImageBtn) {
            this.changeImageBtn.addEventListener('click', () => this.changeImage());
        }
        if (this.clearResultsBtn) {
            this.clearResultsBtn.addEventListener('click', () => this.clearResults());
        }

        // Export buttons
        if (this.exportCsvBtn) {
            this.exportCsvBtn.addEventListener('click', () => this.exportResults('csv'));
        }
        if (this.exportJsonBtn) {
            this.exportJsonBtn.addEventListener('click', () => this.exportResults('json'));
        }
        if (this.exportResultsBtn) {
            this.exportResultsBtn.addEventListener('click', () => this.exportCurrentResults());
        }

        // Provider selection
        this.providerSelect.addEventListener('change', (e) => this.switchProvider(e.target.value));

        // Prompt suggestions
        this.promptSuggestions.addEventListener('click', (e) => {
            if (e.target.classList.contains('suggestion')) {
                this.promptInput.value = e.target.textContent;
            }
        });

        // Enter key in prompt
        this.promptInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter' && !e.shiftKey && !this.isProcessing) {
                e.preventDefault();
                this.analyzeImage();
            }
        });
    }

    setMode(mode) {
        // Update active menu item
        this.menuItems.forEach(item => {
            item.classList.toggle('active', item.dataset.mode === mode);
        });

        // Get mode config
        const config = this.modeConfigs[mode];
        if (!config) return;

        this.currentMode = mode;

        // Update UI
        this.modeIcon.className = `fas ${config.icon}`;
        this.modeTitle.textContent = config.title;
        this.modeDescription.textContent = config.description;
        
        // Update options
        this.processingOptions.innerHTML = config.options;
        
        // Update prompt - always update when switching modes
        this.promptInput.placeholder = config.prompt || 'Enter your question or instructions...';
        
        // Always set the default prompt for the mode
        // User can still modify it if they want something different
        this.promptInput.value = config.prompt || '';
        
        // Update suggestions
        this.updatePromptSuggestions(config.suggestions);
        
        // Show/hide export buttons
        this.exportButtons.style.display = config.showExport ? 'block' : 'none';
        this.exportResultsBtn.style.display = config.showExport ? 'block' : 'none';
    }

    updatePromptSuggestions(suggestions) {
        this.promptSuggestions.innerHTML = suggestions
            .map(s => `<span class="suggestion">${s}</span>`)
            .join('');
    }

    handleFileSelect(event) {
        const file = event.target.files[0];
        if (file) this.handleFile(file);
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
        this.imagePreviewImg.src = imageSrc;
        this.imagePreview.style.display = 'block';
        this.uploadArea.style.display = 'none';
        this.analyzeBtn.disabled = false;
    }

    changeImage() {
        this.fileInput.click();
    }

    async analyzeImage() {
        if (!this.currentImage || this.isProcessing) return;

        this.isProcessing = true;
        this.analyzeBtn.disabled = true;
        this.analyzeBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Processing...';
        this.showStatus('Processing image...', 'info');

        try {
            const prompt = this.promptInput.value || this.modeConfigs[this.currentMode].prompt;
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
                    this.lastResults = result.data;
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
                this.lastResults = { text: result.response };
            }

            // Show success and update provider display
            const provider = result.metadata?.provider || result.data?.metadata?.provider || 'unknown';
            this.showStatus(`Analysis complete! (Provider: ${provider})`, 'success');
            
            // Update provider display if it differs from UI
            if (provider !== 'unknown' && provider !== this.api.currentProvider) {
                console.warn(`Provider mismatch: UI shows ${this.api.currentProvider}, server used ${provider}`);
                // Sync UI with actual provider used
                this.api.currentProvider = provider;
                this.providerSelect.value = provider;
                this.updateProviderStatus();
            }
            
            // Show results section
            this.resultsSection.style.display = 'block';
            
            // Scroll to results
            this.resultsSection.scrollIntoView({ behavior: 'smooth', block: 'start' });

        } catch (error) {
            console.error('Processing error:', error);
            
            // Check for fallback
            if (error.message?.includes('fallback') && this.api.currentProvider === 'openai') {
                const useFallback = await this.showFallbackConfirmation();
                if (useFallback) {
                    await this.switchProvider('local');
                    await this.analyzeImage();
                    return;
                }
            }
            
            this.showStatus(`Error: ${error.message}`, 'error');
        } finally {
            this.isProcessing = false;
            this.analyzeBtn.disabled = false;
            this.analyzeBtn.innerHTML = '<i class="fas fa-play-circle"></i> Analyze Image';
        }
    }

    displayBankResults(data) {
        let html = '<div class="bank-results-container">';
        
        // Summary card
        html += '<div class="result-card summary-card">';
        html += '<div class="card-header">';
        html += '<h3><i class="fas fa-chart-pie"></i> Summary</h3>';
        html += '</div>';
        html += '<div class="card-body">';
        
        if (data.bank_name) {
            html += `<div class="summary-item"><strong>Bank:</strong> ${data.bank_name}</div>`;
        }
        if (data.statement_period) {
            html += `<div class="summary-item"><strong>Period:</strong> ${data.statement_period}</div>`;
        }
        if (data.account_number) {
            html += `<div class="summary-item"><strong>Account:</strong> ${data.account_number}</div>`;
        }
        
        html += '<div class="summary-stats">';
        html += `<div class="stat-item">
            <span class="stat-label">Transactions</span>
            <span class="stat-value">${data.transaction_count || data.transactions?.length || 0}</span>
        </div>`;
        html += `<div class="stat-item">
            <span class="stat-label">Total Debits</span>
            <span class="stat-value debit">$${(data.total_debits || 0).toFixed(2)}</span>
        </div>`;
        html += `<div class="stat-item">
            <span class="stat-label">Total Credits</span>
            <span class="stat-value credit">$${(data.total_credits || 0).toFixed(2)}</span>
        </div>`;
        html += '</div>';
        
        html += '</div>';
        html += '</div>';
        
        // Transactions table
        if (data.transactions && data.transactions.length > 0) {
            html += '<div class="result-card transactions-card">';
            html += '<div class="card-header">';
            html += '<h3><i class="fas fa-list"></i> Transactions</h3>';
            html += '</div>';
            html += '<div class="card-body">';
            html += '<div class="table-responsive">';
            html += '<table class="data-table">';
            html += '<thead><tr>';
            html += '<th>Date</th><th>Description</th><th>Category</th>';
            html += '<th class="text-right">Debit</th><th class="text-right">Credit</th><th class="text-right">Balance</th>';
            html += '</tr></thead><tbody>';
            
            data.transactions.forEach(txn => {
                html += '<tr>';
                html += `<td>${txn.date}</td>`;
                html += `<td>${txn.description}</td>`;
                html += `<td><span class="category-tag">${txn.category || 'Other'}</span></td>`;
                html += `<td class="text-right debit">${txn.debit ? '$' + txn.debit.toFixed(2) : '-'}</td>`;
                html += `<td class="text-right credit">${txn.credit ? '$' + txn.credit.toFixed(2) : '-'}</td>`;
                html += `<td class="text-right balance">$${(txn.balance || 0).toFixed(2)}</td>`;
                html += '</tr>';
            });
            
            html += '</tbody></table>';
            html += '</div>';
            html += '</div>';
            html += '</div>';
        }
        
        html += '</div>';
        
        this.resultsContent.innerHTML = html;
    }

    displayTextResult(text) {
        // Convert markdown to HTML
        const html = this.markdownToHtml(text);
        
        this.resultsContent.innerHTML = `
            <div class="result-card text-result">
                <div class="card-body">
                    <div class="formatted-text">${html}</div>
                </div>
            </div>
        `;
    }

    markdownToHtml(markdown) {
        let html = markdown
            .replace(/^### (.*$)/gim, '<h3>$1</h3>')
            .replace(/^## (.*$)/gim, '<h2>$1</h2>')
            .replace(/^# (.*$)/gim, '<h1>$1</h1>')
            .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
            .replace(/\*(.+?)\*/g, '<em>$1</em>')
            .replace(/```([\s\S]*?)```/g, '<pre><code>$1</code></pre>')
            .replace(/`(.+?)`/g, '<code>$1</code>')
            .replace(/^\* (.+)/gim, '<li>$1</li>')
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

    async exportResults(format) {
        if (!this.lastResults || this.currentMode !== 'bank-extraction') {
            this.showStatus('No data to export', 'error');
            return;
        }

        try {
            if (format === 'csv') {
                const csv = this.convertToCSV(this.lastResults);
                this.downloadFile(csv, 'bank_transactions.csv', 'text/csv');
            } else {
                const json = JSON.stringify(this.lastResults, null, 2);
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
                    `"${(txn.description || '').replace(/"/g, '""')}"`,
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
        this.lastResults = null;
        this.imagePreview.style.display = 'none';
        this.uploadArea.style.display = 'block';
        this.promptInput.value = this.modeConfigs[this.currentMode].prompt || '';
        this.resultsSection.style.display = 'none';
        this.resultsContent.innerHTML = '';
        this.analyzeBtn.disabled = true;
        this.fileInput.value = '';
        this.showStatus('Cleared all data', 'info');
    }

    clearResults() {
        this.resultsSection.style.display = 'none';
        this.resultsContent.innerHTML = '';
        this.lastResults = null;
    }

    exportCurrentResults() {
        if (this.currentMode === 'bank-extraction' && this.lastResults) {
            this.exportResults('csv');
        } else if (this.lastResults?.text) {
            const content = this.lastResults.text;
            this.downloadFile(content, 'analysis_results.txt', 'text/plain');
            this.showStatus('Exported results', 'success');
        } else {
            this.showStatus('No results to export', 'error');
        }
    }

    async loadProviders() {
        try {
            const providers = await this.api.getProviders();
            
            this.providerSelect.innerHTML = '';
            for (const [key, info] of Object.entries(providers)) {
                const option = document.createElement('option');
                option.value = key;
                option.textContent = info.display_name;
                option.disabled = !info.available;
                if (!info.available) {
                    option.textContent += ' (Unavailable)';
                }
                this.providerSelect.appendChild(option);
            }
            
            // Update current provider info
            this.updateProviderStatus();
        } catch (error) {
            console.error('Failed to load providers:', error);
        }
    }

    async switchProvider(provider) {
        // Show privacy warning for OpenAI if not shown
        if (provider === 'openai' && !this.hasShownPrivacyWarning) {
            const proceed = await this.showPrivacyWarning();
            if (!proceed) {
                this.providerSelect.value = this.api.currentProvider;
                return;
            }
            this.hasShownPrivacyWarning = true;
        }

        try {
            const result = await this.api.switchProvider(provider);
            
            if (result.status === 'success') {
                this.updateProviderStatus();
                this.showStatus(`Switched to ${provider}`, 'success');
            } else {
                throw new Error(result.message || 'Failed to switch provider');
            }
        } catch (error) {
            console.error('Provider switch failed:', error);
            this.showStatus(`Failed to switch provider: ${error.message}`, 'error');
            this.providerSelect.value = this.api.currentProvider;
        }
    }

    updateProviderStatus() {
        const provider = this.api.currentProvider;
        const isOpenAI = provider === 'openai';
        
        // Update indicator
        this.providerIndicator.className = `provider-indicator ${provider}`;
        this.providerIndicator.innerHTML = isOpenAI 
            ? '<i class="fas fa-cloud"></i><span>OpenAI</span>'
            : '<i class="fas fa-lock"></i><span>Local</span>';
        
        // Update status panel
        this.activeProviderName.textContent = isOpenAI ? 'OpenAI GPT-4V' : 'Local VLM';
        this.activeProviderModel.textContent = isOpenAI ? 'gpt-4-vision-preview' : 'Qwen2.5-VL-3B';
    }

    showStatus(message, type = 'info') {
        this.statusMessage.textContent = message;
        this.statusMessage.className = `status-message ${type} show`;
        
        setTimeout(() => {
            this.statusMessage.classList.remove('show');
        }, 5000);
    }

    async showPrivacyWarning() {
        return new Promise((resolve) => {
            this.privacyModal.style.display = 'block';
            
            const proceedBtn = this.privacyModal.querySelector('.proceed-btn');
            const cancelBtn = this.privacyModal.querySelector('.cancel-btn');
            
            const handleProceed = () => {
                this.privacyModal.style.display = 'none';
                cleanup();
                resolve(true);
            };
            
            const handleCancel = () => {
                this.privacyModal.style.display = 'none';
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
            this.fallbackModal.style.display = 'block';
            
            const yesBtn = this.fallbackModal.querySelector('.yes-btn');
            const noBtn = this.fallbackModal.querySelector('.no-btn');
            
            const handleYes = () => {
                this.fallbackModal.style.display = 'none';
                cleanup();
                resolve(true);
            };
            
            const handleNo = () => {
                this.fallbackModal.style.display = 'none';
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

    startMonitoring() {
        // Update server status
        this.updateServerStatus();
        setInterval(() => this.updateServerStatus(), 30000);
        
        // Update VRAM status
        this.updateVRAMStatus();
        setInterval(() => this.updateVRAMStatus(), 10000);
    }

    async updateServerStatus() {
        const isHealthy = await this.api.checkHealth();
        const statusDot = this.serverStatus.querySelector('.status-dot');
        const statusText = this.serverStatus.querySelector('.status-text');
        
        if (isHealthy) {
            statusDot.className = 'status-dot online';
            statusText.textContent = 'Connected';
        } else {
            statusDot.className = 'status-dot offline';
            statusText.textContent = 'Disconnected';
        }
    }

    async updateVRAMStatus() {
        const status = await this.api.getVRAMStatus();
        if (status) {
            const percentage = status.usage_percentage;
            this.vramBar.style.width = `${percentage}%`;
            this.vramBar.className = `vram-fill ${percentage > 90 ? 'critical' : percentage > 70 ? 'warning' : 'normal'}`;
            this.vramText.textContent = `${percentage.toFixed(0)}%`;
            this.vramDetails.textContent = `${status.allocated_gb.toFixed(1)}GB / ${status.total_gb.toFixed(1)}GB`;
        }
    }

    updateAudioLink() {
        const audioLink = document.getElementById('audioTranscriptionLink');
        if (audioLink) {
            audioLink.href = 'http://localhost:8002';
        }
    }
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    window.unifiedInterface = new UnifiedVLMInterface();
});