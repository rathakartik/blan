#!/usr/bin/env python3
"""
Focused test for Core AI Chat Functionality
Tests the specific endpoints mentioned in the review request
"""

import requests
import json
import uuid
from datetime import datetime

# Configuration
BASE_URL = "https://5f968ed4-0598-44bb-9e69-5064cb737711.preview.emergentagent.com"
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

def test_chat_endpoint_detailed():
    """Detailed test of the chat endpoint"""
    print_test_header("Core AI Chat Endpoint - POST /api/chat")
    
    issues = []
    
    # Test 1: Valid chat with demo mode
    print("\n--- Test 1: Valid Chat Message ---")
    try:
        response = requests.post(
            f"{API_BASE}/chat",
            json={
                "message": "Hello, how are you?",
                "session_id": "test-session-123",
                "site_id": "demo"
            },
            headers={"Content-Type": "application/json"},
            timeout=15
        )
        
        data = response.json()
        print_result("/api/chat", response.status_code, data)
        
        if response.status_code == 200:
            # Check if GROQ is working or falling back to demo
            model_used = data.get("model", "unknown")
            if model_used == "demo_fallback":
                issues.append("GROQ API is failing, falling back to demo mode")
                print("⚠️ GROQ API is not working, using demo fallback")
            elif model_used == "llama3-8b-8192":
                print("✅ GROQ API is working correctly")
            else:
                print(f"ℹ️ Using model: {model_used}")
                
            # Check response structure
            required_fields = ["response", "session_id", "timestamp", "model"]
            missing_fields = [field for field in required_fields if field not in data]
            if missing_fields:
                issues.append(f"Missing required fields in chat response: {missing_fields}")
            else:
                print("✅ All required fields present in response")
        else:
            issues.append(f"Chat endpoint returned {response.status_code} instead of 200")
            
    except Exception as e:
        issues.append(f"Chat endpoint request failed: {e}")
        print(f"❌ Request failed: {e}")
    
    # Test 2: Error handling - missing message
    print("\n--- Test 2: Missing Message Error Handling ---")
    try:
        response = requests.post(
            f"{API_BASE}/chat",
            json={"site_id": "demo"},
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        
        print_result("/api/chat (missing message)", response.status_code, response.json() if response.content else {}, expected_status=400)
        
        if response.status_code != 400:
            issues.append(f"Chat endpoint should return 400 for missing message, got {response.status_code}")
            print("❌ Error handling issue: should return 400 for missing message")
        else:
            print("✅ Proper error handling for missing message")
            
    except Exception as e:
        issues.append(f"Error testing missing message: {e}")
        print(f"❌ Error testing missing message: {e}")
    
    # Test 3: Session management
    print("\n--- Test 3: Session Management ---")
    session_id = str(uuid.uuid4())
    try:
        # Send multiple messages with same session
        for i in range(3):
            response = requests.post(
                f"{API_BASE}/chat",
                json={
                    "message": f"Message {i+1} in conversation",
                    "session_id": session_id,
                    "site_id": "demo"
                },
                headers={"Content-Type": "application/json"},
                timeout=15
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get("session_id") == session_id:
                    print(f"✅ Message {i+1}: Session ID consistent")
                else:
                    issues.append(f"Session ID inconsistency in message {i+1}")
                    print(f"❌ Message {i+1}: Session ID mismatch")
            else:
                issues.append(f"Message {i+1} failed with status {response.status_code}")
                print(f"❌ Message {i+1} failed")
                
    except Exception as e:
        issues.append(f"Session management test failed: {e}")
        print(f"❌ Session management test failed: {e}")
    
    return len(issues) == 0, issues

def test_widget_config_detailed():
    """Detailed test of the widget config endpoint"""
    print_test_header("Widget Configuration - POST /api/widget/config")
    
    issues = []
    
    # Test 1: Demo site config
    print("\n--- Test 1: Demo Site Configuration ---")
    try:
        response = requests.post(
            f"{API_BASE}/widget/config",
            json={"site_id": "demo"},
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        
        print_result("/api/widget/config", response.status_code, response.json() if response.content else {})
        
        if response.status_code == 200:
            data = response.json()
            required_fields = ["site_id", "greeting_message", "bot_name", "theme", "position", "auto_greet", "voice_enabled", "language"]
            missing_fields = [field for field in required_fields if field not in data]
            
            if missing_fields:
                issues.append(f"Missing required fields in widget config: {missing_fields}")
                print(f"❌ Missing required fields: {missing_fields}")
            else:
                print("✅ All required fields present")
                
            # Check theme structure
            if "theme" in data and isinstance(data["theme"], dict):
                theme_fields = ["primary_color", "secondary_color", "text_color", "background_color"]
                missing_theme_fields = [field for field in theme_fields if field not in data["theme"]]
                
                if missing_theme_fields:
                    issues.append(f"Missing theme fields: {missing_theme_fields}")
                    print(f"❌ Missing theme fields: {missing_theme_fields}")
                else:
                    print("✅ Theme structure is complete")
            else:
                issues.append("Theme is missing or not a dict")
                print("❌ Theme is missing or not a dict")
                
        elif response.status_code == 404:
            # Check if it's using fallback config
            data = response.json()
            if "Site not found" in data.get("detail", ""):
                issues.append("Widget config endpoint not returning fallback config for demo site")
                print("❌ Should return fallback config for demo site, not 404")
            
        else:
            issues.append(f"Widget config returned unexpected status: {response.status_code}")
            
    except Exception as e:
        issues.append(f"Widget config test failed: {e}")
        print(f"❌ Request failed: {e}")
    
    # Test 2: Error handling - missing site_id
    print("\n--- Test 2: Missing Site ID Error Handling ---")
    try:
        response = requests.post(
            f"{API_BASE}/widget/config",
            json={},
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        
        print_result("/api/widget/config (missing site_id)", response.status_code, response.json() if response.content else {}, expected_status=400)
        
        if response.status_code == 400:
            print("✅ Proper error handling for missing site_id")
        else:
            issues.append(f"Should return 400 for missing site_id, got {response.status_code}")
            print("❌ Error handling issue")
            
    except Exception as e:
        issues.append(f"Error testing missing site_id: {e}")
        print(f"❌ Error testing missing site_id: {e}")
    
    return len(issues) == 0, issues

def test_analytics_detailed():
    """Detailed test of the analytics endpoint"""
    print_test_header("Analytics Logging - POST /api/analytics/interaction")
    
    issues = []
    
    # Test various interaction types
    test_cases = [
        {
            "name": "Widget Open",
            "payload": {
                "site_id": "demo",
                "session_id": f"test-session-{uuid.uuid4()}",
                "type": "widget_open"
            }
        },
        {
            "name": "Chat Message",
            "payload": {
                "site_id": "demo",
                "session_id": f"test-session-{uuid.uuid4()}",
                "type": "chat_message",
                "user_message": "Hello there!",
                "ai_response": "Hi! How can I help you?"
            }
        },
        {
            "name": "Voice Input",
            "payload": {
                "site_id": "demo",
                "session_id": f"test-session-{uuid.uuid4()}",
                "type": "voice_input"
            }
        }
    ]
    
    for test_case in test_cases:
        print(f"\n--- Testing: {test_case['name']} ---")
        
        try:
            response = requests.post(
                f"{API_BASE}/analytics/interaction",
                json=test_case["payload"],
                headers={"Content-Type": "application/json"},
                timeout=10
            )
            
            print_result("/api/analytics/interaction", response.status_code, response.json() if response.content else {})
            
            if response.status_code == 200:
                data = response.json()
                if data.get("status") == "logged":
                    print("✅ Interaction logged successfully")
                else:
                    issues.append(f"Unexpected response for {test_case['name']}: {data}")
                    print(f"❌ Unexpected response: {data}")
            else:
                issues.append(f"Analytics logging failed for {test_case['name']}: {response.status_code}")
                print(f"❌ Failed with status {response.status_code}")
                
        except Exception as e:
            issues.append(f"Analytics test failed for {test_case['name']}: {e}")
            print(f"❌ Request failed: {e}")
    
    return len(issues) == 0, issues

def test_conversation_logging():
    """Test if conversations are being logged properly"""
    print_test_header("Conversation Logging Test")
    
    issues = []
    session_id = f"logging-test-{uuid.uuid4()}"
    
    # Send a chat message and check if it gets logged
    print("\n--- Testing Conversation Logging ---")
    try:
        # Send chat message
        chat_response = requests.post(
            f"{API_BASE}/chat",
            json={
                "message": "Test message for logging",
                "session_id": session_id,
                "site_id": "demo"
            },
            headers={"Content-Type": "application/json"},
            timeout=15
        )
        
        if chat_response.status_code == 200:
            print("✅ Chat message sent successfully")
            
            # Log analytics interaction
            analytics_response = requests.post(
                f"{API_BASE}/analytics/interaction",
                json={
                    "site_id": "demo",
                    "session_id": session_id,
                    "type": "chat_message",
                    "user_message": "Test message for logging",
                    "ai_response": chat_response.json().get("response")
                },
                headers={"Content-Type": "application/json"},
                timeout=10
            )
            
            if analytics_response.status_code == 200:
                print("✅ Analytics interaction logged successfully")
            else:
                issues.append(f"Analytics logging failed: {analytics_response.status_code}")
                print("❌ Analytics logging failed")
        else:
            issues.append(f"Chat message failed: {chat_response.status_code}")
            print("❌ Chat message failed")
            
    except Exception as e:
        issues.append(f"Conversation logging test failed: {e}")
        print(f"❌ Test failed: {e}")
    
    return len(issues) == 0, issues

def main():
    """Run focused tests for core AI chat functionality"""
    print("🚀 Starting Core AI Chat Functionality Tests")
    print(f"Testing against: {BASE_URL}")
    print(f"Timestamp: {datetime.now().isoformat()}")
    
    all_issues = []
    test_results = {}
    
    # Test 1: Chat Endpoint
    chat_success, chat_issues = test_chat_endpoint_detailed()
    test_results["chat_endpoint"] = chat_success
    all_issues.extend(chat_issues)
    
    # Test 2: Widget Config
    config_success, config_issues = test_widget_config_detailed()
    test_results["widget_config"] = config_success
    all_issues.extend(config_issues)
    
    # Test 3: Analytics
    analytics_success, analytics_issues = test_analytics_detailed()
    test_results["analytics"] = analytics_success
    all_issues.extend(analytics_issues)
    
    # Test 4: Conversation Logging
    logging_success, logging_issues = test_conversation_logging()
    test_results["conversation_logging"] = logging_success
    all_issues.extend(logging_issues)
    
    # Print summary
    print(f"\n{'='*60}")
    print("CORE AI CHAT FUNCTIONALITY TEST SUMMARY")
    print(f"{'='*60}")
    
    for test_name, success in test_results.items():
        status = "✅ PASSED" if success else "❌ FAILED"
        print(f"  {test_name.upper().replace('_', ' ')}: {status}")
    
    passed_tests = sum(1 for result in test_results.values() if result)
    total_tests = len(test_results)
    
    print(f"\nOverall Result: {passed_tests}/{total_tests} tests passed")
    
    if all_issues:
        print(f"\n{'='*60}")
        print("IDENTIFIED ISSUES")
        print(f"{'='*60}")
        for i, issue in enumerate(all_issues, 1):
            print(f"{i}. {issue}")
    
    if passed_tests == total_tests:
        print("\n🎉 All core AI chat functionality tests passed!")
        return True
    else:
        print(f"\n⚠️ {len(all_issues)} issues found in core AI chat functionality.")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)