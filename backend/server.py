from fastapi import FastAPI, HTTPException, Depends, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
# from starlette.middleware.base import BaseHTTPMiddleware  # Temporarily disabled
from pymongo import MongoClient
from groq import Groq
import os
from dotenv import load_dotenv
import logging
from typing import Optional, Dict, Any, List
import json
from datetime import datetime, timedelta
import uuid
import re
import time
from collections import defaultdict
import asyncio

import asyncio
import aiohttp
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse, parse_qs
from typing import Dict, List, Set, Optional, Any, Tuple
import json
import re
from datetime import datetime, timedelta
from collections import defaultdict, Counter
import textstat
import logging
from dataclasses import dataclass, asdict
import hashlib
import nltk
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import KMeans
import numpy as np

# Import new modules
from models import *
from auth import *
from database import DatabaseService
from website_intelligence import WebsiteIntelligenceEngine

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/var/log/supervisor/backend.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Rate limiting storage
rate_limits = defaultdict(lambda: defaultdict(list))

# Security configurations
MAX_MESSAGE_LENGTH = 1000
MAX_REQUESTS_PER_MINUTE = 60
MAX_CHAT_REQUESTS_PER_MINUTE = 20
BLOCKED_PATTERNS = [
    r'<script[^>]*>.*?</script>',
    r'javascript:',
    r'on\w+\s*=',
    r'eval\s*\(',
    r'document\.',
    r'window\.',
]

# Initialize FastAPI app
app = FastAPI(
    title="AI Voice Assistant API", 
    version="1.0.0",
    description="Production-ready AI Voice Assistant API with enhanced security"
)

# Mount static files for widget assets
app.mount("/static", StaticFiles(directory="/app/backend/static"), name="static")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure this properly for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================================================
# SECURITY & RATE LIMITING MIDDLEWARE - TEMPORARILY DISABLED FOR DEBUGGING
# ============================================================================

def get_client_ip(request: Request) -> str:
    """Get client IP address from request"""
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host

def is_rate_limited(client_ip: str, endpoint: str, max_requests: int = MAX_REQUESTS_PER_MINUTE) -> bool:
    """Check if client IP is rate limited for specific endpoint"""
    current_time = time.time()
    minute_ago = current_time - 60
    
    # Clean old entries
    rate_limits[client_ip][endpoint] = [
        req_time for req_time in rate_limits[client_ip][endpoint] 
        if req_time > minute_ago
    ]
    
    # Check if rate limit exceeded
    if len(rate_limits[client_ip][endpoint]) >= max_requests:
        return True
    
    # Add current request
    rate_limits[client_ip][endpoint].append(current_time)
    return False

def sanitize_input(text: str) -> str:
    """Sanitize user input to prevent XSS and injection attacks"""
    if not text:
        return ""
    
    # Remove potentially dangerous patterns
    for pattern in BLOCKED_PATTERNS:
        text = re.sub(pattern, '', text, flags=re.IGNORECASE)
    
    # Limit length
    if len(text) > MAX_MESSAGE_LENGTH:
        text = text[:MAX_MESSAGE_LENGTH]
    
    # Remove excessive whitespace
    text = re.sub(r'\s+', ' ', text).strip()
    
    return text

def validate_message_content(message: str) -> bool:
    """Validate message content for safety"""
    if not message or len(message.strip()) == 0:
        return False
    
    if len(message) > MAX_MESSAGE_LENGTH:
        return False
    
    # Check for spam patterns
    spam_patterns = [
        r'(.)\1{10,}',  # Repeated characters
        r'[A-Z\s]{50,}',  # Excessive caps
        r'(https?://\S+\s*){5,}',  # Multiple URLs
    ]
    
    for pattern in spam_patterns:
        if re.search(pattern, message):
            return False
    
    return True

# Security middleware - temporarily disabled
# async def security_middleware(request: Request, call_next):
#     """Security middleware for request validation"""
#     start_time = time.time()
#     
#     # Get client IP
#     client_ip = get_client_ip(request)
#     
#     # Check rate limiting for API endpoints
#     if request.url.path.startswith("/api/"):
#         endpoint = request.url.path
#         max_requests = MAX_CHAT_REQUESTS_PER_MINUTE if "/chat" in endpoint else MAX_REQUESTS_PER_MINUTE
#         
#         if is_rate_limited(client_ip, endpoint, max_requests):
#             logger.warning(f"Rate limit exceeded for {client_ip} on {endpoint}")
#             raise HTTPException(
#                 status_code=429,
#                 detail="Rate limit exceeded. Please try again later."
#             )
#     
#     response = await call_next(request)
#     
#     # Log request
#     process_time = time.time() - start_time
#     logger.info(f"{client_ip} - {request.method} {request.url.path} - {response.status_code} - {process_time:.3f}s")
#     
#     return response

# Security middleware class - temporarily disabled
# class SecurityMiddleware(BaseHTTPMiddleware):
#     async def dispatch(self, request: Request, call_next):
#         return await security_middleware(request, call_next)

# Add security middleware - temporarily disabled for testing
# app.add_middleware(SecurityMiddleware)

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
    """Enhanced health check endpoint with detailed status"""
    health_status = {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0",
        "services": {},
        "metrics": {}
    }
    
    # MongoDB health check
    try:
        mongo_client.admin.command('ping')
        health_status["services"]["mongodb"] = {
            "status": "connected",
            "response_time": "< 100ms"
        }
    except Exception as e:
        health_status["services"]["mongodb"] = {
            "status": "disconnected",
            "error": str(e)
        }
        health_status["status"] = "degraded"
    
    # GROQ API health check
    try:
        if groq_client and os.getenv("GROQ_API_KEY"):
            health_status["services"]["groq"] = {
                "status": "connected",
                "model": "llama3-8b-8192"
            }
        else:
            health_status["services"]["groq"] = {
                "status": "demo_mode",
                "reason": "No API key configured"
            }
    except Exception as e:
        health_status["services"]["groq"] = {
            "status": "error",
            "error": str(e)
        }
    
    # System metrics
    try:
        # Memory usage (simplified)
        import psutil
        memory_info = psutil.virtual_memory()
        health_status["metrics"] = {
            "memory_usage": f"{memory_info.percent}%",
            "memory_available": f"{memory_info.available / (1024**3):.1f}GB",
            "cpu_usage": f"{psutil.cpu_percent()}%"
        }
    except ImportError:
        health_status["metrics"] = {
            "note": "psutil not available for system metrics"
        }
    
    # Rate limiting status
    active_connections = sum(len(endpoints) for endpoints in rate_limits.values())
    health_status["rate_limiting"] = {
        "active_connections": active_connections,
        "max_requests_per_minute": MAX_REQUESTS_PER_MINUTE,
        "chat_requests_per_minute": MAX_CHAT_REQUESTS_PER_MINUTE
    }
    
    return health_status

@app.get("/api/metrics")
async def get_metrics():
    """Get application metrics for monitoring"""
    try:
        if not db:
            return {"error": "Database not available"}
        
        # Get basic metrics
        total_conversations = db.conversations.count_documents({})
        total_interactions = db.interactions.count_documents({})
        
        # Get hourly stats for last 24 hours
        twenty_four_hours_ago = datetime.utcnow() - timedelta(hours=24)
        
        hourly_conversations = list(db.conversations.aggregate([
            {"$match": {"timestamp": {"$gte": twenty_four_hours_ago}}},
            {"$group": {
                "_id": {"$dateToString": {"format": "%Y-%m-%d %H:00", "date": "$timestamp"}},
                "count": {"$sum": 1}
            }},
            {"$sort": {"_id": 1}}
        ]))
        
        # Model usage stats
        model_stats = list(db.conversations.aggregate([
            {"$match": {"timestamp": {"$gte": twenty_four_hours_ago}}},
            {"$group": {
                "_id": "$model",
                "count": {"$sum": 1}
            }}
        ]))
        
        # Error rate calculation
        error_count = db.conversations.count_documents({
            "timestamp": {"$gte": twenty_four_hours_ago},
            "model": {"$regex": "fallback|demo"}
        })
        
        total_last_24h = db.conversations.count_documents({
            "timestamp": {"$gte": twenty_four_hours_ago}
        })
        
        error_rate = (error_count / total_last_24h * 100) if total_last_24h > 0 else 0
        
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "totals": {
                "conversations": total_conversations,
                "interactions": total_interactions
            },
            "last_24_hours": {
                "conversations": total_last_24h,
                "error_rate": f"{error_rate:.1f}%",
                "hourly_distribution": hourly_conversations,
                "model_usage": model_stats
            },
            "rate_limiting": {
                "active_ips": len(rate_limits),
                "total_requests_tracked": sum(len(endpoints) for endpoints in rate_limits.values())
            }
        }
    except Exception as e:
        logger.error(f"Metrics error: {e}")
        return {"error": str(e)}

@app.get("/api/status")
async def get_status():
    """Simple status endpoint for load balancer health checks"""
    try:
        # Quick database ping
        mongo_client.admin.command('ping')
        return {"status": "ok", "timestamp": datetime.utcnow().isoformat()}
    except:
        return {"status": "error", "timestamp": datetime.utcnow().isoformat()}

@app.get("/api/embed.js")
async def get_embed_script():
    """Serve the embed script via API endpoint to bypass routing issues"""
    try:
        return FileResponse("/app/backend/static/embed.js", media_type="text/javascript")
    except Exception as e:
        logger.error(f"Embed script error: {e}")
        raise HTTPException(status_code=404, detail="Embed script not found")

@app.post("/api/chat")
async def chat_with_ai(request: Request):
    """Main chat endpoint for the voice widget with 90-day conversation memory"""
    try:
        body = await request.json()
        message = body.get("message", "").strip()
        session_id = body.get("session_id", str(uuid.uuid4()))
        site_id = body.get("site_id", "demo")
        visitor_id = body.get("visitor_id", None)
        
        # Input validation and sanitization
        if not message:
            raise HTTPException(status_code=400, detail="Message is required")
        
        # Sanitize input
        message = sanitize_input(message)
        
        # Validate message content
        if not validate_message_content(message):
            raise HTTPException(status_code=400, detail="Invalid message content")
        
        # Additional rate limiting for chat endpoint
        client_ip = get_client_ip(request)
        if is_rate_limited(client_ip, "chat", MAX_CHAT_REQUESTS_PER_MINUTE):
            raise HTTPException(status_code=429, detail="Chat rate limit exceeded")
        
        # Get site-specific configuration and intelligence
        site_config = await get_site_configuration(site_id)
        
        # Get site intelligence for smarter responses
        site_intelligence = None
        if db_service:
            intelligence_data = await db_service.get_site_intelligence(site_id)
            if intelligence_data:
                site_intelligence = intelligence_data
        
        # Get visitor's historical context (90 days)
        visitor_context = await get_visitor_context(visitor_id, site_id) if visitor_id else None
        
        # AI Response logic with improved error handling
        ai_response = ""
        model_used = "demo"
        
        try:
            if groq_client:
                # Get recent conversation history for immediate context
                conversation_history = await get_conversation_history(session_id, site_id)
                
                # Create conversation context with memory
                conversation_context = [
                    {
                        "role": "system",
                        "content": create_system_prompt_with_memory(site_config, visitor_context)
                    }
                ]
                
                # Add conversation history (last 8 messages for context)
                for msg in conversation_history[-8:]:
                    conversation_context.append({
                        "role": "user",
                        "content": msg["user_message"]
                    })
                    conversation_context.append({
                        "role": "assistant",
                        "content": msg["ai_response"]
                    })
                
                # Add current message with enhanced context
                enhanced_message = await enhance_ai_context_with_memory(message, site_config, visitor_context)
                conversation_context.append({
                    "role": "user",
                    "content": enhanced_message
                })
                
                # Get custom API key for site or use default
                api_key = site_config.get("groq_api_key") or os.getenv("GROQ_API_KEY")
                if api_key:
                    # Create client with custom API key if provided
                    client = Groq(api_key=api_key) if site_config.get("groq_api_key") else groq_client
                    
                    # Get response from GROQ with enhanced parameters
                    completion = client.chat.completions.create(
                        model="llama3-8b-8192",
                        messages=conversation_context,
                        max_tokens=300,  # Increased for more detailed responses
                        temperature=0.8,  # Slightly higher for more creative responses
                        stream=False
                    )
                    
                    ai_response = completion.choices[0].message.content
                    model_used = "llama3-8b-8192"
                    
                    # Content filtering for AI response
                    ai_response = filter_ai_response(ai_response)
                    
                else:
                    raise Exception("No GROQ API key available")
                
        except Exception as e:
            logger.error(f"GROQ API error: {e}")
            # Fallback to demo response with context
            conversation_history = await get_conversation_history(session_id, site_id)
            ai_response = generate_contextual_demo_response_with_memory(message, conversation_history, visitor_context)
            model_used = "demo_fallback"
        
        # Store conversation in MongoDB with visitor ID
        if db is not None:
            try:
                conversation_log = {
                    "session_id": session_id,
                    "site_id": site_id,
                    "visitor_id": visitor_id,
                    "user_message": message,
                    "ai_response": ai_response,
                    "timestamp": datetime.utcnow(),
                    "model": model_used,
                    "tokens_used": len(message.split()) + len(ai_response.split()),
                    "client_ip": client_ip,
                    "user_agent": request.headers.get("user-agent", "unknown"),
                    "expires_at": datetime.utcnow() + timedelta(days=90)  # Auto-expire after 90 days
                }
                db.conversations.insert_one(conversation_log)
                
                # Create index for automatic cleanup
                db.conversations.create_index("expires_at", expireAfterSeconds=0)
                
                logger.info(f"Conversation logged for visitor {visitor_id}, session {session_id}")
            except Exception as e:
                logger.error(f"Failed to log conversation: {e}")
        
        # Get conversation history length
        conversation_history = await get_conversation_history(session_id, site_id)
        
        return {
            "response": ai_response,
            "session_id": session_id,
            "visitor_id": visitor_id,
            "timestamp": datetime.utcnow().isoformat(),
            "model": model_used,
            "conversation_length": len(conversation_history) + 1,
            "is_returning_visitor": visitor_context is not None and len(visitor_context.get("previous_conversations", [])) > 0,
            "rate_limit_remaining": MAX_CHAT_REQUESTS_PER_MINUTE - len(rate_limits[client_ip]["chat"])
        }
        
    except HTTPException:
        # Re-raise HTTP exceptions (like 400 for missing message)
        raise
    except Exception as e:
        logger.error(f"Chat endpoint error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

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
    try:
        # Return the static widget HTML file
        return FileResponse("/app/backend/static/widget.html")
    except Exception as e:
        logger.error(f"Widget page error: {e}")
        # Fallback HTML
        html_content = f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>AI Voice Assistant Widget</title>
        </head>
        <body>
            <div style="padding: 20px; text-align: center; font-family: system-ui;">
                <h3>AI Voice Assistant</h3>
                <p>Loading...</p>
                <script>
                    const siteId = "{site_id}";
                    const backendUrl = window.location.origin;
                    
                    // Load widget script
                    const script = document.createElement('script');
                    script.src = '/static/widget.js';
                    script.setAttribute('data-site-id', siteId);
                    script.setAttribute('data-backend-url', backendUrl);
                    document.head.appendChild(script);
                </script>
            </div>
        </body>
        </html>
        """
        return HTMLResponse(content=html_content)

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

# ============================================================================
# ENHANCED AI CONVERSATION FUNCTIONS
# ============================================================================

async def get_visitor_context(visitor_id: str, site_id: str) -> Dict[str, Any]:
    """Get visitor's historical context from last 90 days"""
    if not visitor_id or db is None:
        return None
    
    try:
        # Get visitor's conversation history from last 90 days
        ninety_days_ago = datetime.utcnow() - timedelta(days=90)
        
        # Get conversation summary
        conversations = list(db.conversations.find({
            "visitor_id": visitor_id,
            "site_id": site_id,
            "timestamp": {"$gte": ninety_days_ago}
        }).sort("timestamp", -1).limit(50))  # Last 50 conversations
        
        if not conversations:
            return None
        
        # Extract key information
        total_conversations = len(conversations)
        first_visit = conversations[-1]["timestamp"] if conversations else None
        last_visit = conversations[0]["timestamp"] if conversations else None
        
        # Get common topics and interests
        all_messages = []
        for conv in conversations:
            all_messages.append(conv.get("user_message", ""))
        
        # Extract context insights
        context = {
            "visitor_id": visitor_id,
            "total_conversations": total_conversations,
            "first_visit": first_visit,
            "last_visit": last_visit,
            "is_returning_visitor": total_conversations > 1,
            "days_since_first_visit": (datetime.utcnow() - first_visit).days if first_visit else 0,
            "days_since_last_visit": (datetime.utcnow() - last_visit).days if last_visit else 0,
            "recent_topics": extract_topics_from_messages(all_messages[:10]),  # Last 10 messages
            "previous_conversations": conversations[:5]  # Last 5 conversations for context
        }
        
        return context
        
    except Exception as e:
        logger.error(f"Error getting visitor context: {e}")
        return None

def extract_topics_from_messages(messages: List[str]) -> List[str]:
    """Extract key topics from user messages"""
    topics = []
    keywords = {
        "product": ["product", "service", "offer", "buy", "purchase", "price", "cost"],
        "support": ["help", "problem", "issue", "error", "trouble", "fix", "support"],
        "navigation": ["find", "where", "navigate", "locate", "search", "page"],
        "information": ["about", "info", "details", "explain", "what", "how", "why"],
        "account": ["account", "login", "register", "profile", "settings", "password"]
    }
    
    for message in messages:
        message_lower = message.lower()
        for topic, words in keywords.items():
            if any(word in message_lower for word in words):
                if topic not in topics:
                    topics.append(topic)
    
    return topics

async def enhance_ai_context_with_memory(message: str, site_config: Dict[str, Any], visitor_context: Dict[str, Any]) -> str:
    """Enhance AI context with website-specific information and visitor memory"""
    context_parts = [f"User Question: {message}"]
    
    # Add website context
    context_parts.append(f"""
Website Context:
- Site ID: {site_config.get('site_id', 'unknown')}
- Bot Name: {site_config.get('bot_name', 'AI Assistant')}
- Language: {site_config.get('language', 'en-US')}""")
    
    # Add visitor memory context if available
    if visitor_context:
        context_parts.append(f"""
Visitor Memory (Last 90 Days):
- Total Conversations: {visitor_context.get('total_conversations', 0)}
- First Visit: {visitor_context.get('first_visit', 'Unknown')}
- Last Visit: {visitor_context.get('last_visit', 'Unknown')}
- Days Since First Visit: {visitor_context.get('days_since_first_visit', 0)}
- Days Since Last Visit: {visitor_context.get('days_since_last_visit', 0)}
- Previous Topics: {', '.join(visitor_context.get('recent_topics', []))}
- Is Returning Visitor: {visitor_context.get('is_returning_visitor', False)}""")
        
        # Add context from recent conversations
        if visitor_context.get('previous_conversations'):
            context_parts.append("\nRecent Conversation Context:")
            for i, conv in enumerate(visitor_context['previous_conversations'][:3]):
                context_parts.append(f"- {conv.get('user_message', '')[:100]}...")
    
    context_parts.append("\nPlease provide a helpful, personalized response considering the visitor's history and context.")
    
    return "\n".join(context_parts)

def create_system_prompt_with_memory(site_config: Dict[str, Any], visitor_context: Dict[str, Any]) -> str:
    """Create customized system prompt with visitor memory"""
    bot_name = site_config.get("bot_name", "AI Assistant")
    language = site_config.get("language", "en-US")
    
    # Base prompt
    base_prompt = f"""You are {bot_name}, an intelligent AI assistant embedded on a website to help visitors with all their questions and needs."""
    
    # Add personalization based on visitor context
    if visitor_context and visitor_context.get('is_returning_visitor'):
        total_conversations = visitor_context.get('total_conversations', 0)
        days_since_first = visitor_context.get('days_since_first_visit', 0)
        days_since_last = visitor_context.get('days_since_last_visit', 0)
        recent_topics = visitor_context.get('recent_topics', [])
        
        personalization = f"""
**VISITOR CONTEXT:**
- This is a returning visitor who has had {total_conversations} conversations with you
- First visited {days_since_first} days ago
- Last visited {days_since_last} days ago
- Previous interests: {', '.join(recent_topics) if recent_topics else 'General inquiries'}
- Be welcoming and acknowledge their return while being helpful

**PERSONALIZATION GUIDELINES:**
- Reference their previous interests when relevant
- Show appreciation for their return
- Build on previous conversations when appropriate
- Provide continuity in your assistance"""
    else:
        personalization = """
**VISITOR CONTEXT:**
- This appears to be a new visitor
- Provide a warm welcome and comprehensive introduction
- Be extra helpful in explaining website features and capabilities"""
    
    full_prompt = f"""{base_prompt}

{personalization}

**CORE CAPABILITIES:**
- Answer questions about the website, its content, services, and features
- Provide general information on any topic visitors ask about
- Help with navigation and finding information
- Explain products, services, or content on the website
- Assist with technical questions about web technologies
- Provide recommendations and suggestions
- Help with troubleshooting common issues
- Offer guidance on how to use the website effectively

**CONVERSATION STYLE:**
- Be friendly, professional, and conversational
- Keep responses concise (under 200 words) for voice compatibility
- Remember conversation history and maintain context
- Ask clarifying questions when needed
- Provide specific, actionable information
- Use a helpful, supportive tone

**LANGUAGE:** {language}

Remember: You are here to make the visitor's experience better and help them accomplish their goals on this website. Use their history to provide more personalized, relevant assistance!"""
    
    return full_prompt

def generate_contextual_demo_response_with_memory(message: str, conversation_history: List[Dict[str, Any]], visitor_context: Dict[str, Any]) -> str:
    """Generate demo responses with conversation context and visitor memory"""
    message_lower = message.lower()
    
    # Check if this is a returning visitor
    is_returning = visitor_context and visitor_context.get('is_returning_visitor', False)
    
    # Personalized greetings for returning visitors
    if any(greeting in message_lower for greeting in ['hello', 'hi', 'hey', 'good morning', 'good afternoon', 'good evening']):
        if is_returning:
            days_since_last = visitor_context.get('days_since_last_visit', 0)
            total_conversations = visitor_context.get('total_conversations', 0)
            
            if days_since_last == 0:
                return f"Welcome back! I see we've been talking today. I'm here to continue helping you with anything you need on this website. How can I assist you further?"
            elif days_since_last == 1:
                return f"Welcome back! Good to see you again so soon. We've had {total_conversations} conversations before. How can I help you today?"
            elif days_since_last <= 7:
                return f"Welcome back! It's been {days_since_last} days since we last chatted. I remember our previous conversations about {', '.join(visitor_context.get('recent_topics', ['general topics']))}. How can I help you today?"
            else:
                return f"Welcome back! It's been a while since we last talked ({days_since_last} days ago). I'm here to help with anything you need on this website. What can I assist you with?"
        else:
            if conversation_history:
                return "Hello again! How else can I assist you today?"
            else:
                return "Hello! I'm your AI assistant, ready to help you navigate this website and answer any questions you have. What can I help you with today?"
    
    # Use the original contextual response function with memory enhancements
    base_response = generate_contextual_demo_response(message, conversation_history)
    
    # Add personalization for returning visitors
    if is_returning and visitor_context:
        recent_topics = visitor_context.get('recent_topics', [])
        if recent_topics:
            # If the current question relates to previous topics, mention it
            current_topics = extract_topics_from_messages([message])
            common_topics = set(recent_topics) & set(current_topics)
            if common_topics:
                base_response += f" I notice you've asked about {', '.join(common_topics)} before - I'm here to help you dive deeper into this topic!"
    
    return base_response

async def get_conversation_history(session_id: str, site_id: str, limit: int = 10) -> List[Dict[str, Any]]:
    """Get conversation history for a session"""
    try:
        if db is None:
            return []
        
        conversations = list(db.conversations.find({
            "session_id": session_id,
            "site_id": site_id
        }).sort("timestamp", 1).limit(limit))
        
        return [
            {
                "user_message": conv.get("user_message", ""),
                "ai_response": conv.get("ai_response", ""),
                "timestamp": conv.get("timestamp")
            }
            for conv in conversations
        ]
    except Exception as e:
        logger.error(f"Error getting conversation history: {e}")
        return []

async def get_site_configuration(site_id: str) -> Dict[str, Any]:
    """Get site configuration for AI customization"""
    try:
        if not db_service:
            return get_default_site_config()
        
        config = await db_service.get_site_config(site_id)
        if config:
            return config
        return get_default_site_config()
    except Exception as e:
        logger.error(f"Error getting site configuration: {e}")
        return get_default_site_config()

def get_default_site_config() -> Dict[str, Any]:
    """Get default site configuration"""
    return {
        "site_id": "demo-site",
        "greeting_message": "Hi there! I'm your virtual assistant. How can I help you today?",
        "bot_name": "AI Assistant",
        "language": "en-US",
        "voice_enabled": True,
        "groq_api_key": None
    }

async def enhance_ai_context(message: str, site_config: Dict[str, Any]) -> str:
    """Enhance AI context with website-specific information"""
    # Add website context to the message for better AI understanding
    site_context = f"""
Website Context:
- Site ID: {site_config.get('site_id', 'unknown')}
- Bot Name: {site_config.get('bot_name', 'AI Assistant')}
- Language: {site_config.get('language', 'en-US')}

User Question: {message}

Please provide a helpful response considering you are an AI assistant on this website."""
    
    return site_context

def create_system_prompt(site_config: Dict[str, Any]) -> str:
    """Create customized system prompt based on site configuration"""
    bot_name = site_config.get("bot_name", "AI Assistant")
    language = site_config.get("language", "en-US")
    
    base_prompt = f"""You are {bot_name}, an intelligent AI assistant embedded on a website to help visitors with all their questions and needs. You are knowledgeable, helpful, and can assist with:

**CORE CAPABILITIES:**
- Answer questions about the website, its content, services, and features
- Provide general information on any topic visitors ask about
- Help with navigation and finding information
- Explain products, services, or content on the website
- Assist with technical questions about web technologies
- Provide recommendations and suggestions
- Help with troubleshooting common issues
- Offer guidance on how to use the website effectively

**CONVERSATION STYLE:**
- Be friendly, professional, and conversational
- Keep responses concise (under 150 words) for voice compatibility
- Remember conversation history and maintain context
- Ask clarifying questions when needed
- Provide specific, actionable information
- Use a helpful, supportive tone

**KNOWLEDGE AREAS:**
- Website functionality and features
- General business and industry knowledge
- Technology and web development
- Customer service and support
- Product information and comparisons
- How-to guides and tutorials
- Best practices and recommendations
- Common troubleshooting steps

**RESPONSE GUIDELINES:**
1. Always try to be helpful, even if the question is outside your primary knowledge
2. If you don't know something specific about this website, ask for clarification or suggest where they might find the information
3. Provide step-by-step guidance when appropriate
4. Offer multiple solutions when possible
5. Stay engaging and maintain a conversational flow
6. Be proactive in offering additional help

**LANGUAGE:** {language}

Remember: You are here to make the visitor's experience better and help them accomplish their goals on this website. Be their knowledgeable, friendly guide!"""
    
    return base_prompt

def filter_ai_response(response: str) -> str:
    """Filter AI responses for inappropriate content while preserving helpful information"""
    if not response:
        return "I apologize, but I couldn't generate a proper response. Please try again."
    
    # Remove any potential script injection
    for pattern in BLOCKED_PATTERNS:
        response = re.sub(pattern, '', response, flags=re.IGNORECASE)
    
    # Basic profanity filter (minimal to preserve natural conversation)
    profanity_words = [
        'fuck', 'shit', 'bitch', 'ass', 'damn'
    ]
    
    for word in profanity_words:
        response = re.sub(r'\b' + re.escape(word) + r'\b', '[filtered]', response, flags=re.IGNORECASE)
    
    # Allow longer responses for detailed explanations (increased limit)
    if len(response) > 800:
        response = response[:797] + "..."
    
    return response.strip()

def generate_contextual_demo_response(message: str, conversation_history: List[Dict[str, Any]]) -> str:
    """Generate demo responses with conversation context and enhanced capabilities"""
    message_lower = message.lower()
    
    # Check if this is a follow-up based on history
    if conversation_history:
        last_response = conversation_history[-1].get("ai_response", "").lower()
        
        # Handle follow-up questions
        if any(word in message_lower for word in ['more', 'tell me more', 'continue', 'elaborate', 'explain further']):
            if 'website' in last_response or 'site' in last_response:
                return "I can help you understand more about this website's features, navigation, content, or any specific functionality you're interested in. What particular aspect would you like to know more about?"
            elif 'product' in last_response or 'service' in last_response:
                return "I'd be happy to provide more details about products or services. I can explain features, benefits, pricing, or help you compare options. What specific information are you looking for?"
            elif 'help' in last_response:
                return "I'm here to assist with anything you need! I can help with website navigation, answer questions about content, explain features, troubleshoot issues, or provide general information. What would you like help with?"
            else:
                return "I'd be happy to provide more details! Could you be more specific about what aspect you'd like to know more about?"
        
        # Handle clarification requests
        if any(word in message_lower for word in ['what do you mean', 'explain', 'clarify', 'how', 'why']):
            return "Let me clarify that for you. I'm here to help explain anything about this website, its features, or answer any questions you have. What specifically would you like me to explain?"
    
    # Enhanced responses for various query types
    
    # Greetings and basic interactions
    if any(greeting in message_lower for greeting in ['hello', 'hi', 'hey', 'good morning', 'good afternoon', 'good evening']):
        if conversation_history:
            return "Hello again! I'm here to help you with anything you need on this website. Do you have any questions about our content, features, or how to find what you're looking for?"
        else:
            return "Hello! I'm your AI assistant, ready to help you navigate this website and answer any questions you have. What can I help you with today?"
    
    # Website-specific queries
    if any(word in message_lower for word in ['website', 'site', 'page', 'navigation', 'menu', 'find']):
        return "I can help you navigate this website and find what you're looking for. I can explain features, help you locate specific content, or guide you through any processes. What are you trying to find or accomplish?"
    
    # Product/Service queries
    if any(word in message_lower for word in ['product', 'service', 'offer', 'price', 'cost', 'buy', 'purchase']):
        return "I can help you learn about products and services offered here. I can explain features, compare options, discuss pricing, or guide you through the selection process. What specific information are you looking for?"
    
    # Technical support queries
    if any(word in message_lower for word in ['problem', 'issue', 'error', 'not working', 'broken', 'fix', 'trouble']):
        return "I'm here to help resolve any issues you're experiencing. I can provide troubleshooting steps, explain how features work, or guide you to the right resources. What specific problem are you encountering?"
    
    # How-to queries
    if any(word in message_lower for word in ['how to', 'how do', 'how can', 'step', 'guide', 'tutorial']):
        return "I'd be happy to provide step-by-step guidance! I can walk you through processes, explain how to use features, or provide instructions. What would you like to learn how to do?"
    
    # Contact and support queries
    if any(word in message_lower for word in ['contact', 'support', 'help', 'customer service', 'phone', 'email']):
        return "I can help you find contact information and support resources. I can also try to answer your questions directly or guide you to the right person or department. What do you need assistance with?"
    
    # About/Information queries
    if any(word in message_lower for word in ['about', 'company', 'business', 'who', 'what is', 'information']):
        return "I can share information about this website, the company, services, or any other details you're curious about. What specific information would you like to know?"
    
    # General capabilities
    if any(word in message_lower for word in ['what can you do', 'help', 'capabilities', 'assist']):
        return "I can help you with a wide range of things! I can answer questions about this website, explain features, help you navigate, troubleshoot issues, provide information about products or services, and much more. What would you like assistance with?"
    
    # Personal questions
    if any(question in message_lower for question in ['how are you', 'how do you do', 'what are you']):
        return "I'm doing great and I'm here to help! I'm an AI assistant designed to make your experience on this website better. I can answer questions, provide guidance, and help you find what you need. How can I assist you today?"
    
    # Gratitude responses
    if any(word in message_lower for word in ['thank', 'thanks', 'appreciate']):
        return "You're very welcome! I'm glad I could help. If you have any other questions or need assistance with anything else on this website, feel free to ask anytime!"
    
    # Goodbye responses
    if any(word in message_lower for word in ['bye', 'goodbye', 'see you', 'later']):
        return "Goodbye! It was great helping you today. Feel free to come back anytime if you have more questions or need assistance with anything on this website. Have a wonderful day!"
    
    # Default intelligent response for any other query
    context_info = ""
    if conversation_history:
        context_info = " I remember our conversation, so feel free to ask follow-up questions or explore related topics."
    
    return f"That's an interesting question about '{message}'. I'm here to help with anything related to this website - whether it's navigation, features, content, or general information. I can provide explanations, guidance, or help you find what you're looking for.{context_info} What specific aspect would you like to know more about?"

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

# ============================================================================
# WEBSITE INTELLIGENCE & ROI API ENDPOINTS
# ============================================================================

@app.post("/api/sites/{site_id}/crawl")
async def crawl_website(site_id: str, current_user: UserDB = Depends(get_current_user)):
    """Initiate website crawling and intelligence analysis."""
    if not db_service:
        raise HTTPException(status_code=500, detail="Database not available")
    
    try:
        # Get site information
        site = await db_service.get_site_by_id(site_id, current_user.id)
        if not site:
            raise HTTPException(status_code=404, detail="Site not found")
        
        # Start website crawling
        async with WebsiteIntelligenceEngine(db_service) as intelligence:
            site_structure = await intelligence.crawl_website(
                domain=site.domain,
                max_pages=100,
                max_depth=3
            )
            
            return {
                "message": "Website crawling completed successfully",
                "site_id": site_id,
                "domain": site.domain,
                "pages_analyzed": site_structure.total_pages,
                "crawl_timestamp": site_structure.last_full_crawl.isoformat(),
                "roi_metrics": site_structure.roi_metrics
            }
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Website crawling error: {e}")
        raise HTTPException(status_code=500, detail=f"Crawling failed: {str(e)}")

@app.get("/api/sites/{site_id}/intelligence")
async def get_site_intelligence(site_id: str, current_user: UserDB = Depends(get_current_user)):
    """Get website intelligence data for a site."""
    if not db_service:
        raise HTTPException(status_code=500, detail="Database not available")
    
    try:
        # Verify site ownership
        site = await db_service.get_site_by_id(site_id, current_user.id)
        if not site:
            raise HTTPException(status_code=404, detail="Site not found")
        
        # Get intelligence data
        intelligence_data = await db_service.get_site_intelligence(site_id)
        
        if not intelligence_data:
            return {
                "message": "No intelligence data available. Please crawl the website first.",
                "site_id": site_id,
                "crawl_required": True
            }
        
        return {
            "site_id": site_id,
            "intelligence_data": intelligence_data,
            "last_updated": intelligence_data.get("last_full_crawl"),
            "total_pages": intelligence_data.get("total_pages", 0),
            "roi_metrics": intelligence_data.get("roi_metrics", {})
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get site intelligence error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/sites/{site_id}/analyze-intent")
async def analyze_user_intent(site_id: str, request: Request):
    """Analyze user intent and provide intelligent recommendations."""
    try:
        body = await request.json()
        query = body.get("query", "").strip()
        current_page = body.get("current_page", "")
        visitor_id = body.get("visitor_id", "")
        
        if not query:
            raise HTTPException(status_code=400, detail="Query is required")
        
        # Get site intelligence data
        if db_service:
            intelligence_data = await db_service.get_site_intelligence(site_id)
            
            if intelligence_data:
                # Use intelligence engine for analysis
                async with WebsiteIntelligenceEngine(db_service) as intelligence:
                    # Reconstruct site structure from stored data
                    from website_intelligence import SiteStructure
                    site_structure = SiteStructure(**intelligence_data)
                    
                    # Analyze intent
                    intent_analysis = await intelligence.analyze_user_intent(
                        query, current_page, site_structure
                    )
                    
                    # Get navigation suggestions
                    navigation_suggestions = await intelligence.get_navigation_suggestions(
                        query, current_page, site_structure
                    )
                    
                    # Store intent analysis
                    await db_service.store_intent_analysis({
                        "site_id": site_id,
                        "visitor_id": visitor_id,
                        "query": query,
                        "current_page": current_page,
                        "intent_type": intent_analysis.intent_type,
                        "confidence": intent_analysis.confidence,
                        "suggested_pages": intent_analysis.suggested_pages,
                        "conversion_probability": intent_analysis.conversion_probability,
                        "journey_stage": intent_analysis.journey_stage,
                        "timestamp": datetime.utcnow()
                    })
                    
                    # Store navigation suggestion
                    await db_service.store_navigation_suggestion({
                        "site_id": site_id,
                        "visitor_id": visitor_id,
                        "query": query,
                        "current_page": current_page,
                        "suggested_pages": navigation_suggestions,
                        "success_probability": intent_analysis.conversion_probability,
                        "timestamp": datetime.utcnow()
                    })
                    
                    return {
                        "intent_analysis": {
                            "intent_type": intent_analysis.intent_type,
                            "confidence": intent_analysis.confidence,
                            "journey_stage": intent_analysis.journey_stage,
                            "conversion_probability": intent_analysis.conversion_probability,
                            "recommended_actions": intent_analysis.recommended_actions
                        },
                        "navigation_suggestions": navigation_suggestions,
                        "intelligent_response": f"Based on your query '{query}', I can help you with {intent_analysis.intent_type}. " +
                                               f"Here are some relevant pages and actions I recommend."
                    }
        
        # Fallback response if no intelligence data
        return {
            "intent_analysis": {
                "intent_type": "information",
                "confidence": 0.5,
                "journey_stage": "awareness",
                "conversion_probability": 0.3,
                "recommended_actions": ["Provide general information", "Ask clarifying questions"]
            },
            "navigation_suggestions": [],
            "intelligent_response": f"I understand you're looking for information about '{query}'. Let me help you find what you need."
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Intent analysis error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/sites/{site_id}/roi-report")
async def get_roi_report(site_id: str, days: int = 30, current_user: UserDB = Depends(get_current_user)):
    """Generate and retrieve ROI report for a site."""
    if not db_service:
        raise HTTPException(status_code=500, detail="Database not available")
    
    try:
        # Verify site ownership
        site = await db_service.get_site_by_id(site_id, current_user.id)
        if not site:
            raise HTTPException(status_code=404, detail="Site not found")
        
        # Generate ROI report
        roi_report = await db_service.generate_roi_report(site_id, days)
        
        if not roi_report:
            raise HTTPException(status_code=500, detail="Failed to generate ROI report")
        
        # Calculate ROI summary
        engagement_metrics = roi_report.get("engagement_metrics", {})
        conversion_metrics = roi_report.get("conversion_metrics", {})
        roi_metrics = roi_report.get("roi_metrics", {})
        
        # Calculate estimated monthly value
        monthly_savings = roi_metrics.get("support_cost_savings", 0) * (30 / days)
        improved_conversion_value = conversion_metrics.get("conversion_rate", 0) * 100  # Simplified calculation
        
        roi_summary = {
            "total_monthly_value": monthly_savings + improved_conversion_value,
            "support_cost_savings": roi_metrics.get("support_cost_savings", 0),
            "user_engagement_improvement": engagement_metrics.get("pages_per_session", 0),
            "conversion_rate": conversion_metrics.get("conversion_rate", 0),
            "user_satisfaction": roi_metrics.get("user_satisfaction_score", 0),
            "ai_effectiveness": roi_metrics.get("ai_resolution_rate", 0)
        }
        
        return {
            "site_id": site_id,
            "report_period": f"{days} days",
            "generated_at": roi_report.get("generated_at"),
            "roi_summary": roi_summary,
            "detailed_metrics": roi_report,
            "recommendations": generate_roi_recommendations(roi_report)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"ROI report error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/sites/{site_id}/user-journeys")
async def get_user_journeys(site_id: str, visitor_id: Optional[str] = None, days: int = 30, current_user: UserDB = Depends(get_current_user)):
    """Get user journey data for analysis."""
    if not db_service:
        raise HTTPException(status_code=500, detail="Database not available")
    
    try:
        # Verify site ownership
        site = await db_service.get_site_by_id(site_id, current_user.id)
        if not site:
            raise HTTPException(status_code=404, detail="Site not found")
        
        # Get user journeys
        journeys = await db_service.get_user_journeys(site_id, visitor_id, days)
        
        # Calculate journey analytics
        if journeys:
            total_journeys = len(journeys)
            completed_journeys = sum(1 for journey in journeys if journey.get("converted", False))
            avg_journey_length = np.mean([len(journey.get("pages_visited", [])) for journey in journeys])
            
            # Get most common journey paths
            all_paths = [journey.get("pages_visited", []) for journey in journeys]
            common_paths = Counter([tuple(path[:3]) for path in all_paths if len(path) >= 3])  # First 3 pages
            
            journey_analytics = {
                "total_journeys": total_journeys,
                "completed_journeys": completed_journeys,
                "completion_rate": (completed_journeys / total_journeys) * 100,
                "average_journey_length": avg_journey_length,
                "common_paths": [{"path": list(path), "count": count} for path, count in common_paths.most_common(5)]
            }
        else:
            journey_analytics = {
                "total_journeys": 0,
                "completed_journeys": 0,
                "completion_rate": 0,
                "average_journey_length": 0,
                "common_paths": []
            }
        
        return {
            "site_id": site_id,
            "period": f"{days} days",
            "journey_analytics": journey_analytics,
            "individual_journeys": journeys[:20]  # Return latest 20 journeys
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"User journeys error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/track-user-journey")
async def track_user_journey(request: Request):
    """Track user journey for analytics."""
    try:
        body = await request.json()
        
        journey_data = {
            "visitor_id": body.get("visitor_id", ""),
            "session_id": body.get("session_id", ""),
            "site_id": body.get("site_id", ""),
            "page_url": body.get("page_url", ""),
            "page_title": body.get("page_title", ""),
            "time_on_page": body.get("time_on_page", 0),
            "interaction_type": body.get("interaction_type", "page_view"),
            "referrer": body.get("referrer", ""),
            "user_agent": request.headers.get("user-agent", ""),
            "timestamp": datetime.utcnow()
        }
        
        if db_service:
            # Store journey data
            await db_service.store_user_journey(journey_data)
            
            # Update or create user journey record
            existing_journey = await db_service.user_journeys.find_one({
                "visitor_id": journey_data["visitor_id"],
                "session_id": journey_data["session_id"]
            })
            
            if existing_journey:
                # Update existing journey
                pages_visited = existing_journey.get("pages_visited", [])
                if journey_data["page_url"] not in pages_visited:
                    pages_visited.append(journey_data["page_url"])
                
                time_on_pages = existing_journey.get("time_on_pages", {})
                time_on_pages[journey_data["page_url"]] = journey_data["time_on_page"]
                
                await db_service.user_journeys.update_one(
                    {"visitor_id": journey_data["visitor_id"], "session_id": journey_data["session_id"]},
                    {"$set": {
                        "pages_visited": pages_visited,
                        "time_on_pages": time_on_pages,
                        "last_updated": datetime.utcnow()
                    }}
                )
            else:
                # Create new journey
                new_journey = {
                    "visitor_id": journey_data["visitor_id"],
                    "session_id": journey_data["session_id"],
                    "site_id": journey_data["site_id"],
                    "pages_visited": [journey_data["page_url"]],
                    "time_on_pages": {journey_data["page_url"]: journey_data["time_on_page"]},
                    "intent_progression": [],
                    "conversion_events": [],
                    "journey_stage": "awareness",
                    "converted": False,
                    "timestamp": datetime.utcnow(),
                    "last_updated": datetime.utcnow()
                }
                await db_service.user_journeys.insert_one(new_journey)
        
        return {"status": "journey_tracked"}
        
    except Exception as e:
        logger.error(f"Journey tracking error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/sites/{site_id}/analytics/roi")
async def get_roi_analytics(site_id: str, days: int = 30, current_user: UserDB = Depends(get_current_user)):
    """Get detailed ROI analytics."""
    if not db_service:
        raise HTTPException(status_code=500, detail="Database not available")
    
    try:
        # Verify site ownership
        site = await db_service.get_site_by_id(site_id, current_user.id)
        if not site:
            raise HTTPException(status_code=404, detail="Site not found")
        
        # Get latest ROI report
        roi_report = await db_service.get_latest_roi_report(site_id)
        
        # Get intent analytics
        intent_analytics = await db_service.get_intent_analytics(site_id, days)
        
        # Get navigation analytics
        nav_analytics = await db_service.get_navigation_analytics(site_id, days)
        
        return {
            "site_id": site_id,
            "roi_report": roi_report,
            "intent_analytics": intent_analytics,
            "navigation_analytics": nav_analytics,
            "performance_indicators": {
                "user_engagement": calculate_engagement_score(roi_report),
                "conversion_optimization": calculate_conversion_score(roi_report),
                "ai_effectiveness": calculate_ai_effectiveness(roi_report),
                "cost_savings": calculate_cost_savings(roi_report)
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"ROI analytics error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Helper functions for ROI calculations
def generate_roi_recommendations(roi_report: Dict[str, Any]) -> List[str]:
    """Generate ROI improvement recommendations."""
    recommendations = []
    
    roi_metrics = roi_report.get("roi_metrics", {})
    conversion_metrics = roi_report.get("conversion_metrics", {})
    engagement_metrics = roi_report.get("engagement_metrics", {})
    
    # User satisfaction recommendations
    user_satisfaction = roi_metrics.get("user_satisfaction_score", 0)
    if user_satisfaction < 70:
        recommendations.append("Improve AI response quality to increase user satisfaction")
        recommendations.append("Add more comprehensive FAQ content to better address user queries")
    
    # Conversion rate recommendations
    conversion_rate = conversion_metrics.get("conversion_rate", 0)
    if conversion_rate < 5:
        recommendations.append("Optimize conversion funnels and call-to-action placement")
        recommendations.append("Implement personalized recommendations based on user intent")
    
    # Navigation efficiency recommendations
    navigation_efficiency = roi_metrics.get("navigation_efficiency", 0)
    if navigation_efficiency < 80:
        recommendations.append("Improve website navigation structure and internal linking")
        recommendations.append("Add intelligent page suggestions based on user behavior")
    
    # AI effectiveness recommendations
    ai_resolution_rate = roi_metrics.get("ai_resolution_rate", 0)
    if ai_resolution_rate < 60:
        recommendations.append("Expand AI knowledge base with more website-specific content")
        recommendations.append("Implement proactive assistance based on user journey stage")
    
    return recommendations

def calculate_engagement_score(roi_report: Dict[str, Any]) -> float:
    """Calculate user engagement score."""
    if not roi_report:
        return 0.0
    
    engagement_metrics = roi_report.get("engagement_metrics", {})
    pages_per_session = engagement_metrics.get("pages_per_session", 0)
    avg_session_duration = engagement_metrics.get("avg_session_duration", 0)
    
    # Normalize scores (assuming optimal values)
    page_score = min(100, (pages_per_session / 5) * 100)  # 5 pages per session is optimal
    duration_score = min(100, (avg_session_duration / 180) * 100)  # 3 minutes is optimal
    
    return (page_score + duration_score) / 2

def calculate_conversion_score(roi_report: Dict[str, Any]) -> float:
    """Calculate conversion optimization score."""
    if not roi_report:
        return 0.0
    
    conversion_metrics = roi_report.get("conversion_metrics", {})
    conversion_rate = conversion_metrics.get("conversion_rate", 0)
    intent_accuracy = conversion_metrics.get("intent_accuracy", 0)
    
    # Conversion rate score (assuming 10% is excellent)
    conversion_score = min(100, (conversion_rate / 10) * 100)
    
    return (conversion_score + intent_accuracy) / 2

def calculate_ai_effectiveness(roi_report: Dict[str, Any]) -> float:
    """Calculate AI effectiveness score."""
    if not roi_report:
        return 0.0
    
    roi_metrics = roi_report.get("roi_metrics", {})
    ai_resolution_rate = roi_metrics.get("ai_resolution_rate", 0)
    user_satisfaction = roi_metrics.get("user_satisfaction_score", 0)
    
    return (ai_resolution_rate + user_satisfaction) / 2

def calculate_cost_savings(roi_report: Dict[str, Any]) -> float:
    """Calculate cost savings score."""
    if not roi_report:
        return 0.0
    
    roi_metrics = roi_report.get("roi_metrics", {})
    support_cost_savings = roi_metrics.get("support_cost_savings", 0)
    
    # Normalize based on expected monthly savings (assuming $500/month is excellent)
    return min(100, (support_cost_savings / 500) * 100)