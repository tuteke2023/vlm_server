// Enhanced Bank Processor with VLM Classification

class BankProcessorEnhanced extends BankProcessor {
    constructor() {
        super();
        this.correctionsDb = null;
        this.loadCorrectionsDb();
    }

    async loadCorrectionsDb() {
        try {
            const response = await fetch('/transaction_corrections_db.json');
            if (response.ok) {
                this.correctionsDb = await response.json();
                console.log('Corrections database loaded');
            }
        } catch (error) {
            console.warn('Could not load corrections database:', error);
        }
    }

    async classifyWithVLM(transactions) {
        // Create enhanced prompt with corrections
        let prompt = "You are an Australian tax and accounting expert. Analyze these bank transactions.\n\n";
        
        if (this.correctionsDb) {
            prompt += "**GST RULES:**\n";
            prompt += "- GST rate is 10% in Australia\n";
            prompt += "- GST amount = Total amount ÷ 11 (for GST-inclusive prices)\n";
            prompt += "- Wages/salaries are GST-free\n";
            prompt += "- Basic groceries are mostly GST-free\n\n";
            
            prompt += "**EXAMPLES:**\n";
            const examples = this.correctionsDb.learning_examples || [];
            examples.slice(0, 3).forEach(ex => {
                prompt += `${ex.description}: ${ex.correct_classification.reasoning}\n`;
            });
            prompt += "\n";
        }
        
        prompt += `Classify these transactions with GST coding and categories.
Return a JSON array with these fields for each:
- gst_applicable: boolean
- gst_amount: number
- gst_category: string
- business_percentage: number
- category: string
- subcategory: string
- tax_deductible: boolean
- reasoning: string

Transactions:
${JSON.stringify(transactions, null, 2)}`;

        try {
            // Dynamically determine server URL
            const currentHost = window.location.hostname;
            const serverUrl = currentHost === 'localhost' || currentHost === '127.0.0.1' 
                ? 'http://localhost:8000'
                : `http://${currentHost}:8000`;
                
            const response = await fetch(`${serverUrl}/api/v1/generate`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    messages: [{
                        role: 'user',
                        content: prompt
                    }],
                    max_new_tokens: 2048,
                    temperature: 0.2
                })
            });

            if (response.ok) {
                const result = await response.json();
                return this.parseVLMResponse(result.response, transactions);
            }
        } catch (error) {
            console.error('VLM classification error:', error);
        }
        
        return transactions; // Return original if classification fails
    }

    parseVLMResponse(response, originalTransactions) {
        try {
            // Extract JSON from response
            const jsonMatch = response.match(/\[[\s\S]*\]/);
            if (jsonMatch) {
                const classifications = JSON.parse(jsonMatch[0]);
                
                // Merge classifications with original transactions
                return originalTransactions.map((trans, i) => {
                    const classification = classifications[i] || {};
                    
                    // Apply corrections
                    const corrected = this.applyCorrections(trans, classification);
                    
                    return {
                        ...trans,
                        ...corrected
                    };
                });
            }
        } catch (error) {
            console.error('Error parsing VLM response:', error);
        }
        
        return originalTransactions;
    }

    applyCorrections(transaction, classification) {
        const description = transaction.description.toLowerCase();
        const amount = transaction.debit || transaction.credit || 0;
        const isCredit = transaction.credit > 0;
        
        // Start with VLM classification
        const result = { ...classification };
        
        // Apply pattern-based corrections
        if (this.correctionsDb && this.correctionsDb.transaction_corrections) {
            for (const correction of this.correctionsDb.transaction_corrections) {
                const pattern = new RegExp(correction.pattern, 'i');
                if (pattern.test(description)) {
                    Object.assign(result, correction.corrections);
                    break;
                }
            }
        }
        
        // Validation rules
        
        // 1. Fix payroll/wages
        if (/payroll|salary|wages/i.test(description)) {
            result.gst_applicable = false;
            result.gst_amount = 0;
            result.gst_category = 'GST-free supply';
        }
        
        // 2. Fix GST calculations
        if (result.gst_applicable && amount > 0) {
            result.gst_amount = Math.round(amount / 11 * 100) / 100;
        } else {
            result.gst_amount = 0;
        }
        
        // 3. Fix category errors
        if (isCredit && result.category !== 'Income/Revenue') {
            result.category = 'Income/Revenue';
        }
        if (!isCredit && result.category === 'Income/Revenue') {
            if (/supermarket|coles|woolworths/i.test(description)) {
                result.category = 'Personal/Non-business';
                result.subcategory = 'Groceries';
                result.gst_applicable = false;
                result.gst_amount = 0;
            }
        }
        
        return result;
    }

    // Override the mock methods with VLM-powered versions
    async addGSTCoding() {
        if (!this.extractedData) {
            this.showError('Please extract statement first');
            return;
        }

        this.showInfo('Using AI to add GST coding...');
        this.updateProgressStep('process', true);
        
        try {
            // Use VLM to classify transactions
            const classified = await this.classifyWithVLM(this.extractedData.transactions);
            
            // Update transactions with GST coding
            this.extractedData.transactions = classified;
            
            // Update totals
            const totalGST = classified.reduce((sum, t) => sum + (t.gst_amount || 0), 0);
            this.extractedData.total_gst = totalGST;
            
            this.showSuccess(`GST coding added. Total GST: $${totalGST.toFixed(2)}`);
            this.displayExtractionResult(this.extractedData);
            
        } catch (error) {
            this.showError('Failed to add GST coding');
            console.error(error);
        }
    }

    async classifyTransactions() {
        if (!this.extractedData) {
            this.showError('Please extract statement first');
            return;
        }

        this.showInfo('Using AI to classify transactions...');
        
        try {
            const classified = await this.classifyWithVLM(this.extractedData.transactions);
            this.extractedData.transactions = classified;
            
            // Show category summary
            const categories = {};
            classified.forEach(t => {
                const cat = t.category || 'Uncategorized';
                categories[cat] = (categories[cat] || 0) + 1;
            });
            
            let summary = 'Categories: ';
            for (const [cat, count] of Object.entries(categories)) {
                summary += `${cat} (${count}), `;
            }
            
            this.showSuccess(summary.slice(0, -2));
            this.displayExtractionResult(this.extractedData);
            
        } catch (error) {
            this.showError('Failed to classify transactions');
            console.error(error);
        }
    }

    async businessPersonal() {
        if (!this.extractedData) {
            this.showError('Please extract statement first');
            return;
        }

        this.showInfo('Using AI to split business/personal...');
        
        try {
            const classified = await this.classifyWithVLM(this.extractedData.transactions);
            this.extractedData.transactions = classified;
            
            // Calculate totals
            let businessTotal = 0;
            let personalTotal = 0;
            
            classified.forEach(t => {
                const amount = t.debit || 0;
                const bizPercent = t.business_percentage || 0;
                businessTotal += amount * (bizPercent / 100);
                personalTotal += amount * ((100 - bizPercent) / 100);
            });
            
            this.showSuccess(`Business: $${businessTotal.toFixed(2)}, Personal: $${personalTotal.toFixed(2)}`);
            this.displayExtractionResult(this.extractedData);
            
        } catch (error) {
            this.showError('Failed to split transactions');
            console.error(error);
        }
    }

    // Enhanced CSV export with all classifications
    convertToCSV(transactions) {
        const headers = [
            'Date', 'Description', 'Reference', 
            'Debit', 'Credit', 'Balance',
            'GST Amount', 'GST Category',
            'Category', 'Subcategory',
            'Business %', 'Tax Deductible'
        ];
        
        const rows = transactions.map(t => [
            t.date,
            t.description,
            t.reference || '',
            t.debit || '',
            t.credit || '',
            t.balance || '',
            t.gst_amount || 0,
            t.gst_category || '',
            t.category || '',
            t.subcategory || '',
            t.business_percentage || 0,
            t.tax_deductible ? 'Yes' : 'No'
        ]);
        
        // Add headers
        const csv = [headers, ...rows].map(row => 
            row.map(cell => {
                const str = String(cell);
                return str.includes(',') || str.includes('"') 
                    ? `"${str.replace(/"/g, '""')}"` 
                    : str;
            }).join(',')
        ).join('\n');
        
        return csv;
    }
}

// Use the enhanced version
window.bankProcessor = new BankProcessorEnhanced();