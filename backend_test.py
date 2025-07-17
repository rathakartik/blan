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
BASE_URL = "https://50aee594-9836-4d30-87f5-ed69160b25dd.preview.emergentagent.com"  # Using the backend URL from frontend/.env
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
                "email": "test@example.com",
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
                "password": "securepassword123"
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
                "domain": "test-website.com",
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
    phase1_tests = ["health", "chat", "widget_config", "analytics", "conversation_flow"]
    phase1_passed = sum(1 for test in phase1_tests if test_results.get(test, False))
    
    for test_name in phase1_tests:
        result = test_results.get(test_name, False)
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"  {test_name.upper().replace('_', ' ')}: {status}")
    
    print(f"  Phase 1 Result: {phase1_passed}/{len(phase1_tests)} tests passed")
    
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