import React, { useState, useEffect } from 'react';
import VoiceWidget from './components/VoiceWidget';
import { loadWidgetConfig, detectSiteId, checkBrowserSupport } from './utils/widgetUtils';
import './App.css';

function App() {
  const [widgetConfig, setWidgetConfig] = useState(null);
  const [siteId, setSiteId] = useState(null);
  const [browserSupport, setBrowserSupport] = useState(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const initializeWidget = async () => {
      try {
        // Check browser support
        const support = checkBrowserSupport();
        setBrowserSupport(support);

        // Detect site ID
        const detectedSiteId = detectSiteId();
        setSiteId(detectedSiteId);

        // Load widget configuration
        const config = await loadWidgetConfig(detectedSiteId);
        setWidgetConfig(config);

        console.log('Widget initialized:', {
          siteId: detectedSiteId,
          config,
          browserSupport: support
        });
      } catch (error) {
        console.error('Widget initialization failed:', error);
        // Set default config as fallback
        setWidgetConfig({
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
          site_id: "demo"
        });
      } finally {
        setIsLoading(false);
      }
    };

    initializeWidget();
  }, []);

  if (isLoading) {
    return (
      <div className="loading-container">
        <div className="loading-spinner"></div>
        <p>Loading AI Voice Assistant...</p>
      </div>
    );
  }

  return (
    <div className="App">
      {/* Demo Page Content */}
      <header className="demo-header">
        <div className="container">
          <h1>AI Voice Assistant Demo</h1>
          <p>This is a demonstration of the AI Voice Assistant Widget</p>
        </div>
      </header>

      <main className="demo-content">
        <div className="container">
          <section className="hero-section">
            <h2>Welcome to Our Demo Website</h2>
            <p>
              This is a sample website demonstrating the AI Voice Assistant Widget. 
              You can see the widget in the bottom-right corner of your screen.
            </p>
            
            <div className="feature-grid">
              <div className="feature-card">
                <h3>🎤 Voice Interaction</h3>
                <p>Click the voice button to speak directly to the AI assistant</p>
              </div>
              
              <div className="feature-card">
                <h3>🤖 AI Powered</h3>
                <p>Powered by GROQ API with Meta's Llama models for intelligent responses</p>
              </div>
              
              <div className="feature-card">
                <h3>🎯 Customizable</h3>
                <p>Fully customizable appearance and behavior through the dashboard</p>
              </div>
            </div>
          </section>

          <section className="info-section">
            <h2>Widget Information</h2>
            <div className="info-grid">
              <div className="info-item">
                <strong>Site ID:</strong> {siteId}
              </div>
              <div className="info-item">
                <strong>Speech Recognition:</strong> {browserSupport?.speechRecognition ? '✅ Supported' : '❌ Not Supported'}
              </div>
              <div className="info-item">
                <strong>Speech Synthesis:</strong> {browserSupport?.speechSynthesis ? '✅ Supported' : '❌ Not Supported'}
              </div>
              <div className="info-item">
                <strong>Voice Enabled:</strong> {widgetConfig?.voice_enabled ? '✅ Yes' : '❌ No'}
              </div>
              <div className="info-item">
                <strong>Language:</strong> {widgetConfig?.language || 'en-US'}
              </div>
              <div className="info-item">
                <strong>Auto Greet:</strong> {widgetConfig?.auto_greet ? '✅ Yes' : '❌ No'}
              </div>
            </div>
          </section>

          <section className="instructions-section">
            <h2>How to Use the Widget</h2>
            <ol>
              <li>Click the chat icon in the bottom-right corner to open the widget</li>
              <li>The AI will automatically greet you with a welcome message</li>
              <li>Click the microphone button to start voice input</li>
              <li>Speak your question or message clearly</li>
              <li>The AI will respond both with text and voice</li>
              <li>Continue the conversation as needed</li>
            </ol>
          </section>

          <section className="support-section">
            <h2>Browser Support</h2>
            <div className="support-info">
              <p>
                The AI Voice Assistant Widget works best in modern browsers with Web Speech API support:
              </p>
              <ul>
                <li>✅ Chrome (recommended)</li>
                <li>✅ Edge</li>
                <li>✅ Safari (limited speech recognition)</li>
                <li>⚠️ Firefox (limited support)</li>
              </ul>
              <p>
                <strong>Note:</strong> Voice features require microphone permissions and HTTPS in production.
              </p>
            </div>
          </section>
        </div>
      </main>

      <footer className="demo-footer">
        <div className="container">
          <p>&copy; 2024 AI Voice Assistant Widget Demo</p>
        </div>
      </footer>

      {/* Voice Widget Component */}
      {widgetConfig && (
        <VoiceWidget config={widgetConfig} />
      )}
    </div>
  );
}

export default App;