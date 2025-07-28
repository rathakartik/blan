import React, { useState, useEffect, useRef, useMemo } from 'react';
import { v4 as uuidv4 } from 'uuid';
import './VoiceWidget.css';

const VoiceWidget = ({ config = {} }) => {
  const [isOpen, setIsOpen] = useState(false);
  const [isListening, setIsListening] = useState(false);
  const [isSpeaking, setIsSpeaking] = useState(false);
  const [messages, setMessages] = useState([]);
  const [sessionId] = useState(() => uuidv4());
  const [hasGreeted, setHasGreeted] = useState(false);
  const [speechSupported, setSpeechSupported] = useState(false);
  const [textInput, setTextInput] = useState('');
  const [isProcessing, setIsProcessing] = useState(false);
  const [visitorId, setVisitorId] = useState(null);
  
  // Generate or retrieve visitor ID
  useEffect(() => {
    const getVisitorId = () => {
      let id = localStorage.getItem('ai_assistant_visitor_id');
      if (!id) {
        id = `visitor_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
        localStorage.setItem('ai_assistant_visitor_id', id);
      }
      return id;
    };
    
    const id = getVisitorId();
    setVisitorId(id);
    console.log('Visitor ID:', id);
  }, []);
  
  const recognitionRef = useRef(null);
  const synthesisRef = useRef(null);
  const messagesEndRef = useRef(null);

  const defaultConfig = {
    greeting_message: "Hi there! I'm your virtual assistant. How can I help you today?",
    bot_name: "AI Assistant",
    theme: {
      primary_color: "#3B82F6",
      secondary_color: "#1E40AF",
      text_color: "#1F2937",
      background_color: "#FFFFFF"
    },
    position: "bottom-right",
    auto_greet: true,
    voice_enabled: true,
    language: "en-US",
    site_id: "default"
  };

  const widgetConfig = useMemo(() => ({ ...defaultConfig, ...config }), [config]);

  // Initialize speech recognition and synthesis
  useEffect(() => {
    console.log('🎯 Initializing speech recognition...');
    
    // Check for speech recognition support
    if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
      console.log('✅ Speech recognition API available');
      setSpeechSupported(true);
      
      const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
      recognitionRef.current = new SpeechRecognition();
      
      // Enhanced configuration for better recognition
      recognitionRef.current.continuous = false;
      recognitionRef.current.interimResults = true; // Enable interim results for better UX
      recognitionRef.current.maxAlternatives = 1;
      recognitionRef.current.lang = widgetConfig.language;

      recognitionRef.current.onstart = () => {
        console.log('🎤 Speech recognition started');
        setIsListening(true);
        logInteraction('voice_start');
        
        // Add helpful message when first time using voice
        if (messages.length === 1) { // Only auto-greeting message exists
          addMessage('system', '🎤 I\'m listening! Please speak clearly and I\'ll respond to your voice.');
        }
      };

      recognitionRef.current.onresult = (event) => {
        console.log('🗣️ Speech recognition result:', event);
        
        // Get the final result or the latest interim result
        let transcript = '';
        for (let i = event.resultIndex; i < event.results.length; i++) {
          if (event.results[i].isFinal) {
            transcript = event.results[i][0].transcript.trim();
            break;
          } else {
            // For interim results, we could show them as preview (optional)
            transcript = event.results[i][0].transcript.trim();
          }
        }
        
        console.log('📝 Transcript:', transcript);
        
        // Only process if we have a final result with meaningful content
        if (transcript && event.results[event.results.length - 1].isFinal) {
          setIsListening(false);
          handleUserMessage(transcript, 'voice');
        }
      };

      recognitionRef.current.onerror = (event) => {
        console.error('❌ Speech recognition error:', event.error, event);
        setIsListening(false);
        
        // Provide more specific and helpful error messages
        let errorMessage = 'Sorry, I had trouble hearing you. Please try again.';
        switch (event.error) {
          case 'no-speech':
            errorMessage = '🔇 I didn\'t hear anything. Please click the microphone and speak clearly.';
            break;
          case 'audio-capture':
            errorMessage = '🎤 Cannot access your microphone. Please check your microphone is connected and working.';
            break;
          case 'not-allowed':
            errorMessage = '🚫 Microphone access denied. Please allow microphone permission in your browser and try again.';
            break;
          case 'network':
            errorMessage = '🌐 Network error occurred. Please check your internet connection and try again.';
            break;
          case 'service-not-allowed':
            errorMessage = '⚠️ Speech recognition service not available. Please try again later.';
            break;
          case 'aborted':
            errorMessage = '⏹️ Speech recognition was stopped. Click the microphone to try again.';
            break;
        }
        
        addMessage('system', errorMessage);
      };

      recognitionRef.current.onend = () => {
        console.log('🔇 Speech recognition ended');
        setIsListening(false);
        
        // Auto-restart if no result was captured (timeout scenario)
        // This helps with continuous conversation
        setTimeout(() => {
          if (!isListening && messages.length > 1) {
            console.log('💭 Speech recognition ended without result, suggesting to try again');
          }
        }, 500);
      };
      
      console.log('✅ Speech recognition initialized successfully');
    } else {
      console.log('❌ Speech recognition API not available');
      setSpeechSupported(false);
    }

    // Check for speech synthesis support
    if ('speechSynthesis' in window) {
      console.log('✅ Speech synthesis API available');
      synthesisRef.current = window.speechSynthesis;
    } else {
      console.log('❌ Speech synthesis API not available');
    }
  }, [widgetConfig.language]);

  // Auto-greet when widget opens - separate effect to prevent multiple triggers
  useEffect(() => {
    if (widgetConfig.auto_greet && !hasGreeted && isOpen) {
      const greetingTimer = setTimeout(() => {
        console.log('Triggering auto-greeting...');
        if (widgetConfig.voice_enabled && synthesisRef.current) {
          speakMessage(widgetConfig.greeting_message);
        }
        addMessage('bot', widgetConfig.greeting_message);
        setHasGreeted(true);
        logInteraction('auto_greeting');
      }, 500); // Reduced delay for faster response

      return () => clearTimeout(greetingTimer);
    }
  }, [widgetConfig.auto_greet, widgetConfig.voice_enabled, widgetConfig.greeting_message, hasGreeted, isOpen]);

  // IMMEDIATE auto-voice greeting on page load (without requiring widget to be opened)
  useEffect(() => {
    let enableAutoVoice; // Declare function variable

    if (widgetConfig.auto_greet && widgetConfig.voice_enabled && !hasGreeted && synthesisRef.current) {
      const immediateVoiceTimer = setTimeout(() => {
        console.log('🔊 Starting immediate auto-voice greeting on page load...');
        
        // Create a user interaction handler to enable autoplay
        enableAutoVoice = () => {
          if (widgetConfig.voice_enabled && synthesisRef.current && !hasGreeted) {
            speakMessage(widgetConfig.greeting_message);
            setHasGreeted(true);
            logInteraction('immediate_voice_greeting');
            console.log('✅ Immediate voice greeting activated');
          }
          // Remove the event listener after first use
          document.removeEventListener('click', enableAutoVoice);
          document.removeEventListener('scroll', enableAutoVoice);
          document.removeEventListener('keydown', enableAutoVoice);
        };

        // Try immediate voice (may be blocked by browser autoplay policy)
        try {
          speakMessage(widgetConfig.greeting_message);
          setHasGreeted(true);
          logInteraction('immediate_voice_greeting');
          console.log('✅ Immediate voice greeting started successfully');
        } catch (error) {
          console.log('⚠️ Immediate voice blocked by browser, waiting for user interaction');
          // Fallback: Wait for any user interaction to start voice
          document.addEventListener('click', enableAutoVoice, { once: true });
          document.addEventListener('scroll', enableAutoVoice, { once: true });
          document.addEventListener('keydown', enableAutoVoice, { once: true });
        }
      }, 2000); // 2 second delay to allow page to fully load

      return () => {
        clearTimeout(immediateVoiceTimer);
        if (enableAutoVoice) {
          document.removeEventListener('click', enableAutoVoice);
          document.removeEventListener('scroll', enableAutoVoice);
          document.removeEventListener('keydown', enableAutoVoice);
        }
      };
    }
  }, [widgetConfig.auto_greet, widgetConfig.voice_enabled, widgetConfig.greeting_message, hasGreeted]);

  // Widget initialization - ensure immediate setup
  useEffect(() => {
    console.log('Widget initialized with session:', sessionId);
    
    // Pre-load speech synthesis voices for faster response
    if ('speechSynthesis' in window) {
      const loadVoices = () => {
        const voices = speechSynthesis.getVoices();
        if (voices.length > 0) {
          console.log('Speech synthesis voices loaded:', voices.length);
        }
      };
      
      if (speechSynthesis.onvoiceschanged !== undefined) {
        speechSynthesis.onvoiceschanged = loadVoices;
      } else {
        loadVoices();
      }
    }
  }, [sessionId]);

  // Auto-scroll to bottom of messages
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const logInteraction = async (type) => {
    try {
      await fetch(`${process.env.REACT_APP_BACKEND_URL}/api/analytics/interaction`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          site_id: widgetConfig.site_id,
          session_id: sessionId,
          type: type
        })
      });
    } catch (error) {
      console.error('Analytics logging error:', error);
    }
  };

  const addMessage = (sender, text) => {
    const message = {
      id: uuidv4(),
      sender,
      text,
      timestamp: new Date()
    };
    setMessages(prev => [...prev, message]);
  };

  const speakMessage = (text) => {
    if (!synthesisRef.current) return;

    // Cancel any ongoing speech
    synthesisRef.current.cancel();

    const utterance = new SpeechSynthesisUtterance(text);
    utterance.lang = widgetConfig.language;
    utterance.rate = 0.9;
    utterance.pitch = 1.0;
    utterance.volume = 1.0;

    utterance.onstart = () => setIsSpeaking(true);
    utterance.onend = () => setIsSpeaking(false);
    utterance.onerror = () => setIsSpeaking(false);

    synthesisRef.current.speak(utterance);
  };

  const handleUserMessage = async (text, type = 'text') => {
    if (!text.trim() || !visitorId) return;

    setIsProcessing(true);
    addMessage('user', text);
    logInteraction(type === 'voice' ? 'voice_input' : 'text_input');

    try {
      // Use AbortController for request timeout
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 10000); // 10 second timeout

      const response = await fetch(`${process.env.REACT_APP_BACKEND_URL}/api/chat`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          message: text,
          session_id: sessionId,
          site_id: widgetConfig.site_id,
          visitor_id: visitorId // Add visitor ID to request
        }),
        signal: controller.signal
      });

      clearTimeout(timeoutId);

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      addMessage('bot', data.response);

      // Speak the response if voice is enabled - with priority speaking
      if (widgetConfig.voice_enabled && synthesisRef.current) {
        // Cancel any ongoing speech before speaking new response
        synthesisRef.current.cancel();
        setTimeout(() => {
          speakMessage(data.response);
        }, 100);
      }

      logInteraction('ai_response');
    } catch (error) {
      console.error('Chat error:', error);
      
      if (error.name === 'AbortError') {
        addMessage('system', 'Request timeout. Please try again.');
      } else {
        addMessage('system', 'Sorry, I encountered an error. Please try again.');
      }
    } finally {
      setIsProcessing(false);
    }
  };

  const handleTextSubmit = (e) => {
    e.preventDefault();
    if (textInput.trim()) {
      handleUserMessage(textInput.trim(), 'text');
      setTextInput('');
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleTextSubmit(e);
    }
  };

  const startListening = () => {
    console.log('🎤 startListening called');
    console.log('speechSupported:', speechSupported);
    console.log('recognitionRef.current:', recognitionRef.current);
    
    if (!speechSupported || !recognitionRef.current) {
      console.error('❌ Speech recognition not supported or ref is null');
      addMessage('system', 'Speech recognition is not supported in your browser.');
      return;
    }

    // Check if already listening
    if (isListening) {
      console.log('⚠️ Already listening, stopping first');
      try {
        recognitionRef.current.stop();
      } catch (e) {
        console.error('Error stopping recognition:', e);
      }
      return;
    }

    try {
      console.log('🎯 Attempting to start speech recognition...');
      setIsListening(true); // Set listening state immediately for UI feedback
      recognitionRef.current.start();
      console.log('✅ Speech recognition start() called successfully');
    } catch (error) {
      console.error('❌ Recognition start error:', error);
      setIsListening(false); // Reset state if failed
      
      // More specific error messages
      if (error.name === 'NotAllowedError') {
        addMessage('system', 'Microphone access denied. Please allow microphone permission and try again.');
      } else if (error.name === 'NotSupportedError') {
        addMessage('system', 'Speech recognition is not supported in your browser.');
      } else {
        addMessage('system', `Error starting voice recognition: ${error.message}. Please try again.`);
      }
    }
  };

  const stopSpeaking = () => {
    if (synthesisRef.current) {
      synthesisRef.current.cancel();
      setIsSpeaking(false);
    }
  };

  const toggleWidget = () => {
    const newIsOpen = !isOpen;
    setIsOpen(newIsOpen);
    
    if (newIsOpen) {
      // Reset greeting state when widget opens
      if (widgetConfig.auto_greet) {
        setHasGreeted(false);
      }
      logInteraction('widget_open');
    } else {
      logInteraction('widget_close');
      // Stop any ongoing speech when widget closes
      if (synthesisRef.current) {
        synthesisRef.current.cancel();
        setIsSpeaking(false);
      }
    }
  };

  const getPositionClasses = () => {
    switch (widgetConfig.position) {
      case 'bottom-left':
        return 'bottom-4 left-4';
      case 'bottom-right':
      default:
        return 'bottom-4 right-4';
    }
  };

  return (
    <div className={`ai-voice-widget ${getPositionClasses()}`}>
      {/* Widget Toggle Button */}
      <button
        onClick={toggleWidget}
        className="widget-toggle-btn"
        style={{
          backgroundColor: widgetConfig.theme.primary_color,
          color: widgetConfig.theme.background_color
        }}
        aria-label="Toggle AI Assistant"
      >
        {isOpen ? (
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M18 6L6 18M6 6l12 12" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
          </svg>
        ) : (
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
          </svg>
        )}
      </button>

      {/* Widget Panel */}
      {isOpen && (
        <div className="widget-panel" style={{ backgroundColor: widgetConfig.theme.background_color }}>
          {/* Header */}
          <div 
            className="widget-header"
            style={{ 
              backgroundColor: widgetConfig.theme.primary_color,
              color: widgetConfig.theme.background_color 
            }}
          >
            <h3 className="widget-title">{widgetConfig.bot_name}</h3>
            <div className="widget-status">
              {isListening && (
                <div className="listening-indicator">
                  <div className="pulse-dot"></div>
                  <span>Listening...</span>
                </div>
              )}
              {isSpeaking && (
                <div className="speaking-indicator">
                  <div className="speaking-bars">
                    <div className="bar"></div>
                    <div className="bar"></div>
                    <div className="bar"></div>
                  </div>
                  <span>Speaking...</span>
                </div>
              )}
            </div>
          </div>

          {/* Messages */}
          <div className="widget-messages" style={{ color: widgetConfig.theme.text_color }}>
            {messages.map((message) => (
              <div key={message.id} className={`message ${message.sender}`}>
                <div className="message-content">
                  {message.text}
                </div>
                <div className="message-time">
                  {message.timestamp.toLocaleTimeString()}
                </div>
              </div>
            ))}
            {isProcessing && (
              <div className="message bot">
                <div className="message-content">
                  <div className="typing-indicator">
                    <span></span>
                    <span></span>
                    <span></span>
                  </div>
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>

          {/* Controls */}
          <div className="widget-controls">
            {widgetConfig.voice_enabled && (
              <div className="voice-controls">
                <button
                  onClick={startListening}
                  disabled={isListening || isProcessing}
                  className={`voice-btn ${isListening ? 'listening' : ''}`}
                  style={{
                    backgroundColor: isListening ? widgetConfig.theme.secondary_color : widgetConfig.theme.primary_color,
                    color: widgetConfig.theme.background_color
                  }}
                  aria-label="Start voice input"
                >
                  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                    <path d="M12 1a3 3 0 0 0-3 3v8a3 3 0 0 0 6 0V4a3 3 0 0 0-3-3z" stroke="currentColor" strokeWidth="2"/>
                    <path d="M19 10v2a7 7 0 0 1-14 0v-2" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                    <line x1="12" y1="19" x2="12" y2="23" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                    <line x1="8" y1="23" x2="16" y2="23" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                  </svg>
                </button>
                
                {isSpeaking && (
                  <button
                    onClick={stopSpeaking}
                    className="stop-btn"
                    style={{
                      backgroundColor: widgetConfig.theme.danger || '#EF4444',
                      color: widgetConfig.theme.background_color
                    }}
                    aria-label="Stop speaking"
                  >
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                      <rect x="6" y="4" width="4" height="16" stroke="currentColor" strokeWidth="2"/>
                      <rect x="14" y="4" width="4" height="16" stroke="currentColor" strokeWidth="2"/>
                    </svg>
                  </button>
                )}
              </div>
            )}
            
            {/* Text Input Section */}
            <div className="text-input-section">
              <form onSubmit={handleTextSubmit} className="text-input-form">
                <input
                  type="text"
                  value={textInput}
                  onChange={(e) => setTextInput(e.target.value)}
                  onKeyPress={handleKeyPress}
                  placeholder="Type your message..."
                  disabled={isProcessing}
                  className="text-input"
                  style={{
                    borderColor: widgetConfig.theme.primary_color,
                    color: widgetConfig.theme.text_color
                  }}
                />
                <button
                  type="submit"
                  disabled={!textInput.trim() || isProcessing}
                  className="send-btn"
                  style={{
                    backgroundColor: widgetConfig.theme.primary_color,
                    color: widgetConfig.theme.background_color
                  }}
                  aria-label="Send message"
                >
                  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                    <path d="M22 2L11 13" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                    <path d="M22 2L15 22L11 13L2 9L22 2Z" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                  </svg>
                </button>
              </form>
            </div>
            
            <div className="widget-footer">
              <span className="powered-by">Powered by AI Voice Assistant</span>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default VoiceWidget;