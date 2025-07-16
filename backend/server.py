from fastapi import FastAPI, HTTPException, Depends, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import HTMLResponse
from pymongo import MongoClient
from groq import Groq
import os
from dotenv import load_dotenv
import logging
from typing import Optional, Dict, Any, List
import json
from datetime import datetime, timedelta
import uuid

# Import new modules
from models import *
from auth import *
from database import DatabaseService

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(title="AI Voice Assistant API", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure this properly for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize MongoDB connection
try:
    mongo_client = MongoClient(os.getenv("MONGO_URL"))
    db = mongo_client.ai_voice_assistant
    # Test connection
    mongo_client.admin.command('ping')
    logger.info("MongoDB connected successfully")
    
    # Initialize database service
    db_service = DatabaseService(mongo_client)
except Exception as e:
    logger.error(f"MongoDB connection failed: {e}")
    db = None
    db_service = None

# Initialize GROQ client
try:
    groq_api_key = os.getenv("GROQ_API_KEY")
    if groq_api_key:
        # Set the API key as environment variable for GROQ client
        os.environ["GROQ_API_KEY"] = groq_api_key
        groq_client = Groq()
        logger.info("GROQ client initialized successfully")
    else:
        logger.warning("GROQ_API_KEY not found in environment variables")
        groq_client = None
except Exception as e:
    logger.error(f"GROQ initialization failed: {e}")
    groq_client = None

# Security
security = HTTPBearer()

@app.get("/")
async def root():
    return {"message": "AI Voice Assistant API is running"}

@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "mongodb": "connected" if db is not None else "disconnected",
        "groq": "connected" if groq_client is not None else "disconnected",
        "timestamp": datetime.utcnow().isoformat()
    }

@app.post("/api/chat")
async def chat_with_ai(request: Request):
    """Main chat endpoint for the voice widget"""
    try:
        body = await request.json()
        message = body.get("message")
        session_id = body.get("session_id", str(uuid.uuid4()))
        site_id = body.get("site_id")
        
        if not message:
            raise HTTPException(status_code=400, detail="Message is required")
        
        # AI Response logic
        ai_response = ""
        model_used = "demo"
        
        if groq_client:
            try:
                # Create conversation context
                conversation_context = [
                    {
                        "role": "system",
                        "content": "You are a helpful AI assistant embedded on a website. You should be friendly, concise, and helpful. Keep responses brief and conversational, suitable for voice interaction."
                    },
                    {
                        "role": "user",
                        "content": message
                    }
                ]
                
                # Get response from GROQ
                completion = groq_client.chat.completions.create(
                    model="llama3-8b-8192",  # Using Meta's Llama model
                    messages=conversation_context,
                    max_tokens=150,
                    temperature=0.7
                )
                
                ai_response = completion.choices[0].message.content
                model_used = "llama3-8b-8192"
                
            except Exception as e:
                logger.error(f"GROQ API error: {e}")
                # Fallback to demo response
                ai_response = generate_demo_response(message)
                model_used = "demo_fallback"
        else:
            # Demo mode response
            ai_response = generate_demo_response(message)
            model_used = "demo"
        
        # Store conversation in MongoDB if available
        if db is not None:
            try:
                conversation_log = {
                    "session_id": session_id,
                    "site_id": site_id,
                    "user_message": message,
                    "ai_response": ai_response,
                    "timestamp": datetime.utcnow(),
                    "model": model_used
                }
                db.conversations.insert_one(conversation_log)
                logger.info(f"Conversation logged for session {session_id}")
            except Exception as e:
                logger.error(f"Failed to log conversation: {e}")
        
        return {
            "response": ai_response,
            "session_id": session_id,
            "timestamp": datetime.utcnow().isoformat(),
            "model": model_used
        }
        
    except Exception as e:
        logger.error(f"Chat endpoint error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

def generate_demo_response(message: str) -> str:
    """Generate demo responses for testing purposes"""
    message_lower = message.lower()
    
    if any(greeting in message_lower for greeting in ['hello', 'hi', 'hey', 'good morning', 'good afternoon']):
        return "Hello! I'm your AI voice assistant. How can I help you today?"
    
    elif any(question in message_lower for question in ['how are you', 'how do you do']):
        return "I'm doing great, thank you for asking! I'm here to help answer your questions and assist with anything you need."
    
    elif any(word in message_lower for word in ['help', 'what can you do', 'capabilities']):
        return "I can help you with questions, provide information, and have conversations. Try asking me about various topics or let me know what you'd like to know!"
    
    elif any(word in message_lower for word in ['weather', 'temperature']):
        return "I don't have access to current weather data, but I'd be happy to help you find weather information or answer other questions!"
    
    elif any(word in message_lower for word in ['time', 'date']):
        return f"I don't have access to real-time data, but I can help you with other questions. Is there anything else I can assist you with?"
    
    elif any(word in message_lower for word in ['thank', 'thanks']):
        return "You're welcome! I'm glad I could help. Is there anything else you'd like to know?"
    
    elif any(word in message_lower for word in ['bye', 'goodbye', 'see you']):
        return "Goodbye! Feel free to come back anytime if you have more questions. Have a great day!"
    
    else:
        return f"That's an interesting question about '{message}'. I'm currently in demo mode, but I'd be happy to help you explore this topic further. What specific aspect would you like to know more about?"

@app.post("/api/widget/config")
async def get_widget_config(request: Request):
    """Get widget configuration for a specific site"""
    try:
        body = await request.json()
        site_id = body.get("site_id")
        
        if not site_id:
            raise HTTPException(status_code=400, detail="Site ID is required")
        
        # Default configuration (later this will come from database)
        default_config = {
            "site_id": site_id,
            "greeting_message": "Hi there! I'm your virtual assistant. How can I help you today?",
            "bot_name": "AI Assistant",
            "theme": {
                "primary_color": "#3B82F6",
                "secondary_color": "#1E40AF",
                "text_color": "#1F2937",
                "background_color": "#FFFFFF"
            },
            "position": "bottom-right",
            "auto_greet": True,
            "voice_enabled": True,
            "language": "en-US"
        }
        
        # If database is available, try to get custom config
        if db is not None:
            try:
                custom_config = db.widget_configs.find_one({"site_id": site_id})
                if custom_config:
                    # Remove MongoDB _id field
                    custom_config.pop('_id', None)
                    default_config.update(custom_config)
            except Exception as e:
                logger.error(f"Failed to get widget config: {e}")
        
        return default_config
        
    except Exception as e:
        logger.error(f"Widget config endpoint error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/analytics/interaction")
async def log_interaction(request: Request):
    """Log widget interaction for analytics"""
    try:
        body = await request.json()
        interaction_data = {
            "site_id": body.get("site_id"),
            "session_id": body.get("session_id"),
            "interaction_type": body.get("type"),  # greeting, voice_input, text_input, etc.
            "timestamp": datetime.utcnow(),
            "user_agent": request.headers.get("user-agent"),
            "ip_address": request.client.host
        }
        
        if db is not None:
            try:
                db.interactions.insert_one(interaction_data)
                logger.info(f"Interaction logged: {interaction_data['interaction_type']}")
            except Exception as e:
                logger.error(f"Failed to log interaction: {e}")
        
        return {"status": "logged"}
        
    except Exception as e:
        logger.error(f"Analytics endpoint error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)