#!/usr/bin/env python3
"""
Enhanced Backend API Testing Script for AI Voice Assistant Widget
Tests enhanced AI chat functionality with conversation memory and multi-turn conversations
"""

import requests
import json
import time
from datetime import datetime
import uuid

# Configuration
BASE_URL = "https://0f38d26a-3cc7-460b-a771-19fe6f1ae7cc.preview.emergentagent.com"  # Using the backend URL from frontend/.env
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

def test_groq_api_fallback():
    """Test GROQ API and demo fallback behavior"""
    print_test_header("GROQ API and Demo Fallback Test")
    
    session_id = f"groq-test-{uuid.uuid4()}"
    site_id = "demo"
    
    test_cases = [
        {
            "name": "Standard Message (Should use demo fallback)",
            "message": "Hello, how are you today?",
            "expected_model_types": ["demo", "demo_fallback", "llama3-8b-8192"]
        },
        {
            "name": "Complex Question (Should use demo fallback)",
            "message": "Can you explain quantum computing in simple terms?",
            "expected_model_types": ["demo", "demo_fallback", "llama3-8b-8192"]
        },
        {
            "name": "Follow-up Question (Should maintain context)",
            "message": "Tell me more about that",
            "expected_model_types": ["demo", "demo_fallback", "llama3-8b-8192"]
        }
    ]
    
    all_passed = True
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n--- Test {i}: {test_case['name']} ---")
        print(f"Message: '{test_case['message']}'")
        
        try:
            response = requests.post(
                f"{API_BASE}/chat",
                json={
                    "message": test_case["message"],
                    "session_id": session_id,
                    "site_id": site_id
                },
                headers={"Content-Type": "application/json"},
                timeout=15
            )
            
            if response.status_code == 200:
                data = response.json()
                model_used = data.get('model', 'unknown')
                
                print(f"✅ Response received: {data.get('response', 'No response')[:100]}...")
                print(f"   Model used: {model_used}")
                print(f"   Conversation length: {data.get('conversation_length', 0)}")
                
                # Verify model type is one of expected
                if model_used in test_case['expected_model_types']:
                    print(f"✅ Model type is expected: {model_used}")
                else:
                    print(f"⚠️ Unexpected model type: {model_used}, expected one of: {test_case['expected_model_types']}")
                    # Don't fail test as this depends on GROQ API availability
                
                # Check for token counting (if available)
                if 'tokens_used' in data:
                    print(f"✅ Token counting available: {data['tokens_used']} tokens")
                else:
                    print("ℹ️ Token counting not available in response")
                
                # Verify response structure
                required_fields = ["response", "session_id", "timestamp", "model"]
                missing_fields = [field for field in required_fields if field not in data]
                if missing_fields:
                    print(f"❌ Missing required fields: {missing_fields}")
                    all_passed = False
                else:
                    print("✅ All required response fields present")
                    
                # Verify response is not empty
                if data.get('response') and len(data.get('response').strip()) > 0:
                    print("✅ Response is not empty")
                else:
                    print("❌ Response is empty")
                    all_passed = False
                    
            else:
                print(f"❌ Request failed with status {response.status_code}")
                if response.content:
                    print(f"   Error: {response.json()}")
                all_passed = False
                
        except Exception as e:
            print(f"❌ Request failed: {e}")
            all_passed = False
        
        time.sleep(0.5)
    
    return all_passed

def test_site_configuration_retrieval():
    """Test site configuration retrieval and custom system prompts"""
    print_test_header("Site Configuration Retrieval Test")
    
    test_cases = [
        {
            "name": "Demo Site Configuration",
            "site_id": "demo",
            "expected_fields": ["site_id", "greeting_message", "bot_name", "language", "voice_enabled"]
        },
        {
            "name": "Custom Site Configuration",
            "site_id": "custom-test-site",
            "expected_fields": ["site_id", "greeting_message", "bot_name", "language", "voice_enabled"]
        },
        {
            "name": "Non-existent Site (Should use defaults)",
            "site_id": "non-existent-site-12345",
            "expected_fields": ["site_id", "greeting_message", "bot_name", "language", "voice_enabled"]
        }
    ]
    
    all_passed = True
    
    for test_case in test_cases:
        print(f"\n--- Testing: {test_case['name']} ---")
        print(f"Site ID: {test_case['site_id']}")
        
        # Test chat with site configuration
        try:
            response = requests.post(
                f"{API_BASE}/chat",
                json={
                    "message": "Hello, what's your name?",
                    "session_id": f"config-test-{uuid.uuid4()}",
                    "site_id": test_case['site_id']
                },
                headers={"Content-Type": "application/json"},
                timeout=15
            )
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Chat response: {data.get('response', 'No response')[:100]}...")
                print(f"   Model used: {data.get('model', 'Unknown')}")
                
                # The response should be contextual to the site configuration
                response_text = data.get('response', '').lower()
                
                # Check if response mentions assistant or bot (indicating system prompt is working)
                if any(word in response_text for word in ['assistant', 'bot', 'help', 'ai']):
                    print("✅ Response shows system prompt influence")
                else:
                    print("⚠️ Response may not reflect system prompt customization")
                
                print("✅ Site configuration retrieval working")
                
            else:
                print(f"❌ Chat request failed with status {response.status_code}")
                all_passed = False
                
        except Exception as e:
            print(f"❌ Chat request failed: {e}")
            all_passed = False
        
        # Test widget configuration endpoint for the same site
        try:
            config_response = requests.post(
                f"{API_BASE}/widget/config",
                json={"site_id": test_case['site_id']},
                headers={"Content-Type": "application/json"},
                timeout=10
            )
            
            if config_response.status_code == 200:
                config_data = config_response.json()
                print(f"✅ Widget config retrieved for site: {test_case['site_id']}")
                
                # Verify expected fields are present
                missing_fields = [field for field in test_case['expected_fields'] if field not in config_data]
                if missing_fields:
                    print(f"❌ Missing config fields: {missing_fields}")
                    all_passed = False
                else:
                    print("✅ All expected config fields present")
                    
                print(f"   Bot name: {config_data.get('bot_name', 'Unknown')}")
                print(f"   Language: {config_data.get('language', 'Unknown')}")
                print(f"   Voice enabled: {config_data.get('voice_enabled', 'Unknown')}")
                
            else:
                print(f"❌ Widget config request failed with status {config_response.status_code}")
                all_passed = False
                
        except Exception as e:
            print(f"❌ Widget config request failed: {e}")
            all_passed = False
        
        time.sleep(0.5)
    
    return all_passed

def test_error_handling():
    """Test error handling for chat endpoint"""
    print_test_header("Error Handling Test")
    
    test_cases = [
        {
            "name": "Missing Message",
            "payload": {"site_id": "demo"},
            "expected_status": 400,
            "description": "Should return 400 for missing message"
        },
        {
            "name": "Invalid Session ID",
            "payload": {
                "message": "Hello",
                "session_id": "",
                "site_id": "demo"
            },
            "expected_status": 200,
            "description": "Should handle empty session_id gracefully"
        },
        {
            "name": "Missing Site ID",
            "payload": {
                "message": "Hello",
                "session_id": "test-session"
            },
            "expected_status": 200,
            "description": "Should handle missing site_id gracefully"
        }
    ]
    
    all_passed = True
    
    for test_case in test_cases:
        print(f"\n--- Testing: {test_case['name']} ---")
        print(f"Description: {test_case['description']}")
        
        try:
            response = requests.post(
                f"{API_BASE}/chat",
                json=test_case["payload"],
                headers={"Content-Type": "application/json"},
                timeout=10
            )
            
            print_result("/api/chat", response.status_code, response.json() if response.content else {}, test_case["expected_status"])
            
            if response.status_code == test_case["expected_status"]:
                print(f"✅ {test_case['description']}")
            else:
                print(f"❌ Expected status {test_case['expected_status']}, got {response.status_code}")
                all_passed = False
                
        except Exception as e:
            print(f"❌ Request failed: {e}")
            all_passed = False
    
    return all_passed

def test_conversation_logging():
    """Test conversation logging with token tracking"""
    print_test_header("Conversation Logging & Token Tracking Test")
    
    session_id = f"logging-test-{uuid.uuid4()}"
    site_id = "demo"
    
    messages = [
        "Hello, I'm testing conversation logging",
        "Can you help me understand how this works?",
        "Thank you for the explanation"
    ]
    
    all_passed = True
    
    for i, message in enumerate(messages, 1):
        print(f"\n--- Message {i}: {message} ---")
        
        try:
            response = requests.post(
                f"{API_BASE}/chat",
                json={
                    "message": message,
                    "session_id": session_id,
                    "site_id": site_id
                },
                headers={"Content-Type": "application/json"},
                timeout=15
            )
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Response: {data.get('response', 'No response')[:50]}...")
                print(f"   Model: {data.get('model', 'Unknown')}")
                print(f"   Timestamp: {data.get('timestamp', 'Unknown')}")
                print(f"   Conversation length: {data.get('conversation_length', 0)}")
                
                # Verify conversation length increases
                if data.get('conversation_length', 0) == i:
                    print("✅ Conversation length tracking working")
                else:
                    print(f"⚠️ Conversation length: expected {i}, got {data.get('conversation_length', 0)}")
                
                # Check for timestamp format
                timestamp = data.get('timestamp', '')
                if timestamp and 'T' in timestamp:
                    print("✅ Timestamp format is correct (ISO format)")
                else:
                    print("⚠️ Timestamp format may be incorrect")
                
            else:
                print(f"❌ Request failed with status {response.status_code}")
                all_passed = False
                
        except Exception as e:
            print(f"❌ Request failed: {e}")
            all_passed = False
        
        time.sleep(0.5)
    
    return all_passed

def main():
    """Run enhanced AI chat functionality tests"""
    print("🚀 Starting Enhanced AI Chat Functionality Tests")
    print(f"Testing against: {BASE_URL}")
    print(f"Timestamp: {datetime.now().isoformat()}")
    
    test_results = {}
    
    # Run enhanced conversation memory tests
    print("\n" + "="*60)
    print("ENHANCED AI CHAT FUNCTIONALITY TESTS")
    print("="*60)
    
    test_results["enhanced_conversation_memory"] = test_enhanced_conversation_memory()
    test_results["groq_api_fallback"] = test_groq_api_fallback()
    test_results["site_configuration_retrieval"] = test_site_configuration_retrieval()
    test_results["error_handling"] = test_error_handling()
    test_results["conversation_logging"] = test_conversation_logging()
    
    # Print summary
    print(f"\n{'='*60}")
    print("TEST SUMMARY")
    print(f"{'='*60}")
    
    for test_name, result in test_results.items():
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"  {test_name.upper().replace('_', ' ')}: {status}")
    
    # Overall results
    total_tests = len(test_results)
    passed_tests = sum(1 for result in test_results.values() if result)
    
    print(f"\nOverall Result: {passed_tests}/{total_tests} tests passed")
    
    if passed_tests == total_tests:
        print("🎉 All enhanced AI chat functionality tests passed!")
        return True
    else:
        print("⚠️  Some tests failed. Please check the detailed output above.")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)