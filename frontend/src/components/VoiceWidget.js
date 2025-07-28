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
  const [platformInfo, setPlatformInfo] = useState(null);
  const [voiceMode, setVoiceMode] = useState('full'); // 'full', 'speech-only', 'text-only'
  const [permissionGranted, setPermissionGranted] = useState(false);
  const [retryCount, setRetryCount] = useState(0);
  
  
  // Platform detection and configuration
  useEffect(() => {
    const detectPlatform = () => {
      const userAgent = navigator.userAgent.toLowerCase();
      const platform = navigator.platform.toLowerCase();
      
      const info = {
        isIOS: /iphone|ipad|ipod/.test(userAgent) || (platform === 'macintel' && navigator.maxTouchPoints > 1),
        isAndroid: /android/.test(userAgent),
        isMobile: /mobile|android|iphone|ipad|ipod/.test(userAgent),
        isWindows: /windows|win32|win64/.test(platform),
        isLinux: /linux/.test(platform),
        isMac: /mac/.test(platform),
        browser: getBrowserInfo(userAgent),
        supports: {
          speechRecognition: 'webkitSpeechRecognition' in window || 'SpeechRecognition' in window,
          speechSynthesis: 'speechSynthesis' in window,
          mediaDevices: 'MediaDevices' in window && 'getUserMedia' in navigator.mediaDevices,
          webRTC: 'RTCPeerConnection' in window
        }
      };
      
      // Set voice mode based on platform capabilities
      if (info.isIOS) {
        // iOS Safari has limited speech recognition support
        setVoiceMode('speech-only');
      } else if (info.supports.speechRecognition && info.supports.speechSynthesis && info.supports.mediaDevices) {
        setVoiceMode('full');
      } else if (info.supports.speechSynthesis) {
        setVoiceMode('speech-only');
      } else {
        setVoiceMode('text-only');
      }
      
      console.log('Platform detected:', info);
      console.log('Voice mode set to:', info.isIOS ? 'speech-only' : 'full');
      
      return info;
    };
    
    const getBrowserInfo = (userAgent) => {
      if (userAgent.includes('chrome')) return 'chrome';
      if (userAgent.includes('firefox')) return 'firefox';
      if (userAgent.includes('safari') && !userAgent.includes('chrome')) return 'safari';
      if (userAgent.includes('edge')) return 'edge';
      return 'unknown';
    };
    
    const info = detectPlatform();
    setPlatformInfo(info);
  }, []);

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

  // Enhanced speech recognition initialization with platform-specific configuration
  useEffect(() => {
    if (!platformInfo) return;
    
    console.log('🎯 Initializing speech recognition with platform-specific settings...');
    
    // Check for speech recognition support
    if (platformInfo.supports.speechRecognition && (voiceMode === 'full' || voiceMode === 'speech-only')) {
      console.log('✅ Speech recognition API available');
      setSpeechSupported(true);
      
      const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
      recognitionRef.current = new SpeechRecognition();
      
      // Platform-specific configuration
      if (platformInfo.isIOS) {
        // iOS-specific settings
        recognitionRef.current.continuous = false;
        recognitionRef.current.interimResults = false; // iOS doesn't handle interim results well
        recognitionRef.current.maxAlternatives = 1;
        console.log('🍎 iOS speech recognition configured');
      } else if (platformInfo.isAndroid) {
        // Android-specific settings
        recognitionRef.current.continuous = false;
        recognitionRef.current.interimResults = true;
        recognitionRef.current.maxAlternatives = 3;
        console.log('🤖 Android speech recognition configured');
      } else {
        // Desktop (Windows/Linux/Mac) settings
        recognitionRef.current.continuous = false;
        recognitionRef.current.interimResults = true;
        recognitionRef.current.maxAlternatives = 1;
        console.log('🖥️ Desktop speech recognition configured');
      }
      
      recognitionRef.current.lang = widgetConfig.language;

      recognitionRef.current.onstart = () => {
        console.log('🎤 Speech recognition started');
        setIsListening(true);
        logInteraction('voice_start');
        
        // Add helpful message when first time using voice
        if (messages.length === 1 && !platformInfo.isIOS) { // Skip on iOS to avoid confusion
          addMessage('system', '🎤 I\'m listening! Please speak clearly and I\'ll respond to your voice.');
        }
      };

      recognitionRef.current.onresult = (event) => {
        console.log('🗣️ Speech recognition result:', event);
        
        // Handle results differently based on platform
        let transcript = '';
        
        if (platformInfo.isIOS) {
          // iOS: Only process final results
          for (let i = event.resultIndex; i < event.results.length; i++) {
            if (event.results[i].isFinal) {
              transcript = event.results[i][0].transcript.trim();
              break;
            }
          }
        } else {
          // Other platforms: Handle interim results for better UX
          for (let i = event.resultIndex; i < event.results.length; i++) {
            if (event.results[i].isFinal) {
              transcript = event.results[i][0].transcript.trim();
              break;
            } else {
              // Show interim results as preview
              const interimTranscript = event.results[i][0].transcript.trim();
              if (interimTranscript) {
                // Could show interim results in UI (optional)
                console.log('📝 Interim:', interimTranscript);
              }
            }
          }
        }
        
        console.log('📝 Final transcript:', transcript);
        
        // Only process if we have a final result with meaningful content
        if (transcript && (platformInfo.isIOS || event.results[event.results.length - 1].isFinal)) {
          setIsListening(false);
          setRetryCount(0); // Reset retry count on successful recognition
          handleUserMessage(transcript, 'voice');
        }
      };

      recognitionRef.current.onerror = (event) => {
        console.error('❌ Speech recognition error:', event.error, event);
        setIsListening(false);
        
        // Platform-specific error handling
        let errorMessage = 'Sorry, I had trouble hearing you. Please try again.';
        
        if (platformInfo.isIOS) {
          switch (event.error) {
            case 'no-speech':
              errorMessage = '🔇 Tap and hold the microphone, then speak clearly.';
              break;
            case 'not-allowed':
              errorMessage = '🚫 Please allow microphone access in Safari settings and try again.';
              break;
            case 'network':
              errorMessage = '🌐 Voice recognition requires internet connection. Please check your connection.';
              break;
            default:
              errorMessage = '⚠️ Voice recognition failed. Please try typing your message instead.';
          }
        } else {
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
        }
        
        addMessage('system', errorMessage);
        
        // Auto-retry logic for certain errors (except permission-related)
        if (!['not-allowed', 'service-not-allowed'].includes(event.error) && retryCount < 2) {
          setTimeout(() => {
            setRetryCount(prev => prev + 1);
            console.log(`🔄 Auto-retrying speech recognition (attempt ${retryCount + 1}/2)`);
          }, 2000);
        }
      };

      recognitionRef.current.onend = () => {
        console.log('🔇 Speech recognition ended');
        setIsListening(false);
        
        // Platform-specific end handling
        if (platformInfo.isIOS) {
          // iOS: Show helpful message about tap-to-speak
          setTimeout(() => {
            if (!isListening && messages.length > 1) {
              console.log('💭 iOS: Speech recognition ended, ready for next interaction');
            }
          }, 500);
        } else {
          // Other platforms: Standard end handling
          setTimeout(() => {
            if (!isListening && messages.length > 1) {
              console.log('💭 Speech recognition ended without result, ready for retry');
            }
          }, 500);
        }
      };
      
      console.log('✅ Speech recognition initialized successfully');
    } else {
      console.log('❌ Speech recognition API not available or disabled for this platform');
      setSpeechSupported(false);
    }

    // Enhanced speech synthesis initialization
    if (platformInfo.supports.speechSynthesis) {
      console.log('✅ Speech synthesis API available');
      synthesisRef.current = window.speechSynthesis;
      
      // Platform-specific synthesis settings
      if (platformInfo.isIOS) {
        // iOS requires user interaction for speech synthesis
        console.log('🍎 iOS speech synthesis configured (requires user interaction)');
      } else {
        console.log('🖥️ Desktop speech synthesis configured');
      }
    } else {
      console.log('❌ Speech synthesis API not available');
    }
  }, [platformInfo, widgetConfig.language, voiceMode]);

  // Platform-aware auto-greet when widget opens
  useEffect(() => {
    if (widgetConfig.auto_greet && !hasGreeted && isOpen && platformInfo) {
      const greetingTimer = setTimeout(() => {
        console.log('Triggering auto-greeting...');
        
        // Platform-specific voice greeting
        if (widgetConfig.voice_enabled && synthesisRef.current && (voiceMode === 'full' || voiceMode === 'speech-only')) {
          // iOS requires user interaction for speech synthesis
          if (platformInfo.isIOS) {
            console.log('iOS: Skipping auto-voice greeting, requires user interaction');
            // Add message suggesting user to tap for voice
            addMessage('bot', widgetConfig.greeting_message);
            addMessage('system', '🍎 Tap the microphone to hear my voice!');
          } else {
            // Desktop and Android can auto-speak
            try {
              speakMessage(widgetConfig.greeting_message);
            } catch (error) {
              console.error('Auto-speak error:', error);
            }
          }
        }
        
        addMessage('bot', widgetConfig.greeting_message);
        setHasGreeted(true);
        logInteraction('auto_greeting');
      }, 500);

      return () => clearTimeout(greetingTimer);
    }
  }, [widgetConfig.auto_greet, widgetConfig.voice_enabled, widgetConfig.greeting_message, hasGreeted, isOpen, platformInfo, voiceMode]);

  // Enhanced immediate auto-voice greeting on page load with platform detection
  useEffect(() => {
    let enableAutoVoice;

    if (widgetConfig.auto_greet && widgetConfig.voice_enabled && !hasGreeted && synthesisRef.current && platformInfo) {
      // Skip immediate auto-voice for iOS due to autoplay restrictions
      if (platformInfo.isIOS) {
        console.log('🍎 iOS: Skipping immediate auto-voice greeting due to autoplay restrictions');
        return;
      }
      
      const immediateVoiceTimer = setTimeout(() => {
        console.log('🔊 Starting immediate auto-voice greeting on page load...');
        
        // Create a user interaction handler to enable autoplay
        enableAutoVoice = () => {
          if (widgetConfig.voice_enabled && synthesisRef.current && !hasGreeted && !platformInfo.isIOS) {
            try {
              speakMessage(widgetConfig.greeting_message);
              setHasGreeted(true);
              logInteraction('immediate_voice_greeting');
              console.log('✅ Immediate voice greeting activated');
            } catch (error) {
              console.error('Immediate voice greeting error:', error);
            }
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
  }, [widgetConfig.auto_greet, widgetConfig.voice_enabled, widgetConfig.greeting_message, hasGreeted, platformInfo]);

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

  // Enhanced speech synthesis with platform-specific voice selection
  const speakMessage = (text) => {
    if (!synthesisRef.current) return;

    // Cancel any ongoing speech
    synthesisRef.current.cancel();

    const utterance = new SpeechSynthesisUtterance(text);
    utterance.lang = widgetConfig.language;
    
    // Platform-specific voice configuration
    if (platformInfo?.isIOS) {
      // iOS-specific settings
      utterance.rate = 0.8; // Slightly slower for iOS
      utterance.pitch = 1.0;
      utterance.volume = 0.8; // Slightly quieter for iOS
      
      // Try to use a better voice for iOS
      const voices = synthesisRef.current.getVoices();
      const iosVoice = voices.find(voice => 
        voice.lang.startsWith(widgetConfig.language.split('-')[0]) && 
        (voice.name.includes('Samantha') || voice.name.includes('Karen'))
      );
      if (iosVoice) {
        utterance.voice = iosVoice;
      }
    } else if (platformInfo?.isAndroid) {
      // Android-specific settings
      utterance.rate = 0.9;
      utterance.pitch = 1.0;
      utterance.volume = 1.0;
      
      const voices = synthesisRef.current.getVoices();
      const androidVoice = voices.find(voice => 
        voice.lang.startsWith(widgetConfig.language.split('-')[0])
      );
      if (androidVoice) {
        utterance.voice = androidVoice;
      }
    } else {
      // Desktop settings
      utterance.rate = 0.9;
      utterance.pitch = 1.0;
      utterance.volume = 1.0;
      
      // Try to find a good quality voice
      const voices = synthesisRef.current.getVoices();
      const desktopVoice = voices.find(voice => 
        voice.lang.startsWith(widgetConfig.language.split('-')[0]) && 
        voice.localService === false // Prefer cloud voices for better quality
      ) || voices.find(voice => 
        voice.lang.startsWith(widgetConfig.language.split('-')[0])
      );
      
      if (desktopVoice) {
        utterance.voice = desktopVoice;
      }
    }

    utterance.onstart = () => {
      setIsSpeaking(true);
      console.log('🔊 Speech synthesis started');
    };
    
    utterance.onend = () => {
      setIsSpeaking(false);
      console.log('🔇 Speech synthesis ended');
    };
    
    utterance.onerror = (event) => {
      setIsSpeaking(false);
      console.error('❌ Speech synthesis error:', event);
    };

    // Platform-specific speech synthesis execution
    if (platformInfo?.isIOS) {
      // iOS requires user interaction for speech synthesis
      // The speech will only work if this is called within a user interaction context
      try {
        synthesisRef.current.speak(utterance);
      } catch (error) {
        console.error('iOS speech synthesis error:', error);
      }
    } else {
      // Other platforms can speak directly
      synthesisRef.current.speak(utterance);
    }
  };

  // Enhanced handleUserMessage with real-time optimization and retry logic
  const handleUserMessage = async (text, type = 'text') => {
    if (!text.trim() || !visitorId) return;

    setIsProcessing(true);
    addMessage('user', text);
    logInteraction(type === 'voice' ? 'voice_input' : 'text_input');

    const maxRetries = 3;
    let attempt = 0;
    
    while (attempt < maxRetries) {
      try {
        // Dynamic timeout based on platform and connection
        const timeout = platformInfo?.isMobile ? 8000 : 10000; // Shorter timeout for mobile
        
        // Use AbortController for request timeout
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), timeout);

        const response = await fetch(`${process.env.REACT_APP_BACKEND_URL}/api/chat`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            message: text,
            session_id: sessionId,
            site_id: widgetConfig.site_id,
            visitor_id: visitorId,
            platform: platformInfo?.browser || 'unknown',
            voice_mode: voiceMode
          }),
          signal: controller.signal
        });

        clearTimeout(timeoutId);

        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data = await response.json();
        addMessage('bot', data.response);

        // Enhanced speech synthesis with platform-specific handling
        if (widgetConfig.voice_enabled && synthesisRef.current && (voiceMode === 'full' || voiceMode === 'speech-only')) {
          // Cancel any ongoing speech before speaking new response
          synthesisRef.current.cancel();
          
          // Platform-specific delay for speech synthesis
          const speechDelay = platformInfo?.isIOS ? 300 : 100;
          
          setTimeout(() => {
            speakMessage(data.response);
          }, speechDelay);
        }

        logInteraction('ai_response');
        break; // Success, exit retry loop
        
      } catch (error) {
        attempt++;
        console.error(`Chat error (attempt ${attempt}/${maxRetries}):`, error);
        
        if (attempt === maxRetries) {
          // Final attempt failed
          if (error.name === 'AbortError') {
            addMessage('system', '⏰ Request timeout. The server is taking too long to respond. Please try again.');
          } else if (error.message.includes('Failed to fetch')) {
            addMessage('system', '🌐 Network connection issue. Please check your internet connection and try again.');
          } else if (error.message.includes('500')) {
            addMessage('system', '🔧 Server error. Please try again in a moment.');
          } else {
            addMessage('system', '❌ Sorry, I encountered an error. Please try again.');
          }
        } else {
          // Retry with exponential backoff
          const delay = Math.min(1000 * Math.pow(2, attempt - 1), 3000);
          console.log(`🔄 Retrying in ${delay}ms...`);
          await new Promise(resolve => setTimeout(resolve, delay));
        }
      }
    }
    
    setIsProcessing(false);
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

  // Enhanced startListening with platform-specific microphone permission handling
  const startListening = async () => {
    console.log('🎤 startListening called');
    console.log('speechSupported:', speechSupported);
    console.log('recognitionRef.current:', recognitionRef.current);
    console.log('platformInfo:', platformInfo);
    
    if (!speechSupported || !recognitionRef.current) {
      console.error('❌ Speech recognition not supported or ref is null');
      addMessage('system', '❌ Speech recognition is not supported in your browser. Please use the text input instead.');
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
      
      // Platform-specific microphone permission handling
      if (platformInfo?.isMobile || platformInfo?.isIOS) {
        // Mobile/iOS: Must request permission first and handle with user interaction
        if (navigator.mediaDevices && navigator.mediaDevices.getUserMedia) {
          try {
            const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
            console.log('🎤 Mobile microphone permission granted');
            setPermissionGranted(true);
            
            // Stop the stream immediately, we just needed permission
            stream.getTracks().forEach(track => track.stop());
            
            // Add delay for mobile platforms to ensure permission is fully processed
            await new Promise(resolve => setTimeout(resolve, 500));
            
            startRecognitionWithFeedback();
          } catch (error) {
            console.error('❌ Mobile microphone permission error:', error);
            handlePermissionError(error);
          }
        } else {
          // Fallback for older mobile browsers
          startRecognitionWithFeedback();
        }
      } else {
        // Desktop: Can try direct recognition start with fallback permission request
        if (navigator.mediaDevices && navigator.mediaDevices.getUserMedia) {
          navigator.mediaDevices.getUserMedia({ audio: true })
            .then(() => {
              console.log('🎤 Desktop microphone permission granted');
              setPermissionGranted(true);
              startRecognitionWithFeedback();
            })
            .catch((error) => {
              console.error('❌ Desktop microphone permission error:', error);
              if (error.name === 'NotAllowedError') {
                handlePermissionError(error);
              } else {
                // Try to start recognition anyway (fallback for older browsers)
                startRecognitionWithFeedback();
              }
            });
        } else {
          // Fallback for browsers without getUserMedia
          startRecognitionWithFeedback();
        }
      }
      
    } catch (error) {
      console.error('❌ Recognition start error:', error);
      setIsListening(false);
      handlePermissionError(error);
    }
  };

  const handlePermissionError = (error) => {
    let errorMessage = '';
    
    if (platformInfo?.isIOS) {
      switch (error.name) {
        case 'NotAllowedError':
          errorMessage = '🚫 Please allow microphone access in Safari settings: Settings > Safari > Microphone > Allow';
          break;
        case 'NotFoundError':
          errorMessage = '🎤 No microphone found. Please connect a microphone or use the text input.';
          break;
        case 'NotSupportedError':
          errorMessage = '❌ Voice recognition is not supported in your browser version. Please use the text input.';
          break;
        default:
          errorMessage = '⚠️ Voice recognition failed. Please try typing your message instead.';
      }
    } else if (platformInfo?.isAndroid) {
      switch (error.name) {
        case 'NotAllowedError':
          errorMessage = '🚫 Please allow microphone access when prompted by your browser.';
          break;
        case 'NotFoundError':
          errorMessage = '🎤 No microphone found. Please check your microphone is connected.';
          break;
        default:
          errorMessage = '⚠️ Voice recognition failed. Please try again or use the text input.';
      }
    } else {
      // Desktop
      switch (error.name) {
        case 'NotAllowedError':
          errorMessage = '🚫 Microphone access denied. Please allow microphone permission in your browser and try again.';
          break;
        case 'NotFoundError':
          errorMessage = '🎤 No microphone found. Please check your microphone is connected and working.';
          break;
        case 'NotSupportedError':
          errorMessage = '❌ Speech recognition is not supported in your browser.';
          break;
        default:
          errorMessage = `❌ Error starting voice recognition: ${error.message}. Please try again.`;
      }
    }
    
    addMessage('system', errorMessage);
  };

  const startRecognitionWithFeedback = () => {
    try {
      setIsListening(true); // Set listening state immediately for UI feedback
      recognitionRef.current.start();
      console.log('✅ Speech recognition start() called successfully');
      
      // Platform-specific timeout handling
      const timeout = platformInfo?.isIOS ? 8000 : 
                     platformInfo?.isMobile ? 10000 : 
                     12000; // Longer timeout for desktop
      
      setTimeout(() => {
        if (isListening && recognitionRef.current) {
          console.log(`⏰ Speech recognition timeout (${timeout}ms), stopping...`);
          try {
            recognitionRef.current.stop();
          } catch (e) {
            console.error('Error stopping recognition on timeout:', e);
          }
          setIsListening(false);
          
          const timeoutMessage = platformInfo?.isIOS ? 
            '⏰ Listening timeout. Please tap the microphone and speak immediately.' :
            '⏰ Listening timeout. Please click the microphone and try speaking again.';
          
          addMessage('system', timeoutMessage);
        }
      }, timeout);
      
    } catch (error) {
      console.error('❌ startRecognitionWithFeedback error:', error);
      setIsListening(false);
      throw error;
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

          {/* Enhanced Voice Controls with Platform-Specific UI */}
          <div className="widget-controls">
            {widgetConfig.voice_enabled && (voiceMode === 'full' || voiceMode === 'speech-only') && (
              <div className="voice-controls">
                {/* Platform-specific voice button */}
                <button
                  onClick={startListening}
                  disabled={isListening || isProcessing}
                  className={`voice-btn ${isListening ? 'listening' : ''}`}
                  style={{
                    backgroundColor: isListening ? widgetConfig.theme.secondary_color : widgetConfig.theme.primary_color,
                    color: widgetConfig.theme.background_color
                  }}
                  aria-label={platformInfo?.isIOS ? "Tap to speak" : "Click to speak"}
                  title={platformInfo?.isIOS ? "Tap and speak immediately" : "Click and speak clearly"}
                >
                  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                    <path d="M12 1a3 3 0 0 0-3 3v8a3 3 0 0 0 6 0V4a3 3 0 0 0-3-3z" stroke="currentColor" strokeWidth="2"/>
                    <path d="M19 10v2a7 7 0 0 1-14 0v-2" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                    <line x1="12" y1="19" x2="12" y2="23" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                    <line x1="8" y1="23" x2="16" y2="23" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                  </svg>
                </button>
                
                {/* Voice Mode Indicator */}
                {voiceMode === 'speech-only' && (
                  <div className="voice-mode-indicator" title="Voice output only (speech recognition limited)">
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                      <path d="M11 5L6 9H2v6h4l5 4V5z" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                      <path d="M19.07 4.93a10 10 0 0 1 0 14.14M15.54 8.46a5 5 0 0 1 0 7.07" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                    </svg>
                  </div>
                )}
                
                {/* Platform-specific help text */}
                {platformInfo?.isIOS && (
                  <div className="ios-help-text">
                    <small>Tap mic, speak immediately</small>
                  </div>
                )}
                
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
            
            {/* Text input always available as fallback */}
            <div className="text-input-section">
              <form onSubmit={handleTextSubmit} className="text-input-form">
                <input
                  type="text"
                  value={textInput}
                  onChange={(e) => setTextInput(e.target.value)}
                  onKeyPress={handleKeyPress}
                  placeholder={
                    voiceMode === 'text-only' ? 'Type your message...' :
                    platformInfo?.isIOS ? 'Type message or tap mic to speak...' :
                    'Type message or click mic to speak...'
                  }
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