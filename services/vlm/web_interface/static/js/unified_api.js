/**
 * Unified API Client for VLM Server
 * Consolidates all API interactions using the new unified endpoints
 */

class UnifiedAPIClient {
    constructor(serverUrl = 'http://localhost:8000') {
        this.serverUrl = serverUrl;
        this.currentProvider = 'local';
    }

    /**
     * Get available providers
     */
    async getProviders() {
        try {
            const response = await fetch(`${this.serverUrl}/api/v1/providers_unified`);
            if (!response.ok) throw new Error('Failed to fetch providers');
            return await response.json();
        } catch (error) {
            console.error('Error fetching providers:', error);
            // Fallback to legacy endpoint if unified not available
            try {
                const response = await fetch(`${this.serverUrl}/api/v1/providers`);
                if (!response.ok) throw new Error('Failed to fetch providers');
                return await response.json();
            } catch {
                // Return default providers if both fail
                return {
                    local: { available: true, display_name: 'Local VLM' },
                    openai: { available: false, display_name: 'OpenAI GPT-4V' }
                };
            }
        }
    }

    /**
     * Switch provider
     */
    async switchProvider(provider) {
        try {
            const response = await fetch(`${this.serverUrl}/api/v1/switch_provider_unified`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ provider })
            });
            
            if (!response.ok) throw new Error('Failed to switch provider');
            const result = await response.json();
            
            if (result.status === 'success') {
                this.currentProvider = provider;
            }
            
            return result;
        } catch (error) {
            console.error('Error switching provider:', error);
            // Try legacy endpoint
            try {
                const response = await fetch(`${this.serverUrl}/api/v1/switch_provider`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ provider })
                });
                const result = await response.json();
                if (result.status === 'success') {
                    this.currentProvider = provider;
                }
                return result;
            } catch {
                throw error;
            }
        }
    }

    /**
     * Generate text/analyze image
     */
    async generate(messages, options = {}) {
        const payload = {
            messages,
            temperature: options.temperature || 0.7,
            max_tokens: options.maxTokens || 2048,
            ...options
        };

        try {
            // Try unified endpoint first
            const response = await fetch(`${this.serverUrl}/api/v1/generate_unified`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });

            if (!response.ok) throw new Error('Unified generate failed');
            return await response.json();
        } catch (error) {
            // Fallback to legacy endpoint
            const response = await fetch(`${this.serverUrl}/api/v1/generate`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    ...payload,
                    max_new_tokens: payload.max_tokens // Legacy uses different param name
                })
            });

            if (!response.ok) {
                const errorText = await response.text();
                throw new Error(`Generation failed: ${errorText}`);
            }

            const result = await response.json();
            // Normalize legacy response to match unified format
            return {
                response: result.response,
                metadata: {
                    provider: this.currentProvider,
                    model: result.model || 'unknown',
                    processing_time: result.processing_time
                }
            };
        }
    }

    /**
     * Extract bank statement
     */
    async extractBankStatement(messages, options = {}) {
        const payload = {
            messages,
            temperature: 0.1, // Low temperature for accuracy
            max_tokens: options.maxTokens || 4000,
            ...options
        };

        try {
            // Try LangChain endpoint first (best quality)
            const response = await fetch(`${this.serverUrl}/api/v1/bank_extract_langchain`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });

            if (!response.ok) throw new Error('LangChain extraction failed');
            const result = await response.json();
            
            // Ensure consistent format
            return {
                status: 'success',
                data: {
                    bank_name: result.bank_name,
                    account_number: result.account_number,
                    statement_period: result.statement_period,
                    transactions: result.transactions || [],
                    total_debits: result.total_debits || 0,
                    total_credits: result.total_credits || 0,
                    transaction_count: result.transactions?.length || 0
                },
                metadata: result.metadata || {
                    provider: this.currentProvider,
                    extraction_method: 'langchain'
                }
            };
        } catch (error) {
            console.warn('LangChain extraction failed, trying legacy:', error);
            
            // Fallback to legacy JSON extraction
            try {
                const response = await fetch(`${this.serverUrl}/api/v1/bank_extract_json`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        ...payload,
                        max_new_tokens: payload.max_tokens
                    })
                });

                if (!response.ok) throw new Error('Legacy extraction failed');
                const result = await response.json();
                
                // Legacy endpoint already returns in correct format
                return result;
            } catch (legacyError) {
                console.error('All extraction methods failed:', legacyError);
                throw legacyError;
            }
        }
    }

    /**
     * Export bank transactions
     */
    async exportBankTransactions(messages, format = 'csv') {
        const payload = {
            messages,
            export_format: format
        };

        const response = await fetch(`${this.serverUrl}/api/v1/bank_export`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });

        if (!response.ok) {
            throw new Error('Export failed');
        }

        if (format === 'csv') {
            return await response.text();
        } else {
            return await response.json();
        }
    }

    /**
     * Health check
     */
    async checkHealth() {
        try {
            const response = await fetch(`${this.serverUrl}/health`);
            return response.ok;
        } catch {
            return false;
        }
    }

    /**
     * Get VRAM status
     */
    async getVRAMStatus() {
        try {
            const response = await fetch(`${this.serverUrl}/vram_status`);
            if (!response.ok) return null;
            return await response.json();
        } catch {
            return null;
        }
    }
}

// Export for use in other scripts
window.UnifiedAPIClient = UnifiedAPIClient;