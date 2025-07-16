// Utility functions for the voice widget

export const loadWidgetConfig = async (siteId) => {
  try {
    const response = await fetch(`${process.env.REACT_APP_BACKEND_URL}/api/widget/config`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ site_id: siteId })
    });

    if (!response.ok) {
      throw new Error('Failed to load widget configuration');
    }

    return await response.json();
  } catch (error) {
    console.error('Error loading widget config:', error);
    // Return default configuration if loading fails
    return {
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
      site_id: siteId || "default"
    };
  }
};

export const detectSiteId = () => {
  // Try to get site ID from various sources
  const urlParams = new URLSearchParams(window.location.search);
  const siteIdFromUrl = urlParams.get('site_id');
  
  if (siteIdFromUrl) {
    return siteIdFromUrl;
  }
  
  // Try to get from meta tag
  const metaTag = document.querySelector('meta[name="ai-widget-site-id"]');
  if (metaTag) {
    return metaTag.getAttribute('content');
  }
  
  // Try to get from data attribute on script tag
  const scriptTag = document.querySelector('script[data-site-id]');
  if (scriptTag) {
    return scriptTag.getAttribute('data-site-id');
  }
  
  // Fallback to domain-based ID
  return window.location.hostname.replace(/[^a-zA-Z0-9]/g, '-');
};

export const checkBrowserSupport = () => {
  const support = {
    speechRecognition: 'webkitSpeechRecognition' in window || 'SpeechRecognition' in window,
    speechSynthesis: 'speechSynthesis' in window,
    webRTC: 'MediaDevices' in window && 'getUserMedia' in window.navigator.mediaDevices
  };
  
  return support;
};

export const logAnalytics = async (eventType, data = {}) => {
  try {
    await fetch(`${process.env.REACT_APP_BACKEND_URL}/api/analytics/interaction`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        type: eventType,
        timestamp: new Date().toISOString(),
        ...data
      })
    });
  } catch (error) {
    console.error('Analytics logging failed:', error);
  }
};

// Voice utility functions
export const getAvailableVoices = () => {
  if (!('speechSynthesis' in window)) {
    return [];
  }
  
  return speechSynthesis.getVoices();
};

export const findBestVoice = (language = 'en-US', gender = 'female') => {
  const voices = getAvailableVoices();
  
  // Filter by language
  const languageVoices = voices.filter(voice => 
    voice.lang.toLowerCase().startsWith(language.toLowerCase().split('-')[0])
  );
  
  if (languageVoices.length === 0) {
    return voices[0] || null;
  }
  
  // Try to find preferred gender
  const genderKeywords = {
    female: ['female', 'woman', 'samantha', 'karen', 'moira', 'tessa', 'veena', 'fiona'],
    male: ['male', 'man', 'daniel', 'alex', 'fred', 'jorge', 'lekha', 'rishi']
  };
  
  const preferredVoice = languageVoices.find(voice => 
    genderKeywords[gender].some(keyword => 
      voice.name.toLowerCase().includes(keyword)
    )
  );
  
  return preferredVoice || languageVoices[0];
};

// Storage utilities for widget state
export const saveWidgetState = (siteId, state) => {
  try {
    const key = `ai-widget-state-${siteId}`;
    localStorage.setItem(key, JSON.stringify(state));
  } catch (error) {
    console.error('Failed to save widget state:', error);
  }
};

export const loadWidgetState = (siteId) => {
  try {
    const key = `ai-widget-state-${siteId}`;
    const stored = localStorage.getItem(key);
    return stored ? JSON.parse(stored) : null;
  } catch (error) {
    console.error('Failed to load widget state:', error);
    return null;
  }
};

// Error handling utility
export const handleWidgetError = (error, context = 'widget') => {
  console.error(`Widget error in ${context}:`, error);
  
  // Log error to analytics
  logAnalytics('error', {
    error_type: error.name,
    error_message: error.message,
    context: context,
    user_agent: navigator.userAgent,
    url: window.location.href
  });
  
  // Return user-friendly error message
  switch (error.name) {
    case 'NotAllowedError':
      return 'Microphone access was denied. Please enable it in your browser settings.';
    case 'NotSupportedError':
      return 'Voice features are not supported in your browser.';
    case 'NetworkError':
      return 'Network connection issue. Please check your internet connection.';
    default:
      return 'An unexpected error occurred. Please try again.';
  }
};