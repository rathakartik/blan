from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
import uuid

# User Models
class UserBase(BaseModel):
    email: EmailStr
    full_name: str

class UserCreate(UserBase):
    password: str

class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    password: Optional[str] = None

class UserResponse(UserBase):
    id: str
    created_at: datetime
    updated_at: datetime
    is_active: bool

# Authentication Models
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: Optional[str] = None

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class PasswordResetRequest(BaseModel):
    email: EmailStr

class PasswordReset(BaseModel):
    token: str
    new_password: str

# Site Models
class SiteTheme(BaseModel):
    primary_color: str = "#3B82F6"
    secondary_color: str = "#1E40AF"
    text_color: str = "#1F2937"
    background_color: str = "#FFFFFF"
    danger_color: str = "#EF4444"

class SiteBase(BaseModel):
    name: str
    domain: str
    description: Optional[str] = None
    greeting_message: str = "Hi there! I'm your virtual assistant. How can I help you today?"
    bot_name: str = "AI Assistant"
    theme: SiteTheme = Field(default_factory=SiteTheme)
    position: str = "bottom-right"
    auto_greet: bool = True
    voice_enabled: bool = True
    language: str = "en-US"
    groq_api_key: Optional[str] = None
    is_active: bool = True

class SiteCreate(SiteBase):
    pass

class SiteUpdate(BaseModel):
    name: Optional[str] = None
    domain: Optional[str] = None
    description: Optional[str] = None
    greeting_message: Optional[str] = None
    bot_name: Optional[str] = None
    theme: Optional[SiteTheme] = None
    position: Optional[str] = None
    auto_greet: Optional[bool] = None
    voice_enabled: Optional[bool] = None
    language: Optional[str] = None
    groq_api_key: Optional[str] = None
    is_active: Optional[bool] = None

class SiteResponse(SiteBase):
    id: str
    user_id: str
    created_at: datetime
    updated_at: datetime
    total_interactions: int = 0
    total_conversations: int = 0
    last_interaction: Optional[datetime] = None

# Analytics Models
class InteractionCreate(BaseModel):
    site_id: str
    session_id: str
    interaction_type: str
    user_message: Optional[str] = None
    ai_response: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class InteractionResponse(BaseModel):
    id: str
    site_id: str
    session_id: str
    interaction_type: str
    user_message: Optional[str] = None
    ai_response: Optional[str] = None
    timestamp: datetime

class AnalyticsStats(BaseModel):
    total_interactions: int
    total_sessions: int
    total_conversations: int
    avg_session_duration: float
    top_interaction_types: List[Dict[str, Any]]
    daily_stats: List[Dict[str, Any]]
    popular_questions: List[Dict[str, Any]]

class DashboardStats(BaseModel):
    total_sites: int
    total_interactions: int
    total_conversations: int
    active_sessions: int
    recent_interactions: List[InteractionResponse]
    site_performance: List[Dict[str, Any]]

# Configuration Models
class WidgetConfig(BaseModel):
    site_id: str
    greeting_message: str
    bot_name: str
    theme: SiteTheme
    position: str
    auto_greet: bool
    voice_enabled: bool
    language: str

class EmbedScript(BaseModel):
    site_id: str
    script_content: str
    installation_instructions: str

# Database Models (for MongoDB)
class UserDB(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    email: str
    full_name: str
    hashed_password: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    is_active: bool = True
    reset_token: Optional[str] = None
    reset_token_expires: Optional[datetime] = None

class SiteDB(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    name: str
    domain: str
    description: Optional[str] = None
    greeting_message: str = "Hi there! I'm your virtual assistant. How can I help you today?"
    bot_name: str = "AI Assistant"
    theme: Dict[str, str] = Field(default_factory=lambda: {
        "primary_color": "#3B82F6",
        "secondary_color": "#1E40AF",
        "text_color": "#1F2937",
        "background_color": "#FFFFFF",
        "danger_color": "#EF4444"
    })
    position: str = "bottom-right"
    auto_greet: bool = True
    voice_enabled: bool = True
    language: str = "en-US"
    groq_api_key: Optional[str] = None
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class InteractionDB(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    site_id: str
    session_id: str
    interaction_type: str
    user_message: Optional[str] = None
    ai_response: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    user_agent: Optional[str] = None
    ip_address: Optional[str] = None