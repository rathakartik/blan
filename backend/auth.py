from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import HTTPException, status
import secrets
import uuid
import os

# Security configurations
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-here-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
RESET_TOKEN_EXPIRE_MINUTES = 60

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """Generate password hash."""
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create JWT access token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def create_reset_token() -> str:
    """Create password reset token."""
    return secrets.token_urlsafe(32)

def verify_token(token: str) -> Optional[str]:
    """Verify JWT token and return email."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            return None
        return email
    except JWTError:
        return None

def generate_site_id() -> str:
    """Generate unique site ID."""
    return str(uuid.uuid4())

def generate_embed_script(site_id: str, backend_url: str) -> str:
    """Generate embed script for widget."""
    script = f"""
<!-- AI Voice Assistant Widget -->
<script>
(function() {{
    // Widget configuration
    const WIDGET_CONFIG = {{
        siteId: '{site_id}',
        backendUrl: '{backend_url}',
        version: '1.0.0'
    }};
    
    // Create widget container
    const widgetContainer = document.createElement('div');
    widgetContainer.id = 'ai-voice-widget-container';
    widgetContainer.setAttribute('data-site-id', WIDGET_CONFIG.siteId);
    
    // Widget styles
    const widgetStyles = document.createElement('style');
    widgetStyles.textContent = `
        #ai-voice-widget-container {{
            position: fixed;
            bottom: 20px;
            right: 20px;
            z-index: 9999;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
        }}
        
        .ai-widget-toggle {{
            width: 60px;
            height: 60px;
            border-radius: 50%;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            border: none;
            cursor: pointer;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
            display: flex;
            align-items: center;
            justify-content: center;
            transition: all 0.3s ease;
            color: white;
        }}
        
        .ai-widget-toggle:hover {{
            transform: scale(1.1);
            box-shadow: 0 6px 16px rgba(0, 0, 0, 0.15);
        }}
        
        .ai-widget-frame {{
            display: none;
            position: absolute;
            bottom: 80px;
            right: 0;
            width: 350px;
            height: 500px;
            border: none;
            border-radius: 12px;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
            background: white;
            overflow: hidden;
            animation: slideUp 0.3s ease-out;
        }}
        
        @keyframes slideUp {{
            from {{
                opacity: 0;
                transform: translateY(20px);
            }}
            to {{
                opacity: 1;
                transform: translateY(0);
            }}
        }}
        
        @media (max-width: 480px) {{
            .ai-widget-frame {{
                width: 300px;
                height: 450px;
            }}
        }}
    `;
    
    // Widget HTML
    widgetContainer.innerHTML = `
        <button class="ai-widget-toggle" onclick="toggleWidget()">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
        </button>
        <iframe id="ai-widget-frame" class="ai-widget-frame" src="{backend_url}/widget?site_id={site_id}"></iframe>
    `;
    
    // Toggle function
    window.toggleWidget = function() {{
        const frame = document.getElementById('ai-widget-frame');
        if (frame.style.display === 'none' || frame.style.display === '') {{
            frame.style.display = 'block';
            // Log widget open
            fetch(`${{WIDGET_CONFIG.backendUrl}}/api/analytics/interaction`, {{
                method: 'POST',
                headers: {{ 'Content-Type': 'application/json' }},
                body: JSON.stringify({{
                    site_id: WIDGET_CONFIG.siteId,
                    session_id: 'embed-session',
                    type: 'widget_open'
                }})
            }}).catch(console.error);
        }} else {{
            frame.style.display = 'none';
            // Log widget close
            fetch(`${{WIDGET_CONFIG.backendUrl}}/api/analytics/interaction`, {{
                method: 'POST',
                headers: {{ 'Content-Type': 'application/json' }},
                body: JSON.stringify({{
                    site_id: WIDGET_CONFIG.siteId,
                    session_id: 'embed-session',
                    type: 'widget_close'
                }})
            }}).catch(console.error);
        }}
    }};
    
    // Initialize widget
    document.head.appendChild(widgetStyles);
    document.body.appendChild(widgetContainer);
    
    console.log('AI Voice Assistant Widget loaded successfully');
}})();
</script>
"""
    return script.strip()

def get_installation_instructions(site_id: str) -> str:
    """Generate installation instructions."""
    return f"""
# AI Voice Assistant Widget Installation

## Quick Setup (Recommended)

1. **Copy the embed script** provided above
2. **Paste it before the closing `</body>` tag** in your website's HTML
3. **That's it!** The widget will automatically load on your site

## Advanced Configuration

### Custom Positioning
Add these CSS variables to override default positioning:

```css
:root {{
    --ai-widget-bottom: 20px;
    --ai-widget-right: 20px;
}}
```

### Custom Styling
Target the widget container with CSS:

```css
#ai-voice-widget-container {{
    /* Your custom styles here */
}}
```

## Requirements

- **Modern Browser**: Chrome, Firefox, Safari, Edge
- **HTTPS**: Required for voice features in production
- **Microphone Permissions**: Users will be prompted when using voice features

## Support

- **Site ID**: `{site_id}`
- **Status**: Check your dashboard for real-time analytics
- **Issues**: Contact support through your dashboard

## Testing

1. Load your website
2. Look for the chat icon in the bottom-right corner
3. Click to open the widget
4. Test voice features (requires microphone permission)
5. Check your dashboard for interaction analytics

**Note**: The widget will automatically adapt to your site's theme and configuration settings from the dashboard.
"""

# Email utilities (for password reset)
def generate_reset_email_content(reset_token: str, user_name: str) -> tuple:
    """Generate password reset email content."""
    reset_url = f"https://your-domain.com/reset-password?token={reset_token}"
    
    subject = "Reset Your AI Voice Assistant Password"
    
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Password Reset</title>
        <style>
            body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
            .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
            .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; text-align: center; }}
            .content {{ padding: 30px; background: #f8f9fa; }}
            .button {{ display: inline-block; padding: 12px 30px; background: #007bff; color: white; text-decoration: none; border-radius: 5px; }}
            .footer {{ padding: 20px; text-align: center; font-size: 12px; color: #666; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>Password Reset Request</h1>
            </div>
            <div class="content">
                <p>Hi {user_name},</p>
                <p>We received a request to reset your password for your AI Voice Assistant account.</p>
                <p>Click the button below to reset your password:</p>
                <p style="text-align: center; margin: 30px 0;">
                    <a href="{reset_url}" class="button">Reset Password</a>
                </p>
                <p>If you didn't request this password reset, please ignore this email.</p>
                <p>This link will expire in 60 minutes for security reasons.</p>
            </div>
            <div class="footer">
                <p>AI Voice Assistant | Secure Authentication System</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    return subject, html_content

def validate_site_domain(domain: str) -> bool:
    """Validate site domain format."""
    import re
    pattern = r'^[a-zA-Z0-9]([a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?(\.[a-zA-Z0-9]([a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?)*$'
    return re.match(pattern, domain) is not None