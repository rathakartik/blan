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
import re
import time
from collections import defaultdict

# Import new modules
from models import *
from auth import *
from database import DatabaseService

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

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure this properly for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================================================
# SECURITY & RATE LIMITING MIDDLEWARE
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

async def security_middleware(request: Request, call_next):
    """Security middleware for request validation"""
    start_time = time.time()
    
    # Get client IP
    client_ip = get_client_ip(request)
    
    # Check rate limiting for API endpoints
    if request.url.path.startswith("/api/"):
        endpoint = request.url.path
        max_requests = MAX_CHAT_REQUESTS_PER_MINUTE if "/chat" in endpoint else MAX_REQUESTS_PER_MINUTE
        
        if is_rate_limited(client_ip, endpoint, max_requests):
            logger.warning(f"Rate limit exceeded for {client_ip} on {endpoint}")
            return HTTPException(
                status_code=429,
                detail="Rate limit exceeded. Please try again later."
            )
    
    response = await call_next(request)
    
    # Log request
    process_time = time.time() - start_time
    logger.info(f"{client_ip} - {request.method} {request.url.path} - {response.status_code} - {process_time:.3f}s")
    
    return response

# Add security middleware
app.middleware("http")(security_middleware)

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

@app.post("/api/chat")
async def chat_with_ai(request: Request):
    """Main chat endpoint for the voice widget with conversation memory and security"""
    try:
        body = await request.json()
        message = body.get("message", "").strip()
        session_id = body.get("session_id", str(uuid.uuid4()))
        site_id = body.get("site_id", "demo")
        
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
        
        # Get site-specific configuration
        site_config = await get_site_configuration(site_id)
        
        # AI Response logic with improved error handling
        ai_response = ""
        model_used = "demo"
        
        try:
            if groq_client:
                # Get conversation history for context
                conversation_history = await get_conversation_history(session_id, site_id)
                
                # Create conversation context with memory
                conversation_context = [
                    {
                        "role": "system",
                        "content": create_system_prompt(site_config)
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
                enhanced_message = await enhance_ai_context(message, site_config)
                conversation_context.append({
                    "role": "user",
                    "content": enhanced_message
                })
                
                # Get custom API key for site or use default
                api_key = site_config.get("groq_api_key") or os.getenv("GROQ_API_KEY")
                if api_key:
                    # Create client with custom API key if provided
                    client = Groq(api_key=api_key) if site_config.get("groq_api_key") else groq_client
                    
                    # Get response from GROQ with timeout
                    completion = client.chat.completions.create(
                        model="llama3-8b-8192",
                        messages=conversation_context,
                        max_tokens=200,
                        temperature=0.7,
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
            ai_response = generate_contextual_demo_response(message, conversation_history)
            model_used = "demo_fallback"
        
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
                    "tokens_used": len(message.split()) + len(ai_response.split()),
                    "client_ip": client_ip,
                    "user_agent": request.headers.get("user-agent", "unknown")
                }
                db.conversations.insert_one(conversation_log)
                logger.info(f"Conversation logged for session {session_id}")
            except Exception as e:
                logger.error(f"Failed to log conversation: {e}")
        
        # Get conversation history length
        conversation_history = await get_conversation_history(session_id, site_id)
        
        return {
            "response": ai_response,
            "session_id": session_id,
            "timestamp": datetime.utcnow().isoformat(),
            "model": model_used,
            "conversation_length": len(conversation_history) + 1,
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

# ============================================================================
# ENHANCED AI CONVERSATION FUNCTIONS
# ============================================================================

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
    """Filter AI responses for inappropriate content"""
    if not response:
        return "I apologize, but I couldn't generate a proper response. Please try again."
    
    # Remove any potential script injection
    for pattern in BLOCKED_PATTERNS:
        response = re.sub(pattern, '', response, flags=re.IGNORECASE)
    
    # Basic profanity filter (extend as needed)
    profanity_words = [
        'fuck', 'shit', 'damn', 'hell', 'bitch', 'ass', 'crap',
        'piss', 'bastard', 'whore', 'slut', 'retard'
    ]
    
    for word in profanity_words:
        response = re.sub(r'\b' + re.escape(word) + r'\b', '***', response, flags=re.IGNORECASE)
    
    # Ensure response is not too long for voice
    if len(response) > 500:
        response = response[:497] + "..."
    
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