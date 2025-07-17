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

# Authentication dependency
async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> UserDB:
    """Get current authenticated user."""
    token = credentials.credentials
    email = verify_token(token)
    if not email:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token"
        )
    
    user = await db_service.get_user_by_email(email)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )
    
    return user

# Optional authentication dependency
async def get_current_user_optional(credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)) -> Optional[UserDB]:
    """Get current authenticated user (optional)."""
    if not credentials:
        return None
    
    try:
        return await get_current_user(credentials)
    except HTTPException:
        return None

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
    """Main chat endpoint for the voice widget with conversation memory"""
    try:
        body = await request.json()
        message = body.get("message")
        session_id = body.get("session_id", str(uuid.uuid4()))
        site_id = body.get("site_id")
        
        if not message:
            raise HTTPException(status_code=400, detail="Message is required")
        
        # Get site-specific configuration
        site_config = await get_site_configuration(site_id)
        
        # AI Response logic
        ai_response = ""
        model_used = "demo"
        
        if groq_client:
            try:
                # Get conversation history for context
                conversation_history = await get_conversation_history(session_id, site_id)
                
                # Create conversation context with memory
                conversation_context = [
                    {
                        "role": "system",
                        "content": create_system_prompt(site_config)
                    }
                ]
                
                # Add conversation history (last 10 messages for context)
                for msg in conversation_history[-10:]:
                    conversation_context.append({
                        "role": "user",
                        "content": msg["user_message"]
                    })
                    conversation_context.append({
                        "role": "assistant",
                        "content": msg["ai_response"]
                    })
                
                # Add current message
                conversation_context.append({
                    "role": "user",
                    "content": message
                })
                
                # Get custom API key for site or use default
                api_key = site_config.get("groq_api_key") or os.getenv("GROQ_API_KEY")
                if api_key:
                    # Create client with custom API key if provided
                    client = Groq(api_key=api_key) if site_config.get("groq_api_key") else groq_client
                    
                    # Get response from GROQ
                    completion = client.chat.completions.create(
                        model="llama3-8b-8192",  # Using Meta's Llama model
                        messages=conversation_context,
                        max_tokens=200,  # Increased for better responses
                        temperature=0.7,
                        stream=False
                    )
                    
                    ai_response = completion.choices[0].message.content
                    model_used = "llama3-8b-8192"
                    
                else:
                    raise Exception("No GROQ API key available")
                
            except Exception as e:
                logger.error(f"GROQ API error: {e}")
                # Fallback to demo response with context
                ai_response = generate_contextual_demo_response(message, conversation_history)
                model_used = "demo_fallback"
        else:
            # Demo mode response with context
            conversation_history = await get_conversation_history(session_id, site_id)
            ai_response = generate_contextual_demo_response(message, conversation_history)
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
                    "model": model_used,
                    "tokens_used": len(message.split()) + len(ai_response.split())  # Approximate token count
                }
                db.conversations.insert_one(conversation_log)
                logger.info(f"Conversation logged for session {session_id}")
            except Exception as e:
                logger.error(f"Failed to log conversation: {e}")
        
        return {
            "response": ai_response,
            "session_id": session_id,
            "timestamp": datetime.utcnow().isoformat(),
            "model": model_used,
            "conversation_length": len(conversation_history) + 1
        }
        
    except HTTPException:
        # Re-raise HTTP exceptions (like 400 for missing message)
        raise
    except Exception as e:
        logger.error(f"Chat endpoint error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================================
# DASHBOARD API ENDPOINTS
# ============================================================================

# Authentication Endpoints
@app.post("/api/auth/register", response_model=UserResponse)
async def register_user(user_data: UserCreate):
    """Register a new user."""
    if not db_service:
        raise HTTPException(status_code=500, detail="Database not available")
    
    try:
        # Check if user already exists
        existing_user = await db_service.get_user_by_email(user_data.email)
        if existing_user:
            raise HTTPException(
                status_code=400,
                detail="User with this email already exists"
            )
        
        # Create user
        user = await db_service.create_user(
            email=user_data.email,
            full_name=user_data.full_name,
            password=user_data.password
        )
        
        if not user:
            raise HTTPException(status_code=500, detail="Failed to create user")
        
        return UserResponse(
            id=user.id,
            email=user.email,
            full_name=user.full_name,
            created_at=user.created_at,
            updated_at=user.updated_at,
            is_active=user.is_active
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Registration error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/auth/login", response_model=Token)
async def login_user(login_data: LoginRequest):
    """Authenticate user and return token."""
    if not db_service:
        raise HTTPException(status_code=500, detail="Database not available")
    
    try:
        user = await db_service.authenticate_user(login_data.email, login_data.password)
        if not user:
            raise HTTPException(
                status_code=401,
                detail="Invalid email or password"
            )
        
        access_token = create_access_token(data={"sub": user.email})
        return Token(access_token=access_token, token_type="bearer")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/auth/forgot-password")
async def forgot_password(request: PasswordResetRequest):
    """Send password reset email."""
    if not db_service:
        raise HTTPException(status_code=500, detail="Database not available")
    
    try:
        user = await db_service.get_user_by_email(request.email)
        if not user:
            # Don't reveal if email exists or not
            return {"message": "If the email exists, a reset link has been sent"}
        
        reset_token = await db_service.set_reset_token(request.email)
        if reset_token:
            # TODO: Send email with reset token
            # For now, just log it (in production, send actual email)
            logger.info(f"Password reset token for {request.email}: {reset_token}")
        
        return {"message": "If the email exists, a reset link has been sent"}
    except Exception as e:
        logger.error(f"Password reset error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/auth/reset-password")
async def reset_password(reset_data: PasswordReset):
    """Reset password with token."""
    if not db_service:
        raise HTTPException(status_code=500, detail="Database not available")
    
    try:
        success = await db_service.reset_password(reset_data.token, reset_data.new_password)
        if not success:
            raise HTTPException(
                status_code=400,
                detail="Invalid or expired reset token"
            )
        
        return {"message": "Password reset successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Password reset error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/auth/me", response_model=UserResponse)
async def get_current_user_info(current_user: UserDB = Depends(get_current_user)):
    """Get current user information."""
    return UserResponse(
        id=current_user.id,
        email=current_user.email,
        full_name=current_user.full_name,
        created_at=current_user.created_at,
        updated_at=current_user.updated_at,
        is_active=current_user.is_active
    )

# Site Management Endpoints
@app.post("/api/sites", response_model=SiteResponse)
async def create_site(site_data: SiteCreate, current_user: UserDB = Depends(get_current_user)):
    """Create a new site."""
    if not db_service:
        raise HTTPException(status_code=500, detail="Database not available")
    
    try:
        # Validate domain
        if not validate_site_domain(site_data.domain):
            raise HTTPException(status_code=400, detail="Invalid domain format")
        
        # Check if domain already exists
        existing_site = await db_service.get_site_by_domain(site_data.domain)
        if existing_site:
            raise HTTPException(status_code=400, detail="Domain already exists")
        
        site = await db_service.create_site(current_user.id, site_data.dict())
        if not site:
            raise HTTPException(status_code=500, detail="Failed to create site")
        
        return SiteResponse(
            id=site.id,
            user_id=site.user_id,
            name=site.name,
            domain=site.domain,
            description=site.description,
            greeting_message=site.greeting_message,
            bot_name=site.bot_name,
            theme=SiteTheme(**site.theme),
            position=site.position,
            auto_greet=site.auto_greet,
            voice_enabled=site.voice_enabled,
            language=site.language,
            groq_api_key=site.groq_api_key,
            is_active=site.is_active,
            created_at=site.created_at,
            updated_at=site.updated_at
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Site creation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/sites", response_model=List[SiteResponse])
async def get_user_sites(current_user: UserDB = Depends(get_current_user)):
    """Get all sites for the current user."""
    if not db_service:
        raise HTTPException(status_code=500, detail="Database not available")
    
    try:
        sites = await db_service.get_user_sites(current_user.id)
        return [
            SiteResponse(
                id=site.id,
                user_id=site.user_id,
                name=site.name,
                domain=site.domain,
                description=site.description,
                greeting_message=site.greeting_message,
                bot_name=site.bot_name,
                theme=SiteTheme(**site.theme),
                position=site.position,
                auto_greet=site.auto_greet,
                voice_enabled=site.voice_enabled,
                language=site.language,
                groq_api_key=site.groq_api_key,
                is_active=site.is_active,
                created_at=site.created_at,
                updated_at=site.updated_at
            )
            for site in sites
        ]
    except Exception as e:
        logger.error(f"Get sites error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/sites/{site_id}", response_model=SiteResponse)
async def get_site(site_id: str, current_user: UserDB = Depends(get_current_user)):
    """Get a specific site."""
    if not db_service:
        raise HTTPException(status_code=500, detail="Database not available")
    
    try:
        site = await db_service.get_site_by_id(site_id, current_user.id)
        if not site:
            raise HTTPException(status_code=404, detail="Site not found")
        
        return SiteResponse(
            id=site.id,
            user_id=site.user_id,
            name=site.name,
            domain=site.domain,
            description=site.description,
            greeting_message=site.greeting_message,
            bot_name=site.bot_name,
            theme=SiteTheme(**site.theme),
            position=site.position,
            auto_greet=site.auto_greet,
            voice_enabled=site.voice_enabled,
            language=site.language,
            groq_api_key=site.groq_api_key,
            is_active=site.is_active,
            created_at=site.created_at,
            updated_at=site.updated_at
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get site error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/api/sites/{site_id}", response_model=SiteResponse)
async def update_site(site_id: str, site_data: SiteUpdate, current_user: UserDB = Depends(get_current_user)):
    """Update a site."""
    if not db_service:
        raise HTTPException(status_code=500, detail="Database not available")
    
    try:
        # Get current site
        site = await db_service.get_site_by_id(site_id, current_user.id)
        if not site:
            raise HTTPException(status_code=404, detail="Site not found")
        
        # Validate domain if provided
        if site_data.domain and not validate_site_domain(site_data.domain):
            raise HTTPException(status_code=400, detail="Invalid domain format")
        
        # Check if domain already exists (if changing domain)
        if site_data.domain and site_data.domain != site.domain:
            existing_site = await db_service.get_site_by_domain(site_data.domain)
            if existing_site:
                raise HTTPException(status_code=400, detail="Domain already exists")
        
        # Update site
        update_data = {k: v for k, v in site_data.dict().items() if v is not None}
        if update_data.get("theme"):
            update_data["theme"] = update_data["theme"].dict()
        
        success = await db_service.update_site(site_id, current_user.id, update_data)
        if not success:
            raise HTTPException(status_code=500, detail="Failed to update site")
        
        # Return updated site
        updated_site = await db_service.get_site_by_id(site_id, current_user.id)
        return SiteResponse(
            id=updated_site.id,
            user_id=updated_site.user_id,
            name=updated_site.name,
            domain=updated_site.domain,
            description=updated_site.description,
            greeting_message=updated_site.greeting_message,
            bot_name=updated_site.bot_name,
            theme=SiteTheme(**updated_site.theme),
            position=updated_site.position,
            auto_greet=updated_site.auto_greet,
            voice_enabled=updated_site.voice_enabled,
            language=updated_site.language,
            groq_api_key=updated_site.groq_api_key,
            is_active=updated_site.is_active,
            created_at=updated_site.created_at,
            updated_at=updated_site.updated_at
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Update site error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/sites/{site_id}")
async def delete_site(site_id: str, current_user: UserDB = Depends(get_current_user)):
    """Delete a site."""
    if not db_service:
        raise HTTPException(status_code=500, detail="Database not available")
    
    try:
        success = await db_service.delete_site(site_id, current_user.id)
        if not success:
            raise HTTPException(status_code=404, detail="Site not found")
        
        return {"message": "Site deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Delete site error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Analytics Endpoints
@app.get("/api/analytics/dashboard", response_model=DashboardStats)
async def get_dashboard_analytics(current_user: UserDB = Depends(get_current_user)):
    """Get dashboard analytics for the current user."""
    if not db_service:
        raise HTTPException(status_code=500, detail="Database not available")
    
    try:
        stats = await db_service.get_dashboard_stats(current_user.id)
        return stats
    except Exception as e:
        logger.error(f"Dashboard analytics error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/analytics/sites/{site_id}", response_model=AnalyticsStats)
async def get_site_analytics(site_id: str, days: int = 30, current_user: UserDB = Depends(get_current_user)):
    """Get analytics for a specific site."""
    if not db_service:
        raise HTTPException(status_code=500, detail="Database not available")
    
    try:
        # Verify site ownership
        site = await db_service.get_site_by_id(site_id, current_user.id)
        if not site:
            raise HTTPException(status_code=404, detail="Site not found")
        
        stats = await db_service.get_site_analytics(site_id, days)
        return stats
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Site analytics error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Widget Configuration Endpoints
@app.get("/api/sites/{site_id}/embed", response_model=EmbedScript)
async def get_embed_script(site_id: str, current_user: UserDB = Depends(get_current_user)):
    """Get embed script for a site."""
    if not db_service:
        raise HTTPException(status_code=500, detail="Database not available")
    
    try:
        # Verify site ownership
        site = await db_service.get_site_by_id(site_id, current_user.id)
        if not site:
            raise HTTPException(status_code=404, detail="Site not found")
        
        backend_url = os.getenv("BACKEND_URL", "https://your-domain.com")
        script_content = generate_embed_script(site_id, backend_url)
        installation_instructions = get_installation_instructions(site_id)
        
        return EmbedScript(
            site_id=site_id,
            script_content=script_content,
            installation_instructions=installation_instructions
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Embed script error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Widget endpoint (for embedded widgets)
@app.get("/widget", response_class=HTMLResponse)
async def widget_page(site_id: str):
    """Serve the widget page for embedding."""
    if not db_service:
        raise HTTPException(status_code=500, detail="Database not available")
    
    try:
        config = await db_service.get_site_config(site_id)
        if not config:
            raise HTTPException(status_code=404, detail="Site not found")
        
        # Return widget HTML page
        html_content = f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>AI Voice Assistant Widget</title>
            <style>
                body {{
                    margin: 0;
                    padding: 0;
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                    background: transparent;
                }}
                .widget-container {{
                    width: 100%;
                    height: 100vh;
                    display: flex;
                    flex-direction: column;
                }}
            </style>
        </head>
        <body>
            <div class="widget-container">
                <div id="root"></div>
            </div>
            <script>
                window.WIDGET_CONFIG = {json.dumps(config)};
                window.BACKEND_URL = "{os.getenv('BACKEND_URL', 'http://localhost:8001')}";
            </script>
            <script src="/static/widget.js"></script>
        </body>
        </html>
        """
        
        return HTMLResponse(content=html_content)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Widget page error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Updated analytics endpoint to work with new database
@app.post("/api/analytics/interaction")
async def log_interaction(request: Request):
    """Log widget interaction for analytics."""
    try:
        body = await request.json()
        
        if not db_service:
            # Just return success if database not available
            return {"status": "logged"}
        
        interaction_data = {
            "site_id": body.get("site_id"),
            "session_id": body.get("session_id"),
            "interaction_type": body.get("type"),
            "user_message": body.get("user_message"),
            "ai_response": body.get("ai_response"),
            "timestamp": datetime.utcnow(),
            "user_agent": request.headers.get("user-agent"),
            "ip_address": request.client.host
        }
        
        await db_service.create_interaction(interaction_data)
        return {"status": "logged"}
        
    except Exception as e:
        logger.error(f"Analytics endpoint error: {e}")
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
        
        # Default configuration (works for demo and fallback)
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
        if db_service:
            try:
                config = await db_service.get_site_config(site_id)
                if config:
                    return config
            except Exception as e:
                logger.error(f"Failed to get widget config from database: {e}")
        
        # For demo sites or when database lookup fails, return default config
        return default_config
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Widget config endpoint error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)