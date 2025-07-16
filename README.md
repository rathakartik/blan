# AI Voice Assistant Widget

A fully functional AI-powered voice assistant widget that can be embedded on any website to provide interactive voice conversations with visitors.

## 🎯 Features

### Core Functionality
- **Voice Interaction**: Real-time speech-to-text and text-to-speech using Web Speech API
- **AI Conversations**: Powered by GROQ API with Meta's Llama models
- **Auto-Greeting**: Proactively greets visitors when they land on the website
- **Session Management**: Maintains conversation context across interactions
- **Analytics**: Tracks user interactions and conversation metrics

### Customization
- **Theme Customization**: Configurable colors, bot name, and greeting messages
- **Positioning**: Flexible widget placement (bottom-right, bottom-left)
- **Voice Configuration**: Customizable voice settings and language support
- **Responsive Design**: Works seamlessly on desktop and mobile devices

### Technical Features
- **Cross-Browser Support**: Works in Chrome, Edge, Safari, and Firefox
- **MongoDB Integration**: Stores conversations and analytics data
- **RESTful API**: Clean API endpoints for widget configuration and interaction
- **Demo Mode**: Fallback intelligent responses when AI API is not available

## 🏗️ Architecture

### Tech Stack
- **Frontend**: React 18, Tailwind CSS, Web Speech API
- **Backend**: FastAPI (Python), MongoDB, GROQ API
- **Voice Services**: Web Speech API (Browser Native)
- **AI Model**: Meta Llama 3 (8B) via GROQ API

### Project Structure
```
/app/
├── backend/                 # FastAPI backend
│   ├── server.py           # Main server application
│   ├── requirements.txt    # Python dependencies
│   ├── .env               # Environment variables
│   └── .env.example       # Environment template
├── frontend/               # React frontend
│   ├── src/
│   │   ├── components/
│   │   │   ├── VoiceWidget.js    # Main widget component
│   │   │   └── VoiceWidget.css   # Widget styles
│   │   ├── utils/
│   │   │   └── widgetUtils.js    # Utility functions
│   │   ├── App.js              # Demo application
│   │   └── index.js            # Entry point
│   ├── package.json            # Node dependencies
│   └── .env                    # Frontend environment
├── supervisord.conf            # Service management
├── TASK_LIST.md               # Development progress
└── README.md                  # This file
```

## 🚀 Getting Started

### Prerequisites
- Python 3.11+
- Node.js 18+
- MongoDB
- GROQ API key (optional for demo mode)

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd ai-voice-assistant
   ```

2. **Backend Setup**
   ```bash
   cd backend
   pip install -r requirements.txt
   cp .env.example .env
   # Edit .env with your configuration
   ```

3. **Frontend Setup**
   ```bash
   cd frontend
   yarn install
   ```

4. **Start Services**
   ```bash
   # From project root
   sudo supervisorctl restart all
   ```

### Configuration

#### Environment Variables

**Backend (.env)**
```bash
MONGO_URL=mongodb://localhost:27017/ai_voice_assistant
SECRET_KEY=your-secret-key-here
GROQ_API_KEY=your-groq-api-key-here
```

**Frontend (.env)**
```bash
REACT_APP_BACKEND_URL=http://localhost:8001
```

#### GROQ API Setup
1. Visit [GROQ Console](https://console.groq.com/)
2. Create an account and get your API key
3. Add the key to your backend `.env` file

## 🎮 Usage

### Demo Mode
Visit `http://localhost:3000` to see the widget in action on a demo website.

### Widget Integration
To embed the widget on your website:

1. **Get Widget Configuration**
   ```javascript
   POST /api/widget/config
   {
     "site_id": "your-site-id"
   }
   ```

2. **Add Widget to Your Site**
   ```html
   <!-- Add to your HTML <head> -->
   <meta name="ai-widget-site-id" content="your-site-id">
   
   <!-- Add widget script -->
   <script src="http://localhost:3000/widget.js"></script>
   ```

### API Endpoints

#### Chat Endpoint
```bash
POST /api/chat
Content-Type: application/json

{
  "message": "Hello, how can you help me?",
  "session_id": "user-session-123",
  "site_id": "demo"
}
```

#### Widget Configuration
```bash
POST /api/widget/config
Content-Type: application/json

{
  "site_id": "demo"
}
```

#### Analytics Logging
```bash
POST /api/analytics/interaction
Content-Type: application/json

{
  "site_id": "demo",
  "session_id": "user-session-123",
  "type": "voice_input"
}
```

## 🎨 Widget Customization

### Theme Configuration
```javascript
{
  "theme": {
    "primary_color": "#3B82F6",
    "secondary_color": "#1E40AF",
    "text_color": "#1F2937",
    "background_color": "#FFFFFF"
  },
  "position": "bottom-right",
  "greeting_message": "Hi! I'm your AI assistant. How can I help?",
  "bot_name": "AI Assistant",
  "voice_enabled": true,
  "language": "en-US"
}
```

### Browser Support
- ✅ Chrome (full support)
- ✅ Edge (full support)
- ✅ Safari (limited speech recognition)
- ⚠️ Firefox (limited voice features)

## 🔧 Development

### Running Tests
```bash
# Backend testing
python backend_test.py

# Frontend testing (manual)
# Visit http://localhost:3000 and test widget functionality
```

### Demo Mode
The system automatically falls back to demo mode when GROQ API is not available, providing intelligent responses for common queries.

### Adding New Features

1. **Backend Changes**
   - Add new endpoints in `backend/server.py`
   - Update database models as needed
   - Test with the provided test script

2. **Frontend Changes**
   - Modify `VoiceWidget.js` component
   - Update styles in `VoiceWidget.css`
   - Add utility functions in `widgetUtils.js`

## 📊 Analytics

The system tracks:
- Widget interactions (opens, closes, voice inputs)
- Conversation logs with timestamps
- User engagement metrics
- Popular questions and responses

## 🚦 Status

### ✅ Completed Features
- Voice recognition and synthesis
- AI conversation engine
- Widget customization
- Analytics logging
- Demo mode fallback
- Cross-browser compatibility
- MongoDB integration
- API endpoints
- Security measures

### 🔄 Next Steps (Dashboard Development)
- User authentication system
- Site management interface
- Widget configuration dashboard
- Analytics visualization
- Team collaboration features
- Subscription management

## 🔒 Security

- Environment variables for sensitive data
- Input validation on all endpoints
- CORS configuration
- Rate limiting (planned)
- API key management

## 📝 License

This project is licensed under the MIT License.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 🆘 Support

For issues and questions:
1. Check the browser console for errors
2. Verify API endpoints are responding
3. Ensure MongoDB is running
4. Check GROQ API key configuration

## 🎯 Roadmap

- [ ] Dashboard UI for widget management
- [ ] Multi-language support
- [ ] Advanced analytics dashboard
- [ ] Team collaboration features
- [ ] Mobile app integration
- [ ] Advanced voice customization
- [ ] Plugin system for extensions
