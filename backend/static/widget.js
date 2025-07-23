/**
 * AI Voice Assistant Embeddable Widget
 * Production-ready standalone widget for external websites
 * Version: 1.0.0
 */

(function() {
    'use strict';
    
    // Widget configuration and globals
    let widgetConfig = null;
    let widgetInstance = null;
    let isInitialized = false;
    
    // Widget Class Definition
    class AIVoiceWidget {
        constructor(config) {
            this.config = {
                siteId: 'demo',
                backendUrl: 'http://localhost:8001',
                position: 'bottom-right',
                theme: {
                    primary_color: '#3B82F6',
                    secondary_color: '#1E40AF',
                    text_color: '#1F2937',
                    background_color: '#FFFFFF',
                    danger_color: '#EF4444'
                },
                greeting_message: "Hi there! I'm your virtual assistant. How can I help you today?",
                bot_name: 'AI Assistant',
                auto_greet: true,
                voice_enabled: true,
                language: 'en-US',
                ...config
            };
            
            this.isOpen = false;
            this.isListening = false;
            this.isSpeaking = false;
            this.sessionId = this.generateUUID();
            this.visitorId = this.getOrCreateVisitorId();
            this.messages = [];
            this.hasGreeted = false;
            
            this.recognition = null;
            this.synthesis = null;
            
            this.init();
        }
        
        // Utility Methods
        generateUUID() {
            return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
                const r = Math.random() * 16 | 0;
                const v = c == 'x' ? r : (r & 0x3 | 0x8);
                return v.toString(16);
            });
        }
        
        getOrCreateVisitorId() {
            let id = localStorage.getItem('ai_assistant_visitor_id');
            if (!id) {
                id = `visitor_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
                localStorage.setItem('ai_assistant_visitor_id', id);
            }
            return id;
        }
        
        // Widget Initialization
        async init() {
            try {
                // Load configuration from backend
                await this.loadConfiguration();
                
                // Initialize speech APIs
                this.initializeSpeech();
                
                // Create widget DOM
                this.createWidget();
                
                // Set up event listeners
                this.setupEventListeners();
                
                console.log('AI Voice Widget initialized successfully');
                this.logAnalytics('widget_initialized');
            } catch (error) {
                console.error('Widget initialization failed:', error);
                this.createWidget(); // Create with default config
            }
        }
        
        async loadConfiguration() {
            try {
                const response = await fetch(`${this.config.backendUrl}/api/widget/config`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ site_id: this.config.siteId })
                });
                
                if (response.ok) {
                    const config = await response.json();
                    this.config = { ...this.config, ...config };
                }
            } catch (error) {
                console.warn('Failed to load widget configuration, using defaults:', error);
            }
        }
        
        initializeSpeech() {
            // Speech Recognition with explicit permission request
            if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
                const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
                this.recognition = new SpeechRecognition();
                
                this.recognition.continuous = false;
                this.recognition.interimResults = false;
                this.recognition.lang = this.config.language;
                
                this.recognition.onstart = () => {
                    console.log('🎤 Speech recognition started');
                    this.setListening(true);
                };
                
                this.recognition.onend = () => {
                    console.log('🎤 Speech recognition ended');
                    this.setListening(false);
                };
                
                this.recognition.onresult = (event) => {
                    const transcript = event.results[0][0].transcript;
                    console.log('🎤 Speech recognized:', transcript);
                    this.handleUserMessage(transcript, 'voice');
                };
                
                this.recognition.onerror = (event) => {
                    console.error('🎤 Speech recognition error:', event.error);
                    this.setListening(false);
                    
                    if (event.error === 'not-allowed') {
                        this.addMessage('system', 'Microphone access denied. Please allow microphone permissions and try again.');
                    } else if (event.error === 'no-speech') {
                        this.addMessage('system', 'No speech detected. Please try speaking again.');
                    } else {
                        this.addMessage('system', `Speech recognition error: ${event.error}. Please try again.`);
                    }
                };
            } else {
                console.warn('🎤 Speech recognition not supported in this browser');
            }
            
            // Speech Synthesis
            if ('speechSynthesis' in window) {
                this.synthesis = window.speechSynthesis;
                console.log('🔊 Speech synthesis available');
            } else {
                console.warn('🔊 Speech synthesis not supported in this browser');
            }
        }
        
        // Widget DOM Creation
        createWidget() {
            // Remove existing widget if present
            const existing = document.getElementById('ai-voice-widget-container');
            if (existing) {
                existing.remove();
            }
            
            // Create widget container
            const container = document.createElement('div');
            container.id = 'ai-voice-widget-container';
            container.className = `ai-widget-container ${this.config.position}`;
            
            // Widget HTML
            container.innerHTML = `
                <div class="ai-widget-toggle" id="ai-widget-toggle">
                    <svg class="ai-widget-icon ai-widget-chat-icon" viewBox="0 0 24 24" fill="none">
                        <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" stroke="currentColor" stroke-width="2"/>
                    </svg>
                    <svg class="ai-widget-icon ai-widget-close-icon" viewBox="0 0 24 24" fill="none" style="display: none;">
                        <path d="M18 6L6 18M6 6l12 12" stroke="currentColor" stroke-width="2"/>
                    </svg>
                </div>
                
                <div class="ai-widget-panel" id="ai-widget-panel" style="display: none;">
                    <div class="ai-widget-header">
                        <h3 class="ai-widget-title">${this.config.bot_name}</h3>
                        <div class="ai-widget-status" id="ai-widget-status"></div>
                    </div>
                    
                    <div class="ai-widget-messages" id="ai-widget-messages">
                        <!-- Messages will be inserted here -->
                    </div>
                    
                    <div class="ai-widget-controls">
                        ${this.config.voice_enabled ? `
                        <div class="ai-widget-voice-controls">
                            <button class="ai-widget-voice-btn" id="ai-widget-voice-btn" title="Start voice input">
                                <svg viewBox="0 0 24 24" fill="none">
                                    <path d="M12 1a3 3 0 0 0-3 3v8a3 3 0 0 0 6 0V4a3 3 0 0 0-3-3z" stroke="currentColor" stroke-width="2"/>
                                    <path d="M19 10v2a7 7 0 0 1-14 0v-2" stroke="currentColor" stroke-width="2"/>
                                    <line x1="12" y1="19" x2="12" y2="23" stroke="currentColor" stroke-width="2"/>
                                    <line x1="8" y1="23" x2="16" y2="23" stroke="currentColor" stroke-width="2"/>
                                </svg>
                            </button>
                            <button class="ai-widget-stop-btn" id="ai-widget-stop-btn" title="Stop speaking" style="display: none;">
                                <svg viewBox="0 0 24 24" fill="none">
                                    <rect x="6" y="4" width="4" height="16" stroke="currentColor" stroke-width="2"/>
                                    <rect x="14" y="4" width="4" height="16" stroke="currentColor" stroke-width="2"/>
                                </svg>
                            </button>
                            <div class="ai-widget-mic-status" id="ai-widget-mic-status" title="Microphone permission status">
                                <svg viewBox="0 0 24 24" fill="none" class="ai-widget-mic-icon">
                                    <path d="M12 1a3 3 0 0 0-3 3v8a3 3 0 0 0 6 0V4a3 3 0 0 0-3-3z" stroke="currentColor" stroke-width="2"/>
                                    <path d="M19 10v2a7 7 0 0 1-14 0v-2" stroke="currentColor" stroke-width="2"/>
                                    <line x1="12" y1="19" x2="12" y2="23" stroke="currentColor" stroke-width="2"/>
                                    <line x1="8" y1="23" x2="16" y2="23" stroke="currentColor" stroke-width="2"/>
                                </svg>
                                <span class="ai-widget-mic-status-text">Click to check</span>
                            </div>
                        </div>
                        ` : ''}
                        
                        <div class="ai-widget-input-section">
                            <form class="ai-widget-input-form" id="ai-widget-input-form">
                                <input type="text" 
                                       class="ai-widget-input" 
                                       id="ai-widget-input" 
                                       placeholder="Type your message..."
                                       autocomplete="off">
                                <button type="submit" class="ai-widget-send-btn" title="Send message">
                                    <svg viewBox="0 0 24 24" fill="none">
                                        <path d="M22 2L11 13" stroke="currentColor" stroke-width="2"/>
                                        <path d="M22 2L15 22L11 13L2 9L22 2Z" stroke="currentColor" stroke-width="2"/>
                                    </svg>
                                </button>
                            </form>
                        </div>
                        
                        <div class="ai-widget-footer">
                            <span class="ai-widget-powered-by">Powered by AI Voice Assistant</span>
                        </div>
                    </div>
                </div>
            `;
            
            // Add styles
            this.injectStyles();
            
            // Add to page
            document.body.appendChild(container);
            
            // Store references
            this.elements = {
                container: container,
                toggle: container.querySelector('#ai-widget-toggle'),
                panel: container.querySelector('#ai-widget-panel'),
                messages: container.querySelector('#ai-widget-messages'),
                status: container.querySelector('#ai-widget-status'),
                input: container.querySelector('#ai-widget-input'),
                inputForm: container.querySelector('#ai-widget-input-form'),
                voiceBtn: container.querySelector('#ai-widget-voice-btn'),
                stopBtn: container.querySelector('#ai-widget-stop-btn'),
                chatIcon: container.querySelector('.ai-widget-chat-icon'),
                closeIcon: container.querySelector('.ai-widget-close-icon')
            };
        }
        
        injectStyles() {
            if (document.getElementById('ai-widget-styles')) return;
            
            const styles = document.createElement('style');
            styles.id = 'ai-widget-styles';
            styles.textContent = `
                /* AI Voice Widget Styles */
                .ai-widget-container {
                    position: fixed !important;
                    z-index: 2147483647 !important;
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif !important;
                    font-size: 14px !important;
                    line-height: 1.4 !important;
                    color: #333 !important;
                    box-sizing: border-box !important;
                }
                
                .ai-widget-container *, .ai-widget-container *:before, .ai-widget-container *:after {
                    box-sizing: border-box !important;
                }
                
                .ai-widget-container.bottom-right {
                    bottom: 20px !important;
                    right: 20px !important;
                }
                
                .ai-widget-container.bottom-left {
                    bottom: 20px !important;
                    left: 20px !important;
                }
                
                .ai-widget-toggle {
                    width: 60px !important;
                    height: 60px !important;
                    border-radius: 50% !important;
                    background: linear-gradient(135deg, ${this.config.theme.primary_color} 0%, ${this.config.theme.secondary_color} 100%) !important;
                    border: none !important;
                    cursor: pointer !important;
                    box-shadow: 0 4px 16px rgba(0, 0, 0, 0.15) !important;
                    display: flex !important;
                    align-items: center !important;
                    justify-content: center !important;
                    transition: all 0.3s ease !important;
                    color: white !important;
                    outline: none !important;
                }
                
                .ai-widget-toggle:hover {
                    transform: scale(1.05) !important;
                    box-shadow: 0 6px 20px rgba(0, 0, 0, 0.2) !important;
                }
                
                .ai-widget-icon {
                    width: 24px !important;
                    height: 24px !important;
                    stroke: currentColor !important;
                    fill: none !important;
                }
                
                .ai-widget-panel {
                    position: absolute !important;
                    bottom: 80px !important;
                    right: 0 !important;
                    width: 350px !important;
                    height: 500px !important;
                    background: ${this.config.theme.background_color} !important;
                    border-radius: 12px !important;
                    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.15) !important;
                    display: flex !important;
                    flex-direction: column !important;
                    overflow: hidden !important;
                    animation: ai-widget-slideUp 0.3s ease-out !important;
                }
                
                @keyframes ai-widget-slideUp {
                    from {
                        opacity: 0 !important;
                        transform: translateY(20px) !important;
                    }
                    to {
                        opacity: 1 !important;
                        transform: translateY(0) !important;
                    }
                }
                
                .ai-widget-header {
                    background: ${this.config.theme.primary_color} !important;
                    color: white !important;
                    padding: 16px 20px !important;
                    display: flex !important;
                    justify-content: space-between !important;
                    align-items: center !important;
                }
                
                .ai-widget-title {
                    margin: 0 !important;
                    font-size: 16px !important;
                    font-weight: 600 !important;
                }
                
                .ai-widget-status {
                    display: flex !important;
                    align-items: center !important;
                    font-size: 12px !important;
                    gap: 8px !important;
                }
                
                .ai-widget-messages {
                    flex: 1 !important;
                    overflow-y: auto !important;
                    padding: 16px !important;
                    display: flex !important;
                    flex-direction: column !important;
                    gap: 12px !important;
                }
                
                .ai-widget-message {
                    max-width: 80% !important;
                    padding: 12px 16px !important;
                    border-radius: 16px !important;
                    word-wrap: break-word !important;
                    position: relative !important;
                }
                
                .ai-widget-message.user {
                    background: ${this.config.theme.primary_color} !important;
                    color: white !important;
                    align-self: flex-end !important;
                    border-bottom-right-radius: 4px !important;
                }
                
                .ai-widget-message.bot {
                    background: #f1f5f9 !important;
                    color: ${this.config.theme.text_color} !important;
                    align-self: flex-start !important;
                    border-bottom-left-radius: 4px !important;
                }
                
                .ai-widget-message.system {
                    background: #fef3cd !important;
                    color: #856404 !important;
                    align-self: center !important;
                    font-style: italic !important;
                    max-width: 90% !important;
                }
                
                .ai-widget-message-time {
                    font-size: 10px !important;
                    opacity: 0.7 !important;
                    margin-top: 4px !important;
                }
                
                .ai-widget-controls {
                    padding: 16px !important;
                    background: #f8fafc !important;
                    border-top: 1px solid #e2e8f0 !important;
                }
                
                .ai-widget-voice-controls {
                    display: flex !important;
                    gap: 8px !important;
                    margin-bottom: 12px !important;
                }
                
                .ai-widget-voice-btn, .ai-widget-stop-btn {
                    width: 40px !important;
                    height: 40px !important;
                    border-radius: 50% !important;
                    border: none !important;
                    cursor: pointer !important;
                    display: flex !important;
                    align-items: center !important;
                    justify-content: center !important;
                    transition: all 0.2s ease !important;
                    outline: none !important;
                }
                
                .ai-widget-voice-btn {
                    background: ${this.config.theme.primary_color} !important;
                    color: white !important;
                }
                
                .ai-widget-voice-btn:hover {
                    background: ${this.config.theme.secondary_color} !important;
                }
                
                .ai-widget-voice-btn:disabled {
                    opacity: 0.5 !important;
                    cursor: not-allowed !important;
                }
                
                .ai-widget-voice-btn.listening {
                    background: ${this.config.theme.danger_color} !important;
                    animation: ai-widget-pulse 1s infinite !important;
                }
                
                .ai-widget-stop-btn {
                    background: ${this.config.theme.danger_color} !important;
                    color: white !important;
                }
                
                @keyframes ai-widget-pulse {
                    0% { transform: scale(1); opacity: 1; }
                    50% { transform: scale(1.05); opacity: 0.8; }
                    100% { transform: scale(1); opacity: 1; }
                }
                
                .ai-widget-voice-btn svg, .ai-widget-stop-btn svg {
                    width: 20px !important;
                    height: 20px !important;
                }
                
                .ai-widget-input-form {
                    display: flex !important;
                    gap: 8px !important;
                    align-items: center !important;
                }
                
                .ai-widget-input {
                    flex: 1 !important;
                    padding: 12px 16px !important;
                    border: 2px solid #e2e8f0 !important;
                    border-radius: 24px !important;
                    outline: none !important;
                    font-size: 14px !important;
                    font-family: inherit !important;
                    transition: border-color 0.2s ease !important;
                    background: white !important;
                    color: ${this.config.theme.text_color} !important;
                }
                
                .ai-widget-input:focus {
                    border-color: ${this.config.theme.primary_color} !important;
                }
                
                .ai-widget-send-btn {
                    width: 40px !important;
                    height: 40px !important;
                    border-radius: 50% !important;
                    background: ${this.config.theme.primary_color} !important;
                    color: white !important;
                    border: none !important;
                    cursor: pointer !important;
                    display: flex !important;
                    align-items: center !important;
                    justify-content: center !important;
                    transition: all 0.2s ease !important;
                    outline: none !important;
                }
                
                .ai-widget-send-btn:hover {
                    background: ${this.config.theme.secondary_color} !important;
                }
                
                .ai-widget-send-btn:disabled {
                    opacity: 0.5 !important;
                    cursor: not-allowed !important;
                }
                
                .ai-widget-send-btn svg {
                    width: 18px !important;
                    height: 18px !important;
                }
                
                .ai-widget-footer {
                    text-align: center !important;
                    margin-top: 12px !important;
                }
                
                .ai-widget-powered-by {
                    font-size: 10px !important;
                    color: #64748b !important;
                }
                
                .ai-widget-typing {
                    display: flex !important;
                    gap: 4px !important;
                    align-items: center !important;
                }
                
                .ai-widget-typing span {
                    width: 6px !important;
                    height: 6px !important;
                    border-radius: 50% !important;
                    background: #64748b !important;
                    animation: ai-widget-bounce 1.4s infinite ease-in-out !important;
                }
                
                .ai-widget-typing span:nth-child(1) { animation-delay: -0.32s !important; }
                .ai-widget-typing span:nth-child(2) { animation-delay: -0.16s !important; }
                
                @keyframes ai-widget-bounce {
                    0%, 80%, 100% {
                        transform: scale(0) !important;
                    }
                    40% {
                        transform: scale(1) !important;
                    }
                }
                
                /* Mobile Responsive */
                @media (max-width: 480px) {
                    .ai-widget-panel {
                        width: 300px !important;
                        height: 450px !important;
                    }
                    
                    .ai-widget-container.bottom-right {
                        right: 10px !important;
                        bottom: 10px !important;
                    }
                    
                    .ai-widget-container.bottom-left {
                        left: 10px !important;
                        bottom: 10px !important;
                    }
                }
                
                /* Status indicators */
                .ai-widget-listening-indicator {
                    display: flex !important;
                    align-items: center !important;
                    gap: 6px !important;
                    color: #ef4444 !important;
                }
                
                .ai-widget-pulse-dot {
                    width: 8px !important;
                    height: 8px !important;
                    border-radius: 50% !important;
                    background: currentColor !important;
                    animation: ai-widget-pulse 1s infinite !important;
                }
                
                .ai-widget-speaking-indicator {
                    display: flex !important;
                    align-items: center !important;
                    gap: 6px !important;
                    color: #22c55e !important;
                }
                
                .ai-widget-speaking-bars {
                    display: flex !important;
                    gap: 2px !important;
                    align-items: center !important;
                }
                
                .ai-widget-speaking-bar {
                    width: 3px !important;
                    height: 12px !important;
                    background: currentColor !important;
                    border-radius: 2px !important;
                    animation: ai-widget-speaking 0.8s infinite ease-in-out !important;
                }
                
                .ai-widget-speaking-bar:nth-child(2) { animation-delay: 0.1s !important; }
                .ai-widget-speaking-bar:nth-child(3) { animation-delay: 0.2s !important; }
                
                @keyframes ai-widget-speaking {
                    0%, 100% { height: 4px !important; }
                    50% { height: 12px !important; }
                }
            `;
            
            document.head.appendChild(styles);
        }
        
        setupEventListeners() {
            console.log('🔧 Setting up event listeners...');
            
            // Toggle button
            this.elements.toggle.addEventListener('click', () => {
                console.log('🖱️ Widget toggle clicked');
                this.toggleWidget();
            });
            
            // Input form
            this.elements.inputForm.addEventListener('submit', (e) => {
                e.preventDefault();
                const message = this.elements.input.value.trim();
                console.log('📝 Form submitted with message:', message);
                if (message) {
                    this.handleUserMessage(message, 'text');
                    this.elements.input.value = '';
                }
            });
            
            // Voice button
            if (this.elements.voiceBtn) {
                this.elements.voiceBtn.addEventListener('click', () => {
                    console.log('🎤 Voice button clicked');
                    this.startListening();
                });
            }
            
            // Stop button
            if (this.elements.stopBtn) {
                this.elements.stopBtn.addEventListener('click', () => {
                    console.log('⏹️ Stop button clicked');
                    this.stopSpeaking();
                });
            }
            
            // Keyboard shortcuts
            document.addEventListener('keydown', (e) => {
                if (e.ctrlKey && e.shiftKey && e.key === 'A') {
                    e.preventDefault();
                    console.log('⌨️ Keyboard shortcut activated');
                    this.toggleWidget();
                }
            });
            
            console.log('✅ Event listeners set up successfully');
        }
        
        // Widget Actions
        toggleWidget() {
            this.isOpen = !this.isOpen;
            
            if (this.isOpen) {
                this.elements.panel.style.display = 'flex';
                this.elements.chatIcon.style.display = 'none';
                this.elements.closeIcon.style.display = 'block';
                this.elements.input.focus();
                
                // Auto-greet
                if (this.config.auto_greet && !this.hasGreeted) {
                    setTimeout(() => {
                        this.addMessage('bot', this.config.greeting_message);
                        if (this.config.voice_enabled) {
                            this.speak(this.config.greeting_message);
                        }
                        this.hasGreeted = true;
                    }, 500);
                }
                
                this.logAnalytics('widget_opened');
            } else {
                this.elements.panel.style.display = 'none';
                this.elements.chatIcon.style.display = 'block';
                this.elements.closeIcon.style.display = 'none';
                this.stopSpeaking();
                this.logAnalytics('widget_closed');
            }
        }
        
        async handleUserMessage(message, type = 'text') {
            if (!message.trim()) return;
            
            console.log(`💬 Handling ${type} message:`, message);
            
            this.addMessage('user', message);
            this.showTyping();
            this.logAnalytics(type === 'voice' ? 'voice_input' : 'text_input');
            
            try {
                console.log('🌐 Sending chat request to:', `${this.config.backendUrl}/api/chat`);
                
                const requestData = {
                    message: message,
                    session_id: this.sessionId,
                    site_id: this.config.siteId,
                    visitor_id: this.visitorId
                };
                
                console.log('📤 Request data:', requestData);
                
                const response = await fetch(`${this.config.backendUrl}/api/chat`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify(requestData),
                    signal: AbortSignal.timeout(15000)
                });
                
                console.log('📥 Response status:', response.status);
                
                if (!response.ok) {
                    const errorText = await response.text();
                    console.error('❌ HTTP error response:', errorText);
                    throw new Error(`HTTP error! status: ${response.status} - ${errorText}`);
                }
                
                const data = await response.json();
                console.log('✅ Chat response:', data);
                
                this.hideTyping();
                this.addMessage('bot', data.response);
                
                if (this.config.voice_enabled) {
                    console.log('🔊 Speaking response');
                    this.speak(data.response);
                }
                
                this.logAnalytics('ai_response');
                
            } catch (error) {
                console.error('❌ Chat error:', error);
                this.hideTyping();
                
                if (error.name === 'AbortError') {
                    this.addMessage('system', 'Request timeout. Please check your connection and try again.');
                } else if (error.message.includes('Failed to fetch')) {
                    this.addMessage('system', 'Network error. Please check your internet connection and try again.');
                } else {
                    this.addMessage('system', `Error: ${error.message}. Please try again.`);
                }
            }
        }
        
        addMessage(sender, text) {
            const messageEl = document.createElement('div');
            messageEl.className = `ai-widget-message ${sender}`;
            
            const contentEl = document.createElement('div');
            contentEl.textContent = text;
            messageEl.appendChild(contentEl);
            
            const timeEl = document.createElement('div');
            timeEl.className = 'ai-widget-message-time';
            timeEl.textContent = new Date().toLocaleTimeString();
            messageEl.appendChild(timeEl);
            
            this.elements.messages.appendChild(messageEl);
            this.elements.messages.scrollTop = this.elements.messages.scrollHeight;
            
            this.messages.push({ sender, text, timestamp: new Date() });
        }
        
        showTyping() {
            const typingEl = document.createElement('div');
            typingEl.id = 'ai-widget-typing';
            typingEl.className = 'ai-widget-message bot';
            typingEl.innerHTML = `
                <div class="ai-widget-typing">
                    <span></span>
                    <span></span>
                    <span></span>
                </div>
            `;
            
            this.elements.messages.appendChild(typingEl);
            this.elements.messages.scrollTop = this.elements.messages.scrollHeight;
        }
        
        hideTyping() {
            const typingEl = document.getElementById('ai-widget-typing');
            if (typingEl) {
                typingEl.remove();
            }
        }
        
        // Speech Methods
        async requestMicrophonePermission() {
            try {
                console.log('🎤 Requesting microphone permission...');
                const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
                console.log('✅ Microphone permission granted!');
                // Stop the stream immediately as we only needed permission
                stream.getTracks().forEach(track => track.stop());
                return true;
            } catch (error) {
                console.error('❌ Microphone permission denied:', error);
                this.addMessage('system', 'Microphone access is required for voice input. Please allow microphone permissions in your browser settings.');
                return false;
            }
        }

        async startListening() {
            if (!this.recognition) {
                this.addMessage('system', 'Speech recognition is not supported in your browser.');
                return;
            }
            
            console.log('🎤 Starting voice input...');
            
            // Check if we have microphone permission
            if (navigator.permissions) {
                try {
                    const permission = await navigator.permissions.query({ name: 'microphone' });
                    console.log('🎤 Microphone permission status:', permission.state);
                    
                    if (permission.state === 'denied') {
                        this.addMessage('system', 'Microphone access denied. Please allow microphone permissions and try again.');
                        return;
                    }
                } catch (error) {
                    console.warn('Could not check microphone permission:', error);
                }
            }
            
            // Request permission if needed
            const hasPermission = await this.requestMicrophonePermission();
            if (!hasPermission) return;
            
            try {
                this.recognition.start();
                console.log('🎤 Speech recognition started successfully');
            } catch (error) {
                console.error('🎤 Error starting speech recognition:', error);
                if (error.message.includes('already started')) {
                    this.addMessage('system', 'Voice recognition is already active. Please try again in a moment.');
                } else {
                    this.addMessage('system', 'Error starting voice recognition. Please try again.');
                }
            }
        }
        
        setListening(listening) {
            this.isListening = listening;
            
            if (listening) {
                this.elements.status.innerHTML = `
                    <div class="ai-widget-listening-indicator">
                        <div class="ai-widget-pulse-dot"></div>
                        <span>Listening...</span>
                    </div>
                `;
                if (this.elements.voiceBtn) {
                    this.elements.voiceBtn.classList.add('listening');
                }
            } else {
                this.elements.status.innerHTML = '';
                if (this.elements.voiceBtn) {
                    this.elements.voiceBtn.classList.remove('listening');
                }
            }
        }
        
        speak(text) {
            if (!this.synthesis) {
                console.warn('🔊 Speech synthesis not available');
                return;
            }
            
            console.log('🔊 Speaking text:', text);
            
            this.synthesis.cancel();
            
            const utterance = new SpeechSynthesisUtterance(text);
            utterance.lang = this.config.language;
            utterance.rate = 0.9;
            utterance.pitch = 1.0;
            utterance.volume = 1.0;
            
            utterance.onstart = () => {
                console.log('🔊 Speech started');
                this.setSpeaking(true);
            };
            
            utterance.onend = () => {
                console.log('🔊 Speech ended');
                this.setSpeaking(false);
            };
            
            utterance.onerror = (event) => {
                console.error('🔊 Speech error:', event.error);
                this.setSpeaking(false);
            };
            
            this.synthesis.speak(utterance);
        }
        
        setSpeaking(speaking) {
            this.isSpeaking = speaking;
            
            if (speaking) {
                this.elements.status.innerHTML = `
                    <div class="ai-widget-speaking-indicator">
                        <div class="ai-widget-speaking-bars">
                            <div class="ai-widget-speaking-bar"></div>
                            <div class="ai-widget-speaking-bar"></div>
                            <div class="ai-widget-speaking-bar"></div>
                        </div>
                        <span>Speaking...</span>
                    </div>
                `;
                if (this.elements.stopBtn) {
                    this.elements.stopBtn.style.display = 'flex';
                }
            } else {
                this.elements.status.innerHTML = '';
                if (this.elements.stopBtn) {
                    this.elements.stopBtn.style.display = 'none';
                }
            }
        }
        
        stopSpeaking() {
            if (this.synthesis) {
                this.synthesis.cancel();
                this.setSpeaking(false);
            }
        }
        
        // Analytics
        async logAnalytics(type) {
            try {
                await fetch(`${this.config.backendUrl}/api/analytics/interaction`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        site_id: this.config.siteId,
                        session_id: this.sessionId,
                        type: type,
                        timestamp: new Date().toISOString()
                    })
                });
            } catch (error) {
                console.error('Analytics logging failed:', error);
            }
        }
        
        // Cleanup
        destroy() {
            if (this.elements.container) {
                this.elements.container.remove();
            }
            
            const styles = document.getElementById('ai-widget-styles');
            if (styles) {
                styles.remove();
            }
            
            this.stopSpeaking();
        }
    }
    
    // Widget Initialization Function
    function initializeWidget(config = {}) {
        if (widgetInstance) {
            widgetInstance.destroy();
        }
        
        // Get site ID from script attributes
        const scriptTag = document.currentScript || document.querySelector('script[data-site-id]');
        if (scriptTag) {
            config.siteId = config.siteId || scriptTag.getAttribute('data-site-id') || scriptTag.getAttribute('data-ai-widget-site-id');
            config.backendUrl = config.backendUrl || scriptTag.getAttribute('data-backend-url') || window.WIDGET_BACKEND_URL;
        }
        
        // Create widget instance
        widgetInstance = new AIVoiceWidget(config);
        isInitialized = true;
        
        return widgetInstance;
    }
    
    // Auto-initialize if DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', () => {
            if (!isInitialized) {
                initializeWidget();
            }
        });
    } else {
        if (!isInitialized) {
            initializeWidget();
        }
    }
    
    // Global API
    window.AIVoiceWidget = {
        init: initializeWidget,
        getInstance: () => widgetInstance,
        destroy: () => {
            if (widgetInstance) {
                widgetInstance.destroy();
                widgetInstance = null;
                isInitialized = false;
            }
        }
    };
    
    console.log('AI Voice Widget script loaded successfully');
})();