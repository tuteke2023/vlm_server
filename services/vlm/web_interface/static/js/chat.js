/**
 * VLM Chat Interface
 * Clean, conversational interface for the Vision Language Model
 */

class VLMChat {
    constructor() {
        // Dynamically determine server URL based on current location
        const currentHost = window.location.hostname;
        this.serverUrl = currentHost === 'localhost' || currentHost === '127.0.0.1' 
            ? 'http://localhost:8000'
            : `http://${currentHost}:8000`;
            
        this.messages = [];
        this.uploadedFiles = new Map();
        this.isProcessing = false;
        
        this.init();
    }
    
    init() {
        this.setupEventListeners();
        this.checkServerStatus();
        this.updateModelInfo();
        this.setWelcomeTime();
        
        // Update server status every 30 seconds
        setInterval(() => {
            this.checkServerStatus();
            this.updateModelInfo();
        }, 30000);
        
        // Auto-resize textarea
        this.setupTextareaAutoResize();
    }
    
    setupEventListeners() {
        // Send button
        document.getElementById('sendBtn').addEventListener('click', () => {
            this.sendMessage();
        });
        
        // Enter key to send (but Shift+Enter for new line)
        document.getElementById('messageInput').addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                this.sendMessage();
            }
        });
        
        // File upload
        document.getElementById('imageUploadBtn').addEventListener('click', () => {
            document.getElementById('imageFileInput').click();
        });
        
        document.getElementById('imageFileInput').addEventListener('change', (e) => {
            this.handleFileUpload(e.target.files);
        });
        
        // Quick actions
        document.getElementById('clearChatBtn').addEventListener('click', () => {
            this.clearChat();
        });
        
        document.getElementById('exportChatBtn').addEventListener('click', () => {
            this.exportChat();
        });
        
        document.getElementById('clearVramBtn').addEventListener('click', () => {
            this.clearVram();
        });
        
        // Drag and drop for images
        const messagesContainer = document.getElementById('messagesContainer');
        messagesContainer.addEventListener('dragover', (e) => {
            e.preventDefault();
            messagesContainer.style.backgroundColor = 'rgba(102, 126, 234, 0.05)';
        });
        
        messagesContainer.addEventListener('dragleave', (e) => {
            e.preventDefault();
            messagesContainer.style.backgroundColor = '';
        });
        
        messagesContainer.addEventListener('drop', (e) => {
            e.preventDefault();
            messagesContainer.style.backgroundColor = '';
            this.handleFileUpload(e.dataTransfer.files);
        });
    }
    
    setupTextareaAutoResize() {
        const textarea = document.getElementById('messageInput');
        textarea.addEventListener('input', () => {
            textarea.style.height = 'auto';
            textarea.style.height = Math.min(textarea.scrollHeight, 120) + 'px';
        });
    }
    
    setWelcomeTime() {
        const welcomeTimeElement = document.getElementById('welcomeTime');
        welcomeTimeElement.textContent = new Date().toLocaleTimeString();
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
    
    async updateModelInfo() {
        try {
            const [modelsResponse, vramResponse] = await Promise.all([
                fetch(`${this.serverUrl}/available_models`),
                fetch(`${this.serverUrl}/vram_status`)
            ]);
            
            const models = await modelsResponse.json();
            const vramData = await vramResponse.json();
            
            const currentModel = models.find(m => m.is_current);
            if (currentModel) {
                document.getElementById('currentModel').textContent = currentModel.size;
            }
            
            const vramUsage = `${vramData.usage_percentage.toFixed(1)}%`;
            document.getElementById('vramUsage').textContent = vramUsage;
            
            // Update VRAM bar
            const vramBar = document.getElementById('vramBar');
            vramBar.style.width = `${vramData.usage_percentage}%`;
            vramBar.className = 'vram-fill';
            if (vramData.usage_percentage >= 90) {
                vramBar.classList.add('danger');
            } else if (vramData.usage_percentage >= 75) {
                vramBar.classList.add('warning');
            }
            
            // Update status
            const statusText = vramData.usage_percentage < 80 ? 'Ready' : 
                             vramData.usage_percentage < 90 ? 'High Usage' : 'Critical';
            document.getElementById('modelStatus').textContent = statusText;
            
        } catch (error) {
            console.error('Failed to update model info:', error);
        }
    }
    
    handleFileUpload(files) {
        const fileArray = Array.from(files);
        
        fileArray.forEach(file => {
            if (this.validateFile(file)) {
                this.uploadedFiles.set(file.name, file);
            }
        });
        
        this.displayUploadedFiles();
    }
    
    validateFile(file) {
        const maxSize = 10 * 1024 * 1024; // 10MB
        const allowedTypes = ['image/png', 'image/jpeg', 'image/jpg', 'image/gif'];
        
        if (file.size > maxSize) {
            this.showToast('File too large. Maximum size is 10MB.', 'error');
            return false;
        }
        
        if (!allowedTypes.includes(file.type)) {
            this.showToast('Only image files are supported in chat.', 'error');
            return false;
        }
        
        return true;
    }
    
    displayUploadedFiles() {
        const container = document.getElementById('uploadedFiles');
        container.innerHTML = '';
        
        this.uploadedFiles.forEach((file, fileName) => {
            const fileTag = document.createElement('div');
            fileTag.className = 'file-tag';
            fileTag.innerHTML = `
                <i class="fas fa-image"></i>
                <span>${fileName}</span>
                <button class="file-remove" onclick="chat.removeFile('${fileName}')">
                    <i class="fas fa-times"></i>
                </button>
            `;
            container.appendChild(fileTag);
        });
    }
    
    removeFile(fileName) {
        this.uploadedFiles.delete(fileName);
        this.displayUploadedFiles();
    }
    
    async sendMessage() {
        const messageInput = document.getElementById('messageInput');
        const messageText = messageInput.value.trim();
        
        // Don't send empty messages unless there are files
        if (!messageText && this.uploadedFiles.size === 0) {
            return;
        }
        
        if (this.isProcessing) {
            this.showToast('Please wait for the previous message to complete.', 'warning');
            return;
        }
        
        // Create user message
        const userMessage = {
            role: 'user',
            content: [],
            timestamp: new Date()
        };
        
        // Add images first
        for (const [fileName, file] of this.uploadedFiles) {
            const base64 = await this.fileToBase64(file);
            userMessage.content.push({
                type: 'image',
                image: base64
            });
        }
        
        // Add text if provided
        if (messageText) {
            userMessage.content.push({
                type: 'text',
                text: messageText
            });
        }
        
        // Add message to chat
        this.addMessageToChat(userMessage);
        
        // Clear input and files
        messageInput.value = '';
        messageInput.style.height = 'auto';
        this.uploadedFiles.clear();
        this.displayUploadedFiles();
        
        // Send to API
        await this.processMessage(userMessage);
    }
    
    addMessageToChat(message) {
        const messagesContainer = document.getElementById('messagesContainer');
        const messageElement = document.createElement('div');
        messageElement.className = `message ${message.role}`;
        
        const avatarIcon = message.role === 'user' ? 'fa-user' : 'fa-robot';
        const timeString = message.timestamp.toLocaleTimeString();
        
        let contentHtml = '';
        
        if (Array.isArray(message.content)) {
            message.content.forEach(item => {
                if (item.type === 'image') {
                    contentHtml += `<img src="${item.image}" class="message-image" alt="Uploaded image">`;
                } else if (item.type === 'text') {
                    contentHtml += `<div>${this.formatText(item.text)}</div>`;
                }
            });
        } else {
            contentHtml = this.formatText(message.content);
        }
        
        messageElement.innerHTML = `
            <div class="message-avatar">
                <i class="fas ${avatarIcon}"></i>
            </div>
            <div class="message-content">
                <div class="message-bubble">
                    ${contentHtml}
                </div>
                <div class="message-time">${timeString}</div>
            </div>
        `;
        
        messagesContainer.appendChild(messageElement);
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
        
        this.messages.push(message);
        this.updateConversationStatus();
    }
    
    formatText(text) {
        // Simple text formatting - preserve line breaks and make URLs clickable
        return text
            .replace(/\n/g, '<br>')
            .replace(/(https?:\/\/[^\s]+)/g, '<a href="$1" target="_blank">$1</a>');
    }
    
    showTypingIndicator() {
        const messagesContainer = document.getElementById('messagesContainer');
        const typingElement = document.createElement('div');
        typingElement.className = 'typing-indicator';
        typingElement.id = 'typingIndicator';
        
        typingElement.innerHTML = `
            <div class="message-avatar">
                <i class="fas fa-robot"></i>
            </div>
            <div class="message-content">
                <div class="typing-dots">
                    <div class="typing-dot"></div>
                    <div class="typing-dot"></div>
                    <div class="typing-dot"></div>
                </div>
            </div>
        `;
        
        messagesContainer.appendChild(typingElement);
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }
    
    hideTypingIndicator() {
        const typingElement = document.getElementById('typingIndicator');
        if (typingElement) {
            typingElement.remove();
        }
    }
    
    buildConversationHistory(currentUserMessage) {
        const conversationMessages = [];
        
        // Add all previous messages from this session for context
        this.messages.forEach(msg => {
            conversationMessages.push({
                role: msg.role,
                content: this.formatMessageForAPI(msg.content)
            });
        });
        
        // Add the current user message
        conversationMessages.push({
            role: currentUserMessage.role,
            content: this.formatMessageForAPI(currentUserMessage.content)
        });
        
        // Limit conversation history to prevent token overflow
        // Keep last 10 exchanges (20 messages) for context
        const maxMessages = 20;
        if (conversationMessages.length > maxMessages) {
            // Keep the first message (if it's a system message) and recent messages
            const recentMessages = conversationMessages.slice(-maxMessages);
            return recentMessages;
        }
        
        return conversationMessages;
    }
    
    formatMessageForAPI(content) {
        // If content is already in API format (array), return as-is
        if (Array.isArray(content)) {
            return content;
        }
        
        // If content is a string, convert to API format
        if (typeof content === 'string') {
            return [
                {
                    type: 'text',
                    text: content
                }
            ];
        }
        
        // Fallback
        return content;
    }
    
    updateConversationStatus() {
        const statusElement = document.getElementById('conversationStatus');
        if (statusElement) {
            const messageCount = this.messages.length;
            const contextInfo = messageCount > 0 
                ? `💬 Conversation context: ${messageCount} messages (AI remembers this session)`
                : `💬 Conversation context: 0 messages`;
            statusElement.textContent = contextInfo;
        }
    }
    
    async processMessage(userMessage) {
        this.isProcessing = true;
        this.updateSendButton(true);
        this.showTypingIndicator();
        
        try {
            // Build conversation history for context
            const conversationMessages = this.buildConversationHistory(userMessage);
            
            const response = await fetch(`${this.serverUrl}/api/v1/generate`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    messages: conversationMessages,
                    max_new_tokens: 512,
                    temperature: 0.7,
                    enable_safety_check: true
                })
            });
            
            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || `Server error: ${response.status}`);
            }
            
            const result = await response.json();
            
            // Add assistant response
            const assistantMessage = {
                role: 'assistant',
                content: result.response,
                timestamp: new Date()
            };
            
            this.hideTypingIndicator();
            this.addMessageToChat(assistantMessage);
            
        } catch (error) {
            console.error('Error processing message:', error);
            this.hideTypingIndicator();
            
            let errorMessage = 'Sorry, I encountered an error processing your message.';
            if (error.message.includes('VRAM safety check failed')) {
                errorMessage = 'VRAM usage is too high. Try switching to the 3B model or clearing VRAM.';
            } else if (error.message.includes('failed to fetch')) {
                errorMessage = 'Cannot connect to the server. Please check if the VLM server is running.';
            }
            
            const errorResponse = {
                role: 'assistant',
                content: `❌ ${errorMessage}`,
                timestamp: new Date()
            };
            
            this.addMessageToChat(errorResponse);
            this.showToast(error.message, 'error');
            
        } finally {
            this.isProcessing = false;
            this.updateSendButton(false);
            
            // Update model info after processing
            setTimeout(() => {
                this.updateModelInfo();
            }, 1000);
        }
    }
    
    updateSendButton(isProcessing) {
        const sendBtn = document.getElementById('sendBtn');
        const icon = sendBtn.querySelector('i');
        const text = sendBtn.querySelector('span');
        
        if (isProcessing) {
            sendBtn.disabled = true;
            icon.className = 'fas fa-spinner fa-spin';
            text.textContent = 'Sending...';
        } else {
            sendBtn.disabled = false;
            icon.className = 'fas fa-paper-plane';
            text.textContent = 'Send';
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
    
    clearChat() {
        if (confirm('Are you sure you want to clear the chat history?')) {
            const messagesContainer = document.getElementById('messagesContainer');
            
            // Keep only the welcome message
            const welcomeMessage = messagesContainer.querySelector('.message.assistant');
            messagesContainer.innerHTML = '';
            messagesContainer.appendChild(welcomeMessage);
            
            // Clear conversation history for fresh start
            this.messages = [];
            this.updateConversationStatus();
            this.showToast('Chat cleared successfully. Starting fresh conversation.', 'success');
        }
    }
    
    exportChat() {
        if (this.messages.length === 0) {
            this.showToast('No messages to export.', 'warning');
            return;
        }
        
        const chatData = {
            exportDate: new Date().toISOString(),
            messages: this.messages.map(msg => ({
                role: msg.role,
                content: Array.isArray(msg.content) ? 
                    msg.content.map(item => item.type === 'text' ? item.text : '[Image]').join(' ') :
                    msg.content,
                timestamp: msg.timestamp.toISOString()
            }))
        };
        
        const blob = new Blob([JSON.stringify(chatData, null, 2)], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `vlm-chat-${new Date().toISOString().split('T')[0]}.json`;
        a.click();
        URL.revokeObjectURL(url);
        
        this.showToast('Chat exported successfully.', 'success');
    }
    
    async clearVram() {
        try {
            const response = await fetch(`${this.serverUrl}/clear_vram`, {
                method: 'POST'
            });
            
            if (response.ok) {
                this.showToast('VRAM cleared successfully.', 'success');
                this.updateModelInfo();
            } else {
                this.showToast('Failed to clear VRAM.', 'error');
            }
        } catch (error) {
            this.showToast('Error clearing VRAM.', 'error');
        }
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

// Initialize the chat when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.chat = new VLMChat();
});