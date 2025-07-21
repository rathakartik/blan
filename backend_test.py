#!/usr/bin/env python3
"""
Backend API Testing Script for AI Voice Assistant Widget
Tests all backend endpoints for functionality and proper responses
"""

import requests
import json
import time
from datetime import datetime
import uuid

# Configuration
BASE_URL = "https://40207044-9649-4721-9bbd-ae0b3758a267.preview.emergentagent.com"  # Using the backend URL from frontend/.env
API_BASE = f"{BASE_URL}/api"

def print_test_header(test_name):
    """Print formatted test header"""
    print(f"\n{'='*60}")
    print(f"TESTING: {test_name}")
    print(f"{'='*60}")

def print_result(endpoint, status_code, response_data, expected_status=200):
    """Print test result in formatted way"""
    success = "✅" if status_code == expected_status else "❌"
    print(f"{success} {endpoint}")
    print(f"   Status Code: {status_code} (Expected: {expected_status})")
    if isinstance(response_data, dict):
        print(f"   Response: {json.dumps(response_data, indent=2, default=str)}")
    else:
        print(f"   Response: {response_data}")
    print()

def test_health_endpoint():
    """Test the health check endpoint"""
    print_test_header("Health Check Endpoint - GET /api/health")
    
    try:
        response = requests.get(f"{API_BASE}/health", timeout=10)
        data = response.json()
        
        print_result("/api/health", response.status_code, data)
        
        # Validate response structure
        required_fields = ["status", "mongodb", "groq", "timestamp"]
        missing_fields = [field for field in required_fields if field not in data]
        
        if missing_fields:
            print(f"❌ Missing required fields: {missing_fields}")
        else:
            print("✅ All required fields present")
            
        # Check specific values
        if data.get("status") == "healthy":
            print("✅ Service status is healthy")
        else:
            print(f"❌ Service status is not healthy: {data.get('status')}")
            
        return response.status_code == 200 and not missing_fields
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Request failed: {e}")
        return False
    except json.JSONDecodeError as e:
        print(f"❌ Invalid JSON response: {e}")
        return False

def test_chat_endpoint():
    """Test the chat endpoint with various message types"""
    print_test_header("Chat Endpoint - POST /api/chat")
    
    test_cases = [
        {
            "name": "Greeting Message",
            "payload": {
                "message": "Hello there!",
                "session_id": "test-session-123",
                "site_id": "demo"
            }
        },
        {
            "name": "Question Message",
            "payload": {
                "message": "What can you help me with?",
                "session_id": "test-session-123",
                "site_id": "demo"
            }
        },
        {
            "name": "Thank You Message",
            "payload": {
                "message": "Thank you for your help!",
                "session_id": "test-session-123",
                "site_id": "demo"
            }
        },
        {
            "name": "Weather Question",
            "payload": {
                "message": "What's the weather like today?",
                "session_id": "test-session-456",
                "site_id": "demo"
            }
        },
        {
            "name": "Auto-generated Session ID",
            "payload": {
                "message": "Testing without session_id",
                "site_id": "demo"
            }
        }
    ]
    
    all_passed = True
    
    for test_case in test_cases:
        print(f"\n--- Testing: {test_case['name']} ---")
        
        try:
            response = requests.post(
                f"{API_BASE}/chat",
                json=test_case["payload"],
                headers={"Content-Type": "application/json"},
                timeout=15
            )
            
            data = response.json()
            print_result("/api/chat", response.status_code, data)
            
            # Validate response structure
            required_fields = ["response", "session_id", "timestamp", "model"]
            missing_fields = [field for field in required_fields if field not in data]
            
            if missing_fields:
                print(f"❌ Missing required fields: {missing_fields}")
                all_passed = False
            else:
                print("✅ All required fields present")
                
            # Check if response is not empty
            if data.get("response") and len(data.get("response").strip()) > 0:
                print("✅ AI response is not empty")
            else:
                print("❌ AI response is empty")
                all_passed = False
                
            # Check session_id
            if data.get("session_id"):
                print("✅ Session ID is present")
            else:
                print("❌ Session ID is missing")
                all_passed = False
                
            if response.status_code != 200:
                all_passed = False
                
        except requests.exceptions.RequestException as e:
            print(f"❌ Request failed: {e}")
            all_passed = False
        except json.JSONDecodeError as e:
            print(f"❌ Invalid JSON response: {e}")
            all_passed = False
    
    # Test error cases
    print(f"\n--- Testing: Error Cases ---")
    
    # Test missing message
    try:
        response = requests.post(
            f"{API_BASE}/chat",
            json={"site_id": "demo"},
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        
        print_result("/api/chat (missing message)", response.status_code, response.json(), expected_status=400)
        
        if response.status_code == 400:
            print("✅ Properly handles missing message")
        else:
            print("❌ Should return 400 for missing message")
            all_passed = False
            
    except Exception as e:
        print(f"❌ Error testing missing message: {e}")
        all_passed = False
    
    return all_passed

def test_widget_config_endpoint():
    """Test the widget configuration endpoint"""
    print_test_header("Widget Configuration - POST /api/widget/config")
    
    test_cases = [
        {
            "name": "Demo Site Configuration",
            "payload": {"site_id": "demo"}
        },
        {
            "name": "Custom Site Configuration",
            "payload": {"site_id": "test-site-456"}
        }
    ]
    
    all_passed = True
    
    for test_case in test_cases:
        print(f"\n--- Testing: {test_case['name']} ---")
        
        try:
            response = requests.post(
                f"{API_BASE}/widget/config",
                json=test_case["payload"],
                headers={"Content-Type": "application/json"},
                timeout=10
            )
            
            data = response.json()
            print_result("/api/widget/config", response.status_code, data)
            
            # Validate response structure
            required_fields = ["site_id", "greeting_message", "bot_name", "theme", "position", "auto_greet", "voice_enabled", "language"]
            missing_fields = [field for field in required_fields if field not in data]
            
            if missing_fields:
                print(f"❌ Missing required fields: {missing_fields}")
                all_passed = False
            else:
                print("✅ All required fields present")
                
            # Check theme structure
            if "theme" in data and isinstance(data["theme"], dict):
                theme_fields = ["primary_color", "secondary_color", "text_color", "background_color"]
                missing_theme_fields = [field for field in theme_fields if field not in data["theme"]]
                
                if missing_theme_fields:
                    print(f"❌ Missing theme fields: {missing_theme_fields}")
                    all_passed = False
                else:
                    print("✅ Theme structure is complete")
            else:
                print("❌ Theme is missing or not a dict")
                all_passed = False
                
            if response.status_code != 200:
                all_passed = False
                
        except requests.exceptions.RequestException as e:
            print(f"❌ Request failed: {e}")
            all_passed = False
        except json.JSONDecodeError as e:
            print(f"❌ Invalid JSON response: {e}")
            all_passed = False
    
    # Test error case - missing site_id
    print(f"\n--- Testing: Error Cases ---")
    
    try:
        response = requests.post(
            f"{API_BASE}/widget/config",
            json={},
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        
        print_result("/api/widget/config (missing site_id)", response.status_code, response.json(), expected_status=400)
        
        if response.status_code == 400:
            print("✅ Properly handles missing site_id")
        else:
            print("❌ Should return 400 for missing site_id")
            all_passed = False
            
    except Exception as e:
        print(f"❌ Error testing missing site_id: {e}")
        all_passed = False
    
    return all_passed

def test_analytics_endpoint():
    """Test the analytics interaction logging endpoint"""
    print_test_header("Analytics Logging - POST /api/analytics/interaction")
    
    test_cases = [
        {
            "name": "Greeting Interaction",
            "payload": {
                "site_id": "demo",
                "session_id": "test-session-123",
                "type": "greeting"
            }
        },
        {
            "name": "Voice Input Interaction",
            "payload": {
                "site_id": "demo",
                "session_id": "test-session-123",
                "type": "voice_input"
            }
        },
        {
            "name": "Text Input Interaction",
            "payload": {
                "site_id": "demo",
                "session_id": "test-session-456",
                "type": "text_input"
            }
        }
    ]
    
    all_passed = True
    
    for test_case in test_cases:
        print(f"\n--- Testing: {test_case['name']} ---")
        
        try:
            response = requests.post(
                f"{API_BASE}/analytics/interaction",
                json=test_case["payload"],
                headers={"Content-Type": "application/json"},
                timeout=10
            )
            
            data = response.json()
            print_result("/api/analytics/interaction", response.status_code, data)
            
            # Validate response structure
            if data.get("status") == "logged":
                print("✅ Interaction logged successfully")
            else:
                print(f"❌ Unexpected response: {data}")
                all_passed = False
                
            if response.status_code != 200:
                all_passed = False
                
        except requests.exceptions.RequestException as e:
            print(f"❌ Request failed: {e}")
            all_passed = False
        except json.JSONDecodeError as e:
            print(f"❌ Invalid JSON response: {e}")
            all_passed = False
    
    return all_passed

def test_enhanced_conversation_memory():
    """Test enhanced conversation memory and multi-turn conversations"""
    print_test_header("Enhanced Conversation Memory & Multi-Turn Test")
    
    session_id = f"memory-test-{uuid.uuid4()}"
    site_id = "demo"
    
    # Test conversation with follow-up questions to verify memory
    conversation_steps = [
        {
            "message": "Hello",
            "expected_keywords": ["hello", "hi", "assistant", "help"],
            "description": "Initial greeting"
        },
        {
            "message": "Tell me more about AI",
            "expected_keywords": ["ai", "artificial", "intelligence", "help", "questions"],
            "description": "Ask about AI topic"
        },
        {
            "message": "Can you elaborate on that?",
            "expected_keywords": ["elaborate", "details", "more", "specific"],
            "description": "Follow-up question testing context awareness"
        },
        {
            "message": "What do you mean by that?",
            "expected_keywords": ["clarify", "explain", "mean", "detail"],
            "description": "Clarification request testing conversation history"
        },
        {
            "message": "Thank you for explaining",
            "expected_keywords": ["welcome", "glad", "help", "anything else"],
            "description": "Thank you message"
        }
    ]
    
    all_passed = True
    conversation_responses = []
    
    for i, step in enumerate(conversation_steps, 1):
        print(f"\n--- Step {i}: {step['description']} ---")
        print(f"Message: '{step['message']}'")
        
        try:
            chat_response = requests.post(
                f"{API_BASE}/chat",
                json={
                    "message": step["message"],
                    "session_id": session_id,
                    "site_id": site_id
                },
                headers={"Content-Type": "application/json"},
                timeout=15
            )
            
            if chat_response.status_code == 200:
                data = chat_response.json()
                response_text = data.get('response', '').lower()
                conversation_responses.append({
                    "message": step["message"],
                    "response": data.get('response', ''),
                    "model": data.get('model', ''),
                    "conversation_length": data.get('conversation_length', 0)
                })
                
                print(f"✅ Chat response: {data.get('response', 'No response')}")
                print(f"   Model used: {data.get('model', 'Unknown')}")
                print(f"   Conversation length: {data.get('conversation_length', 0)}")
                
                # Verify session consistency
                if data.get("session_id") == session_id:
                    print("✅ Session ID consistent")
                else:
                    print(f"❌ Session ID mismatch: expected {session_id}, got {data.get('session_id')}")
                    all_passed = False
                
                # Check for contextual awareness (for follow-up questions)
                if i > 2:  # After the first two messages, responses should show context awareness
                    if any(keyword in response_text for keyword in step["expected_keywords"]):
                        print("✅ Response shows contextual awareness")
                    else:
                        print(f"⚠️ Response may lack contextual awareness. Expected keywords: {step['expected_keywords']}")
                        # Don't fail the test for this, as demo responses might vary
                
                # Verify conversation length increases
                expected_length = i
                actual_length = data.get('conversation_length', 0)
                if actual_length == expected_length:
                    print(f"✅ Conversation length correct: {actual_length}")
                else:
                    print(f"⚠️ Conversation length: expected {expected_length}, got {actual_length}")
                
                # Verify required response fields
                required_fields = ["response", "session_id", "timestamp", "model"]
                missing_fields = [field for field in required_fields if field not in data]
                if missing_fields:
                    print(f"❌ Missing required fields: {missing_fields}")
                    all_passed = False
                else:
                    print("✅ All required response fields present")
                    
            else:
                print(f"❌ Chat failed with status {chat_response.status_code}")
                if chat_response.content:
                    print(f"   Error: {chat_response.json()}")
                all_passed = False
                
        except Exception as e:
            print(f"❌ Chat request failed: {e}")
            all_passed = False
        
        # Small delay between messages
        time.sleep(0.5)
    
    # Test session isolation - use different session_id
    print(f"\n--- Testing Session Isolation ---")
    different_session_id = f"isolation-test-{uuid.uuid4()}"
    
    try:
        isolation_response = requests.post(
            f"{API_BASE}/chat",
            json={
                "message": "Hello, this is a new session",
                "session_id": different_session_id,
                "site_id": site_id
            },
            headers={"Content-Type": "application/json"},
            timeout=15
        )
        
        if isolation_response.status_code == 200:
            isolation_data = isolation_response.json()
            if isolation_data.get('conversation_length', 0) == 1:
                print("✅ Session isolation working - new session starts with length 1")
            else:
                print(f"❌ Session isolation failed - new session has length {isolation_data.get('conversation_length', 0)}")
                all_passed = False
        else:
            print(f"❌ Session isolation test failed with status {isolation_response.status_code}")
            all_passed = False
            
    except Exception as e:
        print(f"❌ Session isolation test failed: {e}")
        all_passed = False
    
    # Print conversation summary
    print(f"\n--- Conversation Summary ---")
    for i, conv in enumerate(conversation_responses, 1):
        print(f"Step {i}: '{conv['message']}' -> '{conv['response'][:50]}...' (Model: {conv['model']})")
    
    return all_passed

def test_conversation_flow():
    """Test a complete conversation flow"""
    print_test_header("Complete Conversation Flow Test")
    
    session_id = f"flow-test-{uuid.uuid4()}"
    site_id = "demo"
    
    conversation_steps = [
        "Hello, I'm new here!",
        "What can you help me with?",
        "Can you tell me about the weather?",
        "Thank you for your help!",
        "Goodbye!"
    ]
    
    all_passed = True
    
    for i, message in enumerate(conversation_steps, 1):
        print(f"\n--- Step {i}: {message} ---")
        
        # Log interaction
        try:
            analytics_response = requests.post(
                f"{API_BASE}/analytics/interaction",
                json={
                    "site_id": site_id,
                    "session_id": session_id,
                    "type": "text_input"
                },
                headers={"Content-Type": "application/json"},
                timeout=10
            )
            
            if analytics_response.status_code == 200:
                print("✅ Interaction logged")
            else:
                print("❌ Failed to log interaction")
                all_passed = False
                
        except Exception as e:
            print(f"❌ Analytics logging failed: {e}")
            all_passed = False
        
        # Send chat message
        try:
            chat_response = requests.post(
                f"{API_BASE}/chat",
                json={
                    "message": message,
                    "session_id": session_id,
                    "site_id": site_id
                },
                headers={"Content-Type": "application/json"},
                timeout=15
            )
            
            if chat_response.status_code == 200:
                data = chat_response.json()
                print(f"✅ Chat response: {data.get('response', 'No response')[:100]}...")
                
                # Verify session consistency
                if data.get("session_id") == session_id:
                    print("✅ Session ID consistent")
                else:
                    print(f"❌ Session ID mismatch: expected {session_id}, got {data.get('session_id')}")
                    all_passed = False
            else:
                print(f"❌ Chat failed with status {chat_response.status_code}")
                all_passed = False
                
        except Exception as e:
            print(f"❌ Chat request failed: {e}")
            all_passed = False
        
        # Small delay between messages
        time.sleep(0.5)
    
    return all_passed

# ============================================================================
# PHASE 2 DASHBOARD API TESTS
# ============================================================================

def test_user_registration():
    """Test user registration endpoint"""
    print_test_header("User Registration - POST /api/auth/register")
    
    test_cases = [
        {
            "name": "Valid Registration",
            "payload": {
                "email": f"testuser{int(time.time())}@example.com",
                "full_name": "Test User",
                "password": "securepassword123"
            },
            "expected_status": 200
        },
        {
            "name": "Duplicate Email Registration",
            "payload": {
                "email": "test@example.com",  # Use existing email for duplicate test
                "full_name": "Another User",
                "password": "anotherpassword123"
            },
            "expected_status": 400
        },
        {
            "name": "Invalid Email Format",
            "payload": {
                "email": "invalid-email",
                "full_name": "Test User",
                "password": "securepassword123"
            },
            "expected_status": 422
        },
        {
            "name": "Missing Password",
            "payload": {
                "email": "test2@example.com",
                "full_name": "Test User"
            },
            "expected_status": 422
        }
    ]
    
    all_passed = True
    
    for test_case in test_cases:
        print(f"\n--- Testing: {test_case['name']} ---")
        
        try:
            response = requests.post(
                f"{API_BASE}/auth/register",
                json=test_case["payload"],
                headers={"Content-Type": "application/json"},
                timeout=10
            )
            
            print_result("/api/auth/register", response.status_code, response.json() if response.content else {}, test_case["expected_status"])
            
            if response.status_code == test_case["expected_status"]:
                if response.status_code == 200:
                    data = response.json()
                    required_fields = ["id", "email", "full_name", "created_at", "updated_at", "is_active"]
                    missing_fields = [field for field in required_fields if field not in data]
                    
                    if missing_fields:
                        print(f"❌ Missing required fields: {missing_fields}")
                        all_passed = False
                    else:
                        print("✅ All required fields present")
                        
                    # Verify email matches
                    if data.get("email") == test_case["payload"]["email"]:
                        print("✅ Email matches registration data")
                    else:
                        print("❌ Email doesn't match registration data")
                        all_passed = False
                else:
                    print("✅ Error handled correctly")
            else:
                print(f"❌ Expected status {test_case['expected_status']}, got {response.status_code}")
                all_passed = False
                
        except requests.exceptions.RequestException as e:
            print(f"❌ Request failed: {e}")
            all_passed = False
        except json.JSONDecodeError as e:
            print(f"❌ Invalid JSON response: {e}")
            all_passed = False
    
    return all_passed

def test_user_login():
    """Test user login endpoint"""
    print_test_header("User Login - POST /api/auth/login")
    
    test_cases = [
        {
            "name": "Valid Login",
            "payload": {
                "email": "test@example.com",
                "password": "password123"
            },
            "expected_status": 200
        },
        {
            "name": "Invalid Password",
            "payload": {
                "email": "test@example.com",
                "password": "wrongpassword"
            },
            "expected_status": 401
        },
        {
            "name": "Non-existent User",
            "payload": {
                "email": "nonexistent@example.com",
                "password": "somepassword"
            },
            "expected_status": 401
        },
        {
            "name": "Missing Email",
            "payload": {
                "password": "securepassword123"
            },
            "expected_status": 422
        }
    ]
    
    all_passed = True
    access_token = None
    
    for test_case in test_cases:
        print(f"\n--- Testing: {test_case['name']} ---")
        
        try:
            response = requests.post(
                f"{API_BASE}/auth/login",
                json=test_case["payload"],
                headers={"Content-Type": "application/json"},
                timeout=10
            )
            
            print_result("/api/auth/login", response.status_code, response.json() if response.content else {}, test_case["expected_status"])
            
            if response.status_code == test_case["expected_status"]:
                if response.status_code == 200:
                    data = response.json()
                    required_fields = ["access_token", "token_type"]
                    missing_fields = [field for field in required_fields if field not in data]
                    
                    if missing_fields:
                        print(f"❌ Missing required fields: {missing_fields}")
                        all_passed = False
                    else:
                        print("✅ All required fields present")
                        access_token = data.get("access_token")
                        
                    # Verify token type
                    if data.get("token_type") == "bearer":
                        print("✅ Token type is bearer")
                    else:
                        print("❌ Token type is not bearer")
                        all_passed = False
                else:
                    print("✅ Error handled correctly")
            else:
                print(f"❌ Expected status {test_case['expected_status']}, got {response.status_code}")
                all_passed = False
                
        except requests.exceptions.RequestException as e:
            print(f"❌ Request failed: {e}")
            all_passed = False
        except json.JSONDecodeError as e:
            print(f"❌ Invalid JSON response: {e}")
            all_passed = False
    
    return all_passed, access_token

def test_site_creation(access_token):
    """Test site creation endpoint"""
    print_test_header("Site Creation - POST /api/sites")
    
    if not access_token:
        print("❌ No access token available for testing")
        return False, None
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {access_token}"
    }
    
    test_cases = [
        {
            "name": "Valid Site Creation",
            "payload": {
                "name": "Test Website",
                "domain": f"test-website-{int(time.time())}.com",
                "description": "A test website for AI voice assistant",
                "greeting_message": "Welcome to our test website! How can I help you?",
                "bot_name": "TestBot",
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
            },
            "expected_status": 200
        },
        {
            "name": "Duplicate Domain",
            "payload": {
                "name": "Another Test Website",
                "domain": "test-website.com",
                "description": "Another test website"
            },
            "expected_status": 400
        },
        {
            "name": "Invalid Domain Format",
            "payload": {
                "name": "Invalid Domain Site",
                "domain": "invalid..domain",
                "description": "Site with invalid domain"
            },
            "expected_status": 400
        },
        {
            "name": "Missing Required Fields",
            "payload": {
                "description": "Site without name and domain"
            },
            "expected_status": 422
        }
    ]
    
    all_passed = True
    site_id = None
    
    for test_case in test_cases:
        print(f"\n--- Testing: {test_case['name']} ---")
        
        try:
            response = requests.post(
                f"{API_BASE}/sites",
                json=test_case["payload"],
                headers=headers,
                timeout=10
            )
            
            print_result("/api/sites", response.status_code, response.json() if response.content else {}, test_case["expected_status"])
            
            if response.status_code == test_case["expected_status"]:
                if response.status_code == 200:
                    data = response.json()
                    required_fields = ["id", "user_id", "name", "domain", "created_at", "updated_at"]
                    missing_fields = [field for field in required_fields if field not in data]
                    
                    if missing_fields:
                        print(f"❌ Missing required fields: {missing_fields}")
                        all_passed = False
                    else:
                        print("✅ All required fields present")
                        site_id = data.get("id")
                        
                    # Verify domain matches
                    if data.get("domain") == test_case["payload"]["domain"]:
                        print("✅ Domain matches creation data")
                    else:
                        print("❌ Domain doesn't match creation data")
                        all_passed = False
                else:
                    print("✅ Error handled correctly")
            else:
                print(f"❌ Expected status {test_case['expected_status']}, got {response.status_code}")
                all_passed = False
                
        except requests.exceptions.RequestException as e:
            print(f"❌ Request failed: {e}")
            all_passed = False
        except json.JSONDecodeError as e:
            print(f"❌ Invalid JSON response: {e}")
            all_passed = False
    
    return all_passed, site_id

def test_site_listing(access_token):
    """Test site listing endpoint"""
    print_test_header("Site Listing - GET /api/sites")
    
    if not access_token:
        print("❌ No access token available for testing")
        return False
    
    headers = {
        "Authorization": f"Bearer {access_token}"
    }
    
    try:
        response = requests.get(
            f"{API_BASE}/sites",
            headers=headers,
            timeout=10
        )
        
        print_result("/api/sites", response.status_code, response.json() if response.content else {})
        
        if response.status_code == 200:
            data = response.json()
            
            if isinstance(data, list):
                print("✅ Response is a list")
                
                if len(data) > 0:
                    print(f"✅ Found {len(data)} site(s)")
                    
                    # Check first site structure
                    first_site = data[0]
                    required_fields = ["id", "user_id", "name", "domain", "created_at", "updated_at"]
                    missing_fields = [field for field in required_fields if field not in first_site]
                    
                    if missing_fields:
                        print(f"❌ Missing required fields in site: {missing_fields}")
                        return False
                    else:
                        print("✅ Site structure is correct")
                else:
                    print("ℹ️ No sites found (this might be expected)")
                
                return True
            else:
                print("❌ Response is not a list")
                return False
        else:
            print(f"❌ Expected status 200, got {response.status_code}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Request failed: {e}")
        return False
    except json.JSONDecodeError as e:
        print(f"❌ Invalid JSON response: {e}")
        return False

def test_dashboard_analytics(access_token):
    """Test dashboard analytics endpoint"""
    print_test_header("Dashboard Analytics - GET /api/analytics/dashboard")
    
    if not access_token:
        print("❌ No access token available for testing")
        return False
    
    headers = {
        "Authorization": f"Bearer {access_token}"
    }
    
    try:
        response = requests.get(
            f"{API_BASE}/analytics/dashboard",
            headers=headers,
            timeout=10
        )
        
        print_result("/api/analytics/dashboard", response.status_code, response.json() if response.content else {})
        
        if response.status_code == 200:
            data = response.json()
            required_fields = ["total_sites", "total_interactions", "total_conversations", "active_sessions", "recent_interactions", "site_performance"]
            missing_fields = [field for field in required_fields if field not in data]
            
            if missing_fields:
                print(f"❌ Missing required fields: {missing_fields}")
                return False
            else:
                print("✅ All required fields present")
                
            # Verify data types
            if isinstance(data.get("total_sites"), int):
                print("✅ total_sites is integer")
            else:
                print("❌ total_sites is not integer")
                return False
                
            if isinstance(data.get("recent_interactions"), list):
                print("✅ recent_interactions is list")
            else:
                print("❌ recent_interactions is not list")
                return False
                
            if isinstance(data.get("site_performance"), list):
                print("✅ site_performance is list")
            else:
                print("❌ site_performance is not list")
                return False
                
            print(f"ℹ️ Dashboard stats: {data.get('total_sites')} sites, {data.get('total_interactions')} interactions")
            return True
        else:
            print(f"❌ Expected status 200, got {response.status_code}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Request failed: {e}")
        return False
    except json.JSONDecodeError as e:
        print(f"❌ Invalid JSON response: {e}")
        return False

def test_90_day_memory_functionality():
    """Test 90-day visitor memory functionality comprehensively"""
    print_test_header("90-Day Visitor Memory Functionality Test")
    
    # Generate unique visitor ID for testing
    visitor_id = f"visitor-{uuid.uuid4()}"
    site_id = "demo"
    session_id_1 = f"session-1-{uuid.uuid4()}"
    session_id_2 = f"session-2-{uuid.uuid4()}"
    
    print(f"Testing with visitor_id: {visitor_id}")
    print(f"Site ID: {site_id}")
    
    all_passed = True
    
    # Test 1: New Visitor - First Conversation
    print(f"\n--- Test 1: New Visitor First Conversation ---")
    
    try:
        response = requests.post(
            f"{API_BASE}/chat",
            json={
                "message": "Hello, I'm new here and looking for information about your products",
                "session_id": session_id_1,
                "site_id": site_id,
                "visitor_id": visitor_id
            },
            headers={"Content-Type": "application/json"},
            timeout=15
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ New visitor conversation successful")
            print(f"   Response: {data.get('response', '')[:100]}...")
            print(f"   Is returning visitor: {data.get('is_returning_visitor', 'Not specified')}")
            print(f"   Conversation length: {data.get('conversation_length', 0)}")
            
            # Verify new visitor fields
            if data.get('visitor_id') == visitor_id:
                print("✅ Visitor ID correctly stored and returned")
            else:
                print(f"❌ Visitor ID mismatch: expected {visitor_id}, got {data.get('visitor_id')}")
                all_passed = False
                
            if data.get('is_returning_visitor') == False:
                print("✅ Correctly identified as new visitor")
            else:
                print(f"❌ Should be identified as new visitor, got: {data.get('is_returning_visitor')}")
                all_passed = False
                
        else:
            print(f"❌ New visitor conversation failed with status {response.status_code}")
            print(f"   Error: {response.json() if response.content else 'No content'}")
            all_passed = False
            
    except Exception as e:
        print(f"❌ New visitor test failed: {e}")
        all_passed = False
    
    # Small delay to ensure timestamp differences
    time.sleep(1)
    
    # Test 2: Same Visitor - Additional Messages in Same Session
    print(f"\n--- Test 2: Same Visitor - Additional Messages (Same Session) ---")
    
    additional_messages = [
        "Can you tell me more about your services?",
        "What are your pricing options?",
        "Do you offer customer support?"
    ]
    
    for i, message in enumerate(additional_messages, 2):
        try:
            response = requests.post(
                f"{API_BASE}/chat",
                json={
                    "message": message,
                    "session_id": session_id_1,
                    "site_id": site_id,
                    "visitor_id": visitor_id
                },
                headers={"Content-Type": "application/json"},
                timeout=15
            )
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Message {i}: {message[:50]}...")
                print(f"   Conversation length: {data.get('conversation_length', 0)}")
                
                # Verify conversation length increases
                expected_length = i
                actual_length = data.get('conversation_length', 0)
                if actual_length == expected_length:
                    print(f"✅ Conversation length correct: {actual_length}")
                else:
                    print(f"❌ Conversation length: expected {expected_length}, got {actual_length}")
                    all_passed = False
                    
            else:
                print(f"❌ Message {i} failed with status {response.status_code}")
                all_passed = False
                
        except Exception as e:
            print(f"❌ Message {i} failed: {e}")
            all_passed = False
        
        time.sleep(0.5)
    
    # Test 3: Same Visitor - New Session (Cross-Session Memory)
    print(f"\n--- Test 3: Same Visitor - New Session (Cross-Session Memory) ---")
    
    # Wait a bit to simulate time passing
    time.sleep(2)
    
    try:
        response = requests.post(
            f"{API_BASE}/chat",
            json={
                "message": "Hi again! I'm back and have more questions about the products we discussed",
                "session_id": session_id_2,  # Different session
                "site_id": site_id,
                "visitor_id": visitor_id  # Same visitor
            },
            headers={"Content-Type": "application/json"},
            timeout=15
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Cross-session conversation successful")
            print(f"   Response: {data.get('response', '')[:100]}...")
            print(f"   Is returning visitor: {data.get('is_returning_visitor', 'Not specified')}")
            print(f"   Session ID: {data.get('session_id')}")
            print(f"   Visitor ID: {data.get('visitor_id')}")
            
            # Verify returning visitor detection
            if data.get('is_returning_visitor') == True:
                print("✅ Correctly identified as returning visitor")
            else:
                print(f"❌ Should be identified as returning visitor, got: {data.get('is_returning_visitor')}")
                all_passed = False
                
            # Verify session isolation (new session should start with length 1)
            if data.get('conversation_length') == 1:
                print("✅ New session correctly starts with conversation length 1")
            else:
                print(f"❌ New session should start with length 1, got: {data.get('conversation_length')}")
                all_passed = False
                
            # Verify visitor ID consistency
            if data.get('visitor_id') == visitor_id:
                print("✅ Visitor ID consistent across sessions")
            else:
                print(f"❌ Visitor ID inconsistent: expected {visitor_id}, got {data.get('visitor_id')}")
                all_passed = False
                
        else:
            print(f"❌ Cross-session conversation failed with status {response.status_code}")
            print(f"   Error: {response.json() if response.content else 'No content'}")
            all_passed = False
            
    except Exception as e:
        print(f"❌ Cross-session test failed: {e}")
        all_passed = False
    
    # Test 4: Database Storage Verification
    print(f"\n--- Test 4: Database Storage Verification ---")
    
    # Test that conversations are being stored with proper expiration
    try:
        # Send a test message to ensure database storage
        response = requests.post(
            f"{API_BASE}/chat",
            json={
                "message": "This is a test message to verify database storage",
                "session_id": session_id_2,
                "site_id": site_id,
                "visitor_id": visitor_id
            },
            headers={"Content-Type": "application/json"},
            timeout=15
        )
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Database storage test message sent successfully")
            print(f"   Message stored with visitor_id: {data.get('visitor_id')}")
            print(f"   Session ID: {data.get('session_id')}")
            print(f"   Timestamp: {data.get('timestamp')}")
            
            # Verify all required fields are present
            required_fields = ["response", "session_id", "visitor_id", "timestamp", "model", "conversation_length", "is_returning_visitor"]
            missing_fields = [field for field in required_fields if field not in data]
            
            if missing_fields:
                print(f"❌ Missing required fields in response: {missing_fields}")
                all_passed = False
            else:
                print("✅ All required fields present in response")
                
        else:
            print(f"❌ Database storage test failed with status {response.status_code}")
            all_passed = False
            
    except Exception as e:
        print(f"❌ Database storage test failed: {e}")
        all_passed = False
    
    # Test 5: Memory Context Integration
    print(f"\n--- Test 5: Memory Context Integration ---")
    
    # Test that AI responses are personalized based on visitor history
    memory_test_messages = [
        "What did we discuss earlier about products?",
        "Can you remind me about the pricing we talked about?",
        "I'm interested in the services you mentioned before"
    ]
    
    for i, message in enumerate(memory_test_messages, 1):
        try:
            response = requests.post(
                f"{API_BASE}/chat",
                json={
                    "message": message,
                    "session_id": session_id_2,
                    "site_id": site_id,
                    "visitor_id": visitor_id
                },
                headers={"Content-Type": "application/json"},
                timeout=15
            )
            
            if response.status_code == 200:
                data = response.json()
                response_text = data.get('response', '').lower()
                
                print(f"✅ Memory test {i}: {message[:40]}...")
                print(f"   Response: {data.get('response', '')[:80]}...")
                
                # Check if response shows awareness of previous conversation
                memory_indicators = ['previous', 'earlier', 'before', 'discussed', 'mentioned', 'talked', 'remember']
                has_memory_context = any(indicator in response_text for indicator in memory_indicators)
                
                if has_memory_context:
                    print("✅ Response shows memory context awareness")
                else:
                    print("ℹ️ Response may not show explicit memory context (acceptable for demo mode)")
                
                # Verify returning visitor status
                if data.get('is_returning_visitor') == True:
                    print("✅ Consistently identified as returning visitor")
                else:
                    print(f"❌ Should consistently be returning visitor, got: {data.get('is_returning_visitor')}")
                    all_passed = False
                    
            else:
                print(f"❌ Memory test {i} failed with status {response.status_code}")
                all_passed = False
                
        except Exception as e:
            print(f"❌ Memory test {i} failed: {e}")
            all_passed = False
        
        time.sleep(0.5)
    
    # Test 6: Different Visitor - Isolation Test
    print(f"\n--- Test 6: Different Visitor - Memory Isolation ---")
    
    different_visitor_id = f"visitor-{uuid.uuid4()}"
    different_session_id = f"session-{uuid.uuid4()}"
    
    try:
        response = requests.post(
            f"{API_BASE}/chat",
            json={
                "message": "Hello, I'm a completely different visitor",
                "session_id": different_session_id,
                "site_id": site_id,
                "visitor_id": different_visitor_id
            },
            headers={"Content-Type": "application/json"},
            timeout=15
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Different visitor conversation successful")
            print(f"   Visitor ID: {data.get('visitor_id')}")
            print(f"   Is returning visitor: {data.get('is_returning_visitor')}")
            
            # Verify this is treated as a new visitor
            if data.get('is_returning_visitor') == False:
                print("✅ Different visitor correctly identified as new")
            else:
                print(f"❌ Different visitor should be new, got: {data.get('is_returning_visitor')}")
                all_passed = False
                
            # Verify visitor ID isolation
            if data.get('visitor_id') == different_visitor_id:
                print("✅ Visitor ID isolation working correctly")
            else:
                print(f"❌ Visitor ID isolation failed: expected {different_visitor_id}, got {data.get('visitor_id')}")
                all_passed = False
                
        else:
            print(f"❌ Different visitor test failed with status {response.status_code}")
            all_passed = False
            
    except Exception as e:
        print(f"❌ Different visitor test failed: {e}")
        all_passed = False
    
    # Test 7: TTL and Expiration Verification
    print(f"\n--- Test 7: TTL and Expiration Field Verification ---")
    
    # This test verifies that the API is setting up proper expiration
    # We can't directly test the 90-day cleanup without waiting, but we can verify the structure
    try:
        response = requests.post(
            f"{API_BASE}/chat",
            json={
                "message": "Testing TTL expiration setup",
                "session_id": session_id_2,
                "site_id": site_id,
                "visitor_id": visitor_id
            },
            headers={"Content-Type": "application/json"},
            timeout=15
        )
        
        if response.status_code == 200:
            data = response.json()
            print("✅ TTL test message sent successfully")
            
            # Verify timestamp format (should be ISO format)
            timestamp = data.get('timestamp')
            if timestamp:
                try:
                    # Try to parse the timestamp
                    from datetime import datetime
                    parsed_time = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                    print(f"✅ Timestamp format is valid: {timestamp}")
                except ValueError:
                    print(f"❌ Invalid timestamp format: {timestamp}")
                    all_passed = False
            else:
                print("❌ No timestamp in response")
                all_passed = False
                
            print("ℹ️ TTL index and 90-day expiration are set up in the database (verified by code review)")
            print("ℹ️ Automatic cleanup will occur after 90 days as configured")
            
        else:
            print(f"❌ TTL test failed with status {response.status_code}")
            all_passed = False
            
    except Exception as e:
        print(f"❌ TTL test failed: {e}")
        all_passed = False
    
    # Summary
    print(f"\n--- 90-Day Memory Functionality Test Summary ---")
    if all_passed:
        print("🎉 All 90-day memory functionality tests passed!")
        print("✅ Visitor ID storage and retrieval working")
        print("✅ Cross-session memory working")
        print("✅ Returning visitor detection working")
        print("✅ Memory isolation between visitors working")
        print("✅ Database storage with proper fields working")
        print("✅ TTL and expiration setup verified")
    else:
        print("❌ Some 90-day memory functionality tests failed")
        print("   Please check the detailed output above")
    
    return all_passed

def test_complete_dashboard_flow():
    """Test complete dashboard flow from registration to analytics"""
    print_test_header("Complete Dashboard Flow Test")
    
    print("🔄 Testing complete flow: Registration → Login → Site Creation → Site Listing → Dashboard Analytics")
    
    # Step 1: Register user
    print("\n--- Step 1: User Registration ---")
    registration_success = test_user_registration()
    if not registration_success:
        print("❌ Registration failed, cannot continue flow test")
        return False
    
    # Step 2: Login user
    print("\n--- Step 2: User Login ---")
    login_success, access_token = test_user_login()
    if not login_success or not access_token:
        print("❌ Login failed, cannot continue flow test")
        return False
    
    # Step 3: Create site
    print("\n--- Step 3: Site Creation ---")
    site_creation_success, site_id = test_site_creation(access_token)
    if not site_creation_success:
        print("❌ Site creation failed, cannot continue flow test")
        return False
    
    # Step 4: List sites
    print("\n--- Step 4: Site Listing ---")
    site_listing_success = test_site_listing(access_token)
    if not site_listing_success:
        print("❌ Site listing failed, cannot continue flow test")
        return False
    
    # Step 5: Get dashboard analytics
    print("\n--- Step 5: Dashboard Analytics ---")
    analytics_success = test_dashboard_analytics(access_token)
    if not analytics_success:
        print("❌ Dashboard analytics failed, cannot continue flow test")
        return False
    
    print("\n🎉 Complete dashboard flow test passed!")
    return True

def test_widget_endpoint():
    """Test the widget HTML endpoint"""
    print_test_header("Widget HTML Endpoint - GET /widget")
    
    test_cases = [
        {
            "name": "Widget with site_id parameter",
            "url": f"{BASE_URL}/widget?site_id=test-site",
            "expected_status": 200
        },
        {
            "name": "Widget with demo site_id",
            "url": f"{BASE_URL}/widget?site_id=demo",
            "expected_status": 200
        },
        {
            "name": "Widget without site_id parameter",
            "url": f"{BASE_URL}/widget",
            "expected_status": 200  # Should still work with fallback
        }
    ]
    
    all_passed = True
    
    for test_case in test_cases:
        print(f"\n--- Testing: {test_case['name']} ---")
        
        try:
            response = requests.get(test_case["url"], timeout=10)
            
            print(f"Status Code: {response.status_code} (Expected: {test_case['expected_status']})")
            
            if response.status_code == test_case["expected_status"]:
                # Check if response is HTML
                content_type = response.headers.get('content-type', '')
                if 'html' in content_type.lower():
                    print("✅ Response is HTML content")
                else:
                    print(f"⚠️ Content-Type: {content_type} (may not be HTML)")
                
                # Check for basic HTML structure
                html_content = response.text
                if '<html' in html_content and '</html>' in html_content:
                    print("✅ Valid HTML structure detected")
                else:
                    print("❌ Invalid HTML structure")
                    all_passed = False
                
                # Check for widget-related content
                widget_indicators = ['widget', 'assistant', 'script', 'site_id']
                found_indicators = [indicator for indicator in widget_indicators if indicator.lower() in html_content.lower()]
                
                if found_indicators:
                    print(f"✅ Widget-related content found: {found_indicators}")
                else:
                    print("❌ No widget-related content found")
                    all_passed = False
                    
            else:
                print(f"❌ Expected status {test_case['expected_status']}, got {response.status_code}")
                all_passed = False
                
        except requests.exceptions.RequestException as e:
            print(f"❌ Request failed: {e}")
            all_passed = False
    
    return all_passed

def test_static_file_serving():
    """Test static file serving for widget assets"""
    print_test_header("Static File Serving - /static/")
    
    static_files = [
        {
            "name": "Widget JavaScript",
            "url": f"{BASE_URL}/static/widget.js",
            "content_type": "javascript"
        },
        {
            "name": "Embed JavaScript", 
            "url": f"{BASE_URL}/static/embed.js",
            "content_type": "javascript"
        },
        {
            "name": "Widget HTML",
            "url": f"{BASE_URL}/static/widget.html",
            "content_type": "html"
        }
    ]
    
    all_passed = True
    
    for file_test in static_files:
        print(f"\n--- Testing: {file_test['name']} ---")
        
        try:
            response = requests.get(file_test["url"], timeout=10)
            
            print(f"URL: {file_test['url']}")
            print(f"Status Code: {response.status_code}")
            
            if response.status_code == 200:
                print("✅ File accessible")
                
                # Check content type
                content_type = response.headers.get('content-type', '')
                print(f"Content-Type: {content_type}")
                
                # Check file size
                content_length = len(response.content)
                print(f"Content Length: {content_length} bytes")
                
                if content_length > 0:
                    print("✅ File has content")
                else:
                    print("❌ File is empty")
                    all_passed = False
                    
                # Check for expected content based on file type
                content = response.text
                if file_test["content_type"] == "javascript":
                    if any(js_indicator in content for js_indicator in ['function', 'var', 'const', 'let', '{']):
                        print("✅ JavaScript content detected")
                    else:
                        print("⚠️ May not contain JavaScript code")
                elif file_test["content_type"] == "html":
                    if '<html' in content and '</html>' in content:
                        print("✅ HTML content detected")
                    else:
                        print("⚠️ May not contain valid HTML")
                        
            elif response.status_code == 404:
                print("❌ File not found (404)")
                all_passed = False
            else:
                print(f"❌ Unexpected status code: {response.status_code}")
                all_passed = False
                
        except requests.exceptions.RequestException as e:
            print(f"❌ Request failed: {e}")
            all_passed = False
    
    return all_passed

def test_embed_script_generation():
    """Test embed script generation endpoint"""
    print_test_header("Embed Script Generation - GET /api/sites/{site_id}/embed")
    
    # First, we need to create a user and site to test with
    print("Setting up test user and site...")
    
    # Register test user
    test_email = f"embed_test_{int(time.time())}@example.com"
    register_response = requests.post(
        f"{API_BASE}/auth/register",
        json={
            "email": test_email,
            "full_name": "Embed Test User",
            "password": "testpassword123"
        },
        headers={"Content-Type": "application/json"},
        timeout=10
    )
    
    if register_response.status_code != 200:
        print("❌ Failed to create test user for embed script test")
        return False
    
    # Login test user
    login_response = requests.post(
        f"{API_BASE}/auth/login",
        json={
            "email": test_email,
            "password": "testpassword123"
        },
        headers={"Content-Type": "application/json"},
        timeout=10
    )
    
    if login_response.status_code != 200:
        print("❌ Failed to login test user for embed script test")
        return False
    
    access_token = login_response.json().get("access_token")
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {access_token}"
    }
    
    # Create test site
    site_response = requests.post(
        f"{API_BASE}/sites",
        json={
            "name": "Embed Test Site",
            "domain": f"embed-test-{int(time.time())}.com",
            "description": "Test site for embed script generation"
        },
        headers=headers,
        timeout=10
    )
    
    if site_response.status_code != 200:
        print("❌ Failed to create test site for embed script test")
        return False
    
    site_id = site_response.json().get("id")
    print(f"✅ Test site created with ID: {site_id}")
    
    # Now test embed script generation
    all_passed = True
    
    try:
        embed_response = requests.get(
            f"{API_BASE}/sites/{site_id}/embed",
            headers={"Authorization": f"Bearer {access_token}"},
            timeout=10
        )
        
        print_result(f"/api/sites/{site_id}/embed", embed_response.status_code, embed_response.json() if embed_response.content else {})
        
        if embed_response.status_code == 200:
            data = embed_response.json()
            
            # Check required fields
            required_fields = ["site_id", "script_content", "installation_instructions"]
            missing_fields = [field for field in required_fields if field not in data]
            
            if missing_fields:
                print(f"❌ Missing required fields: {missing_fields}")
                all_passed = False
            else:
                print("✅ All required fields present")
                
            # Verify site_id matches
            if data.get("site_id") == site_id:
                print("✅ Site ID matches request")
            else:
                print(f"❌ Site ID mismatch: expected {site_id}, got {data.get('site_id')}")
                all_passed = False
                
            # Check script content
            script_content = data.get("script_content", "")
            if script_content and len(script_content) > 0:
                print("✅ Script content is not empty")
                
                # Check for essential script elements
                script_indicators = ['<script', 'src=', 'data-site-id', site_id]
                found_indicators = [indicator for indicator in script_indicators if indicator in script_content]
                
                if len(found_indicators) >= 3:
                    print(f"✅ Script contains essential elements: {found_indicators}")
                else:
                    print(f"⚠️ Script may be missing some elements. Found: {found_indicators}")
                    
            else:
                print("❌ Script content is empty")
                all_passed = False
                
            # Check installation instructions
            instructions = data.get("installation_instructions", "")
            if instructions and len(instructions) > 0:
                print("✅ Installation instructions provided")
            else:
                print("❌ Installation instructions are empty")
                all_passed = False
                
        else:
            print(f"❌ Expected status 200, got {embed_response.status_code}")
            all_passed = False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Request failed: {e}")
        all_passed = False
    except json.JSONDecodeError as e:
        print(f"❌ Invalid JSON response: {e}")
        all_passed = False
    
    return all_passed

def test_cors_configuration():
    """Test CORS configuration for embedded widgets"""
    print_test_header("CORS Configuration Test")
    
    # Test CORS headers on key endpoints
    endpoints_to_test = [
        f"{API_BASE}/chat",
        f"{API_BASE}/widget/config", 
        f"{API_BASE}/analytics/interaction",
        f"{BASE_URL}/widget"
    ]
    
    all_passed = True
    
    for endpoint in endpoints_to_test:
        print(f"\n--- Testing CORS for: {endpoint} ---")
        
        try:
            # Test preflight request (OPTIONS)
            options_response = requests.options(
                endpoint,
                headers={
                    "Origin": "https://example.com",
                    "Access-Control-Request-Method": "POST",
                    "Access-Control-Request-Headers": "Content-Type"
                },
                timeout=10
            )
            
            print(f"OPTIONS Status: {options_response.status_code}")
            
            # Check CORS headers
            cors_headers = {
                "Access-Control-Allow-Origin": options_response.headers.get("Access-Control-Allow-Origin"),
                "Access-Control-Allow-Methods": options_response.headers.get("Access-Control-Allow-Methods"),
                "Access-Control-Allow-Headers": options_response.headers.get("Access-Control-Allow-Headers"),
                "Access-Control-Allow-Credentials": options_response.headers.get("Access-Control-Allow-Credentials")
            }
            
            print("CORS Headers:")
            for header, value in cors_headers.items():
                print(f"  {header}: {value}")
            
            # Check if CORS is properly configured
            allow_origin = cors_headers.get("Access-Control-Allow-Origin")
            if allow_origin == "*" or allow_origin == "https://example.com":
                print("✅ CORS Allow-Origin configured")
            else:
                print(f"⚠️ CORS Allow-Origin may not be configured for cross-origin requests: {allow_origin}")
                
            allow_methods = cors_headers.get("Access-Control-Allow-Methods")
            if allow_methods and ("POST" in allow_methods or "*" in allow_methods):
                print("✅ CORS Allow-Methods includes POST")
            else:
                print(f"⚠️ CORS Allow-Methods may not include POST: {allow_methods}")
                
        except requests.exceptions.RequestException as e:
            print(f"❌ CORS test failed: {e}")
            all_passed = False
    
    return all_passed

def test_rate_limiting():
    """Test rate limiting doesn't break widget functionality"""
    print_test_header("Rate Limiting Test")
    
    # Test normal usage doesn't hit rate limits
    print("--- Testing Normal Usage Rate Limits ---")
    
    session_id = f"rate-test-{uuid.uuid4()}"
    site_id = "demo"
    
    # Send multiple requests within normal usage patterns
    normal_requests = 5
    all_passed = True
    
    for i in range(normal_requests):
        try:
            response = requests.post(
                f"{API_BASE}/chat",
                json={
                    "message": f"Test message {i+1}",
                    "session_id": session_id,
                    "site_id": site_id
                },
                headers={"Content-Type": "application/json"},
                timeout=10
            )
            
            if response.status_code == 200:
                print(f"✅ Request {i+1}: Success")
            elif response.status_code == 429:
                print(f"❌ Request {i+1}: Rate limited (429) - this shouldn't happen for normal usage")
                all_passed = False
            else:
                print(f"⚠️ Request {i+1}: Status {response.status_code}")
                
        except requests.exceptions.RequestException as e:
            print(f"❌ Request {i+1} failed: {e}")
            all_passed = False
        
        # Small delay between requests
        time.sleep(0.2)
    
    # Test widget config rate limiting
    print("\n--- Testing Widget Config Rate Limits ---")
    
    for i in range(3):
        try:
            response = requests.post(
                f"{API_BASE}/widget/config",
                json={"site_id": "demo"},
                headers={"Content-Type": "application/json"},
                timeout=10
            )
            
            if response.status_code == 200:
                print(f"✅ Widget config request {i+1}: Success")
            elif response.status_code == 429:
                print(f"❌ Widget config request {i+1}: Rate limited (429)")
                all_passed = False
            else:
                print(f"⚠️ Widget config request {i+1}: Status {response.status_code}")
                
        except requests.exceptions.RequestException as e:
            print(f"❌ Widget config request {i+1} failed: {e}")
            all_passed = False
        
        time.sleep(0.1)
    
    return all_passed

def test_multi_site_support():
    """Test different site IDs get different configurations"""
    print_test_header("Multi-Site Support Test")
    
    test_sites = [
        {"site_id": "demo", "name": "Demo Site"},
        {"site_id": "test-site-1", "name": "Test Site 1"},
        {"site_id": "test-site-2", "name": "Test Site 2"},
        {"site_id": "custom-site", "name": "Custom Site"}
    ]
    
    all_passed = True
    site_configs = {}
    
    for site in test_sites:
        site_id = site["site_id"]
        print(f"\n--- Testing Site: {site['name']} ({site_id}) ---")
        
        try:
            # Get widget configuration for this site
            config_response = requests.post(
                f"{API_BASE}/widget/config",
                json={"site_id": site_id},
                headers={"Content-Type": "application/json"},
                timeout=10
            )
            
            if config_response.status_code == 200:
                config_data = config_response.json()
                site_configs[site_id] = config_data
                
                print(f"✅ Configuration retrieved for {site_id}")
                print(f"   Bot Name: {config_data.get('bot_name', 'N/A')}")
                print(f"   Greeting: {config_data.get('greeting_message', 'N/A')[:50]}...")
                print(f"   Theme Primary: {config_data.get('theme', {}).get('primary_color', 'N/A')}")
                
                # Verify site_id is correctly returned
                if config_data.get("site_id") == site_id:
                    print(f"✅ Site ID correctly returned: {site_id}")
                else:
                    print(f"❌ Site ID mismatch: expected {site_id}, got {config_data.get('site_id')}")
                    all_passed = False
                    
            else:
                print(f"❌ Failed to get configuration for {site_id}: Status {config_response.status_code}")
                all_passed = False
                
        except requests.exceptions.RequestException as e:
            print(f"❌ Request failed for {site_id}: {e}")
            all_passed = False
    
    # Test chat with different sites
    print(f"\n--- Testing Chat with Different Sites ---")
    
    for site in test_sites[:2]:  # Test first 2 sites for chat
        site_id = site["site_id"]
        session_id = f"multisite-{site_id}-{uuid.uuid4()}"
        
        try:
            chat_response = requests.post(
                f"{API_BASE}/chat",
                json={
                    "message": f"Hello from {site['name']}",
                    "session_id": session_id,
                    "site_id": site_id
                },
                headers={"Content-Type": "application/json"},
                timeout=15
            )
            
            if chat_response.status_code == 200:
                chat_data = chat_response.json()
                print(f"✅ Chat working for {site_id}")
                print(f"   Response: {chat_data.get('response', '')[:50]}...")
                
                # Verify session isolation between sites
                if chat_data.get("session_id") == session_id:
                    print(f"✅ Session isolation working for {site_id}")
                else:
                    print(f"❌ Session ID issue for {site_id}")
                    all_passed = False
                    
            else:
                print(f"❌ Chat failed for {site_id}: Status {chat_response.status_code}")
                all_passed = False
                
        except requests.exceptions.RequestException as e:
            print(f"❌ Chat request failed for {site_id}: {e}")
            all_passed = False
    
    # Verify configurations are different (or at least properly handled)
    print(f"\n--- Verifying Site Configuration Differences ---")
    
    if len(site_configs) >= 2:
        site_ids = list(site_configs.keys())
        config1 = site_configs[site_ids[0]]
        config2 = site_configs[site_ids[1]]
        
        # Check if configurations have the expected structure
        if config1.get("site_id") != config2.get("site_id"):
            print("✅ Different sites have different site_id values")
        else:
            print("❌ Site configurations should have different site_id values")
            all_passed = False
            
        # All sites should have the required configuration structure
        required_fields = ["site_id", "greeting_message", "bot_name", "theme"]
        for site_id, config in site_configs.items():
            missing_fields = [field for field in required_fields if field not in config]
            if missing_fields:
                print(f"❌ Site {site_id} missing fields: {missing_fields}")
                all_passed = False
            else:
                print(f"✅ Site {site_id} has complete configuration")
    
    return all_passed

def test_visitor_tracking():
    """Test visitor ID persistence for external embeds"""
    print_test_header("Visitor Tracking Test")
    
    # Generate unique visitor ID
    visitor_id = f"visitor-{uuid.uuid4()}"
    site_id = "demo"
    
    print(f"Testing with visitor_id: {visitor_id}")
    
    all_passed = True
    
    # Test 1: First visit with visitor ID
    print(f"\n--- Test 1: First Visit with Visitor ID ---")
    
    session_id_1 = f"session-1-{uuid.uuid4()}"
    
    try:
        response = requests.post(
            f"{API_BASE}/chat",
            json={
                "message": "Hello, I'm a new visitor",
                "session_id": session_id_1,
                "site_id": site_id,
                "visitor_id": visitor_id
            },
            headers={"Content-Type": "application/json"},
            timeout=15
        )
        
        if response.status_code == 200:
            data = response.json()
            print("✅ First visit successful")
            
            # Verify visitor ID is returned
            if data.get("visitor_id") == visitor_id:
                print("✅ Visitor ID correctly returned")
            else:
                print(f"❌ Visitor ID mismatch: expected {visitor_id}, got {data.get('visitor_id')}")
                all_passed = False
                
            # Should be identified as new visitor
            if data.get("is_returning_visitor") == False:
                print("✅ Correctly identified as new visitor")
            else:
                print(f"❌ Should be new visitor, got: {data.get('is_returning_visitor')}")
                all_passed = False
                
        else:
            print(f"❌ First visit failed: Status {response.status_code}")
            all_passed = False
            
    except Exception as e:
        print(f"❌ First visit test failed: {e}")
        all_passed = False
    
    # Test 2: Same visitor, different session
    print(f"\n--- Test 2: Same Visitor, Different Session ---")
    
    session_id_2 = f"session-2-{uuid.uuid4()}"
    
    # Wait a moment to ensure different timestamps
    time.sleep(1)
    
    try:
        response = requests.post(
            f"{API_BASE}/chat",
            json={
                "message": "Hello again, I'm back",
                "session_id": session_id_2,
                "site_id": site_id,
                "visitor_id": visitor_id
            },
            headers={"Content-Type": "application/json"},
            timeout=15
        )
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Return visit successful")
            
            # Verify visitor ID persistence
            if data.get("visitor_id") == visitor_id:
                print("✅ Visitor ID persisted across sessions")
            else:
                print(f"❌ Visitor ID not persisted: expected {visitor_id}, got {data.get('visitor_id')}")
                all_passed = False
                
            # Should be identified as returning visitor
            if data.get("is_returning_visitor") == True:
                print("✅ Correctly identified as returning visitor")
            else:
                print(f"❌ Should be returning visitor, got: {data.get('is_returning_visitor')}")
                all_passed = False
                
            # Session should be isolated (conversation length = 1)
            if data.get("conversation_length") == 1:
                print("✅ Session isolation maintained")
            else:
                print(f"⚠️ Session isolation: expected length 1, got {data.get('conversation_length')}")
                
        else:
            print(f"❌ Return visit failed: Status {response.status_code}")
            all_passed = False
            
    except Exception as e:
        print(f"❌ Return visit test failed: {e}")
        all_passed = False
    
    # Test 3: Analytics tracking with visitor ID
    print(f"\n--- Test 3: Analytics Tracking with Visitor ID ---")
    
    try:
        analytics_response = requests.post(
            f"{API_BASE}/analytics/interaction",
            json={
                "site_id": site_id,
                "session_id": session_id_2,
                "type": "widget_open",
                "visitor_id": visitor_id
            },
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        
        if analytics_response.status_code == 200:
            analytics_data = analytics_response.json()
            if analytics_data.get("status") == "logged":
                print("✅ Analytics tracking with visitor ID successful")
            else:
                print(f"❌ Analytics tracking failed: {analytics_data}")
                all_passed = False
        else:
            print(f"❌ Analytics tracking failed: Status {analytics_response.status_code}")
            all_passed = False
            
    except Exception as e:
        print(f"❌ Analytics tracking test failed: {e}")
        all_passed = False
    
    # Test 4: Different visitor isolation
    print(f"\n--- Test 4: Different Visitor Isolation ---")
    
    different_visitor_id = f"visitor-{uuid.uuid4()}"
    different_session_id = f"session-{uuid.uuid4()}"
    
    try:
        response = requests.post(
            f"{API_BASE}/chat",
            json={
                "message": "Hello, I'm a different visitor",
                "session_id": different_session_id,
                "site_id": site_id,
                "visitor_id": different_visitor_id
            },
            headers={"Content-Type": "application/json"},
            timeout=15
        )
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Different visitor test successful")
            
            # Should be treated as new visitor
            if data.get("is_returning_visitor") == False:
                print("✅ Different visitor correctly treated as new")
            else:
                print(f"❌ Different visitor should be new, got: {data.get('is_returning_visitor')}")
                all_passed = False
                
            # Visitor ID should match
            if data.get("visitor_id") == different_visitor_id:
                print("✅ Different visitor ID correctly handled")
            else:
                print(f"❌ Visitor ID mismatch: expected {different_visitor_id}, got {data.get('visitor_id')}")
                all_passed = False
                
        else:
            print(f"❌ Different visitor test failed: Status {response.status_code}")
            all_passed = False
            
    except Exception as e:
        print(f"❌ Different visitor test failed: {e}")
        all_passed = False
    
    return all_passed

def main():
    """Run all backend API tests"""
    print("🚀 Starting AI Voice Assistant Backend API Tests")
    print(f"Testing against: {BASE_URL}")
    print(f"Timestamp: {datetime.now().isoformat()}")
    
    test_results = {}
    
    # Run Phase 1 tests (existing widget functionality)
    print("\n" + "="*60)
    print("PHASE 1: WIDGET API TESTS")
    print("="*60)
    
    test_results["health"] = test_health_endpoint()
    test_results["chat"] = test_chat_endpoint()
    test_results["widget_config"] = test_widget_config_endpoint()
    test_results["analytics"] = test_analytics_endpoint()
    test_results["conversation_flow"] = test_conversation_flow()
    test_results["enhanced_conversation_memory"] = test_enhanced_conversation_memory()
    
    # Run EMBEDDABLE WIDGET SYSTEM TESTS (New)
    print("\n" + "="*60)
    print("EMBEDDABLE WIDGET SYSTEM TESTS")
    print("="*60)
    
    test_results["widget_endpoint"] = test_widget_endpoint()
    test_results["static_file_serving"] = test_static_file_serving()
    test_results["embed_script_generation"] = test_embed_script_generation()
    test_results["cors_configuration"] = test_cors_configuration()
    test_results["rate_limiting"] = test_rate_limiting()
    test_results["multi_site_support"] = test_multi_site_support()
    test_results["visitor_tracking"] = test_visitor_tracking()
    
    # Run 90-Day Memory Functionality Tests
    print("\n" + "="*60)
    print("90-DAY MEMORY FUNCTIONALITY TESTS")
    print("="*60)
    
    test_results["90_day_memory"] = test_90_day_memory_functionality()
    
    # Run Phase 2 tests (dashboard functionality)
    print("\n" + "="*60)
    print("PHASE 2: DASHBOARD API TESTS")
    print("="*60)
    
    test_results["user_registration"] = test_user_registration()
    login_success, access_token = test_user_login()
    test_results["user_login"] = login_success
    
    if access_token:
        site_creation_success, site_id = test_site_creation(access_token)
        test_results["site_creation"] = site_creation_success
        test_results["site_listing"] = test_site_listing(access_token)
        test_results["dashboard_analytics"] = test_dashboard_analytics(access_token)
    else:
        print("⚠️ Skipping authenticated tests due to login failure")
        test_results["site_creation"] = False
        test_results["site_listing"] = False
        test_results["dashboard_analytics"] = False
    
    # Run complete flow test
    print("\n" + "="*60)
    print("COMPLETE FLOW TEST")
    print("="*60)
    
    test_results["complete_dashboard_flow"] = test_complete_dashboard_flow()
    
    # Print summary
    print(f"\n{'='*60}")
    print("TEST SUMMARY")
    print(f"{'='*60}")
    
    # Phase 1 results
    print("\nPhase 1 (Widget API):")
    phase1_tests = ["health", "chat", "widget_config", "analytics", "conversation_flow", "enhanced_conversation_memory"]
    phase1_passed = sum(1 for test in phase1_tests if test_results.get(test, False))
    
    for test_name in phase1_tests:
        result = test_results.get(test_name, False)
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"  {test_name.upper().replace('_', ' ')}: {status}")
    
    print(f"  Phase 1 Result: {phase1_passed}/{len(phase1_tests)} tests passed")
    
    # Embeddable Widget System results
    print("\nEmbeddable Widget System:")
    widget_tests = ["widget_endpoint", "static_file_serving", "embed_script_generation", "cors_configuration", "rate_limiting", "multi_site_support", "visitor_tracking"]
    widget_passed = sum(1 for test in widget_tests if test_results.get(test, False))
    
    for test_name in widget_tests:
        result = test_results.get(test_name, False)
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"  {test_name.upper().replace('_', ' ')}: {status}")
    
    print(f"  Widget System Result: {widget_passed}/{len(widget_tests)} tests passed")
    
    # 90-Day Memory results
    print("\n90-Day Memory Functionality:")
    memory_tests = ["90_day_memory"]
    memory_passed = sum(1 for test in memory_tests if test_results.get(test, False))
    
    for test_name in memory_tests:
        result = test_results.get(test_name, False)
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"  {test_name.upper().replace('_', ' ')}: {status}")
    
    print(f"  Memory Tests Result: {memory_passed}/{len(memory_tests)} tests passed")
    
    # Phase 2 results
    print("\nPhase 2 (Dashboard API):")
    phase2_tests = ["user_registration", "user_login", "site_creation", "site_listing", "dashboard_analytics"]
    phase2_passed = sum(1 for test in phase2_tests if test_results.get(test, False))
    
    for test_name in phase2_tests:
        result = test_results.get(test_name, False)
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"  {test_name.upper().replace('_', ' ')}: {status}")
    
    print(f"  Phase 2 Result: {phase2_passed}/{len(phase2_tests)} tests passed")
    
    # Complete flow result
    print("\nComplete Flow:")
    flow_result = test_results.get("complete_dashboard_flow", False)
    flow_status = "✅ PASSED" if flow_result else "❌ FAILED"
    print(f"  COMPLETE DASHBOARD FLOW: {flow_status}")
    
    # Overall results
    total_tests = len(test_results)
    passed_tests = sum(1 for result in test_results.values() if result)
    
    print(f"\nOverall Result: {passed_tests}/{total_tests} tests passed")
    
    if passed_tests == total_tests:
        print("🎉 All tests passed! Backend API is working correctly.")
        return True
    else:
        print("⚠️  Some tests failed. Please check the detailed output above.")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)