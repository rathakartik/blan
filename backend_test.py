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
BASE_URL = "http://localhost:8001"  # Using the backend URL from frontend/.env
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

def main():
    """Run all backend API tests"""
    print("🚀 Starting AI Voice Assistant Backend API Tests")
    print(f"Testing against: {BASE_URL}")
    print(f"Timestamp: {datetime.now().isoformat()}")
    
    test_results = {}
    
    # Run individual endpoint tests
    test_results["health"] = test_health_endpoint()
    test_results["chat"] = test_chat_endpoint()
    test_results["widget_config"] = test_widget_config_endpoint()
    test_results["analytics"] = test_analytics_endpoint()
    test_results["conversation_flow"] = test_conversation_flow()
    
    # Print summary
    print(f"\n{'='*60}")
    print("TEST SUMMARY")
    print(f"{'='*60}")
    
    total_tests = len(test_results)
    passed_tests = sum(1 for result in test_results.values() if result)
    
    for test_name, result in test_results.items():
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{test_name.upper().replace('_', ' ')}: {status}")
    
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