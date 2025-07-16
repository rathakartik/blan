from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pymongo import MongoClient
from groq import Groq
import os
from dotenv import load_dotenv
import logging
from typing import Optional, Dict, Any
import json
from datetime import datetime
import uuid

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
except Exception as e:
    logger.error(f"MongoDB connection failed: {e}")
    db = None

# Initialize GROQ client
try:
    groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))
    logger.info("GROQ client initialized successfully")
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
        "mongodb": "connected" if db else "disconnected",
        "groq": "connected" if groq_client else "disconnected",
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
        
        if not groq_client:
            raise HTTPException(status_code=503, detail="GROQ API not available")
        
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
        
        # Store conversation in MongoDB if available
        if db:
            try:
                conversation_log = {
                    "session_id": session_id,
                    "site_id": site_id,
                    "user_message": message,
                    "ai_response": ai_response,
                    "timestamp": datetime.utcnow(),
                    "model": "llama3-8b-8192"
                }
                db.conversations.insert_one(conversation_log)
                logger.info(f"Conversation logged for session {session_id}")
            except Exception as e:
                logger.error(f"Failed to log conversation: {e}")
        
        return {
            "response": ai_response,
            "session_id": session_id,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Chat endpoint error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

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
        if db:
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
        
        if db:
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