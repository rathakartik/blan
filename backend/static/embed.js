/**
 * AI Voice Assistant - Simple Embed Script
 * This script creates the widget toggle and iframe for external websites
 */

(function() {
    'use strict';
    
    // Configuration from script attributes
    const currentScript = document.currentScript || document.querySelector('script[data-site-id]');
    const config = {
        siteId: currentScript?.getAttribute('data-site-id') || 'demo',
        backendUrl: currentScript?.getAttribute('data-backend-url') || 'http://localhost:8001',
        position: currentScript?.getAttribute('data-position') || 'bottom-right',
        theme: currentScript?.getAttribute('data-theme') || 'blue'
    };
    
    // Prevent multiple initialization
    if (window.aiWidgetInitialized) {
        console.warn('AI Voice Widget already initialized');
        return;
    }
    window.aiWidgetInitialized = true;
    
    // Create widget container
    const widgetContainer = document.createElement('div');
    widgetContainer.id = 'ai-voice-widget-embed';
    widgetContainer.setAttribute('data-site-id', config.siteId);
    
    // Position classes
    const positionClasses = {
        'bottom-right': 'bottom: 20px; right: 20px;',
        'bottom-left': 'bottom: 20px; left: 20px;',
        'top-right': 'top: 20px; right: 20px;',
        'top-left': 'top: 20px; left: 20px;'
    };
    
    // Theme colors
    const themeColors = {
        blue: { primary: '#3B82F6', secondary: '#1E40AF' },
        green: { primary: '#10B981', secondary: '#059669' },
        purple: { primary: '#8B5CF6', secondary: '#7C3AED' },
        red: { primary: '#EF4444', secondary: '#DC2626' },
        orange: { primary: '#F59E0B', secondary: '#D97706' }
    };
    
    const colors = themeColors[config.theme] || themeColors.blue;
    
    // Widget styles
    const widgetStyles = `
        #ai-voice-widget-embed {
            position: fixed !important;
            ${positionClasses[config.position] || positionClasses['bottom-right']}
            z-index: 2147483647 !important;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif !important;
        }
        
        .ai-embed-toggle {
            width: 60px !important;
            height: 60px !important;
            border-radius: 50% !important;
            background: linear-gradient(135deg, ${colors.primary} 0%, ${colors.secondary} 100%) !important;
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
        
        .ai-embed-toggle:hover {
            transform: scale(1.05) !important;
            box-shadow: 0 6px 20px rgba(0, 0, 0, 0.2) !important;
        }
        
        .ai-embed-toggle svg {
            width: 24px !important;
            height: 24px !important;
            stroke: currentColor !important;
            fill: none !important;
            transition: all 0.3s ease !important;
        }
        
        .ai-embed-frame {
            display: none !important;
            position: absolute !important;
            bottom: 80px !important;
            right: 0 !important;
            width: 350px !important;
            height: 500px !important;
            border: none !important;
            border-radius: 12px !important;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.15) !important;
            background: white !important;
            overflow: hidden !important;
            animation: ai-embed-slideUp 0.3s ease-out !important;
        }
        
        .ai-embed-frame.show {
            display: block !important;
        }
        
        @keyframes ai-embed-slideUp {
            from {
                opacity: 0 !important;
                transform: translateY(20px) !important;
            }
            to {
                opacity: 1 !important;
                transform: translateY(0) !important;
            }
        }
        
        /* Position adjustments */
        #ai-voice-widget-embed.top-right .ai-embed-frame,
        #ai-voice-widget-embed.top-left .ai-embed-frame {
            bottom: auto !important;
            top: 80px !important;
        }
        
        #ai-voice-widget-embed.bottom-left .ai-embed-frame,
        #ai-voice-widget-embed.top-left .ai-embed-frame {
            right: auto !important;
            left: 0 !important;
        }
        
        /* Mobile responsive */
        @media (max-width: 480px) {
            .ai-embed-frame {
                width: 300px !important;
                height: 450px !important;
            }
            
            #ai-voice-widget-embed {
                bottom: 10px !important;
                right: 10px !important;
                left: auto !important;
                top: auto !important;
            }
            
            #ai-voice-widget-embed.bottom-left {
                left: 10px !important;
                right: auto !important;
            }
        }
        
        /* Loading state */
        .ai-embed-loading {
            display: flex !important;
            align-items: center !important;
            justify-content: center !important;
            height: 100% !important;
            background: white !important;
        }
        
        .ai-embed-spinner {
            width: 40px !important;
            height: 40px !important;
            border: 4px solid #f3f3f3 !important;
            border-top: 4px solid ${colors.primary} !important;
            border-radius: 50% !important;
            animation: ai-embed-spin 1s linear infinite !important;
        }
        
        @keyframes ai-embed-spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
    `;
    
    // Inject styles
    const styleSheet = document.createElement('style');
    styleSheet.id = 'ai-widget-embed-styles';
    styleSheet.textContent = widgetStyles;
    document.head.appendChild(styleSheet);
    
    // Widget HTML
    widgetContainer.className = config.position;
    widgetContainer.innerHTML = `
        <button class="ai-embed-toggle" id="ai-embed-toggle" aria-label="Open AI Assistant">
            <svg class="ai-embed-chat-icon" viewBox="0 0 24 24" fill="none">
                <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
            <svg class="ai-embed-close-icon" viewBox="0 0 24 24" fill="none" style="display: none;">
                <path d="M18 6L6 18M6 6l12 12" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
        </button>
        <iframe id="ai-embed-frame" class="ai-embed-frame" src="${config.backendUrl}/widget?site_id=${config.siteId}">
            <div class="ai-embed-loading">
                <div class="ai-embed-spinner"></div>
            </div>
        </iframe>
    `;
    
    // Add to page
    document.body.appendChild(widgetContainer);
    
    // Widget state
    let isOpen = false;
    let isLoaded = false;
    
    // Get elements
    const toggleButton = document.getElementById('ai-embed-toggle');
    const iframe = document.getElementById('ai-embed-frame');
    const chatIcon = toggleButton.querySelector('.ai-embed-chat-icon');
    const closeIcon = toggleButton.querySelector('.ai-embed-close-icon');
    
    // Toggle function
    function toggleWidget() {
        isOpen = !isOpen;
        
        if (isOpen) {
            iframe.classList.add('show');
            chatIcon.style.display = 'none';
            closeIcon.style.display = 'block';
            toggleButton.setAttribute('aria-label', 'Close AI Assistant');
            
            // Log analytics
            logAnalytics('widget_opened');
        } else {
            iframe.classList.remove('show');
            chatIcon.style.display = 'block';
            closeIcon.style.display = 'none';
            toggleButton.setAttribute('aria-label', 'Open AI Assistant');
            
            // Log analytics  
            logAnalytics('widget_closed');
        }
    }
    
    // Analytics logging
    async function logAnalytics(eventType) {
        try {
            await fetch(`${config.backendUrl}/api/analytics/interaction`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    site_id: config.siteId,
                    session_id: 'embed-session',
                    type: eventType,
                    timestamp: new Date().toISOString(),
                    user_agent: navigator.userAgent,
                    referrer: document.referrer,
                    url: window.location.href
                })
            });
        } catch (error) {
            console.error('Analytics logging failed:', error);
        }
    }
    
    // Event listeners
    toggleButton.addEventListener('click', toggleWidget);
    
    // Handle iframe load
    iframe.addEventListener('load', function() {
        isLoaded = true;
        logAnalytics('widget_loaded');
    });
    
    iframe.addEventListener('error', function() {
        console.error('Failed to load AI Voice Assistant widget');
        iframe.innerHTML = `
            <div style="padding: 20px; text-align: center; color: #ef4444; background: white; height: 100%; display: flex; align-items: center; justify-content: center; flex-direction: column;">
                <p style="margin: 0 0 10px 0; font-size: 14px; font-family: inherit;">Failed to load AI Assistant</p>
                <p style="margin: 0; font-size: 12px; opacity: 0.7; font-family: inherit;">Please check your connection</p>
            </div>
        `;
    });
    
    // Keyboard shortcut (Ctrl+Shift+A)
    document.addEventListener('keydown', function(e) {
        if (e.ctrlKey && e.shiftKey && e.key === 'A') {
            e.preventDefault();
            toggleWidget();
        }
    });
    
    // Handle messages from iframe
    window.addEventListener('message', function(event) {
        if (event.origin !== config.backendUrl.replace(/:\d+$/, '')) return;
        
        if (event.data.type === 'widget-ready') {
            isLoaded = true;
            console.log('AI Voice Widget loaded successfully');
        }
    });
    
    // Global API for programmatic control
    window.AIVoiceWidgetEmbed = {
        open: function() {
            if (!isOpen) toggleWidget();
        },
        close: function() {
            if (isOpen) toggleWidget();
        },
        toggle: toggleWidget,
        isOpen: function() {
            return isOpen;
        },
        isLoaded: function() {
            return isLoaded;
        },
        getSiteId: function() {
            return config.siteId;
        }
    };
    
    // Log initialization
    logAnalytics('widget_initialized');
    
    console.log(`AI Voice Assistant Widget initialized for site: ${config.siteId}`);
})();