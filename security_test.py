#!/usr/bin/env python3
"""
Security and Production Infrastructure Testing Script
Tests enhanced security features, rate limiting, input validation, and production infrastructure
"""

import requests
import json
import time
from datetime import datetime
import uuid
import threading
from concurrent.futures import ThreadPoolExecutor
import re

# Configuration
BASE_URL = "https://5f968ed4-0598-44bb-9e69-5064cb737711.preview.emergentagent.com"
API_BASE = f"{BASE_URL}/api"

def print_test_header(test_name):
    """Print formatted test header"""
    print(f"\n{'='*70}")
    print(f"TESTING: {test_name}")
    print(f"{'='*70}")

def print_result(endpoint, status_code, response_data, expected_status=200, test_name=""):
    """Print test result in formatted way"""
    success = "✅" if status_code == expected_status else "❌"
    print(f"{success} {test_name} - {endpoint}")
    print(f"   Status Code: {status_code} (Expected: {expected_status})")
    if isinstance(response_data, dict):
        print(f"   Response: {json.dumps(response_data, indent=2, default=str)}")
    else:
        print(f"   Response: {response_data}")
    print()

def test_enhanced_health_checks():
    """Test enhanced health check endpoints"""
    print_test_header("Enhanced Health Checks")
    
    all_passed = True
    
    # Test /api/health endpoint
    print("\n--- Testing /api/health endpoint ---")
    try:
        response = requests.get(f"{API_BASE}/health", timeout=10)
        data = response.json()
        
        print_result("/api/health", response.status_code, data, test_name="Detailed Health Check")
        
        # Validate enhanced health check structure
        required_fields = ["status", "timestamp", "version", "services", "metrics"]
        missing_fields = [field for field in required_fields if field not in data]
        
        if missing_fields:
            print(f"❌ Missing required fields: {missing_fields}")
            all_passed = False
        else:
            print("✅ All required health check fields present")
        
        # Check services status
        if "services" in data:
            services = data["services"]
            if "mongodb" in services:
                print(f"✅ MongoDB status: {services['mongodb'].get('status', 'unknown')}")
            if "groq" in services:
                print(f"✅ GROQ status: {services['groq'].get('status', 'unknown')}")
        
        # Check metrics
        if "metrics" in data:
            print("✅ System metrics included in health check")
        
        # Check rate limiting info
        if "rate_limiting" in data:
            rate_info = data["rate_limiting"]
            print(f"✅ Rate limiting info: {rate_info.get('max_requests_per_minute', 'unknown')} req/min, {rate_info.get('chat_requests_per_minute', 'unknown')} chat req/min")
        
    except Exception as e:
        print(f"❌ Health check failed: {e}")
        all_passed = False
    
    # Test /api/metrics endpoint
    print("\n--- Testing /api/metrics endpoint ---")
    try:
        response = requests.get(f"{API_BASE}/metrics", timeout=10)
        data = response.json()
        
        print_result("/api/metrics", response.status_code, data, test_name="Metrics Endpoint")
        
        if response.status_code == 200:
            # Validate metrics structure
            expected_fields = ["timestamp", "totals", "last_24_hours", "rate_limiting"]
            missing_fields = [field for field in expected_fields if field not in data]
            
            if missing_fields:
                print(f"❌ Missing metrics fields: {missing_fields}")
                all_passed = False
            else:
                print("✅ All metrics fields present")
                
            # Check totals
            if "totals" in data:
                totals = data["totals"]
                print(f"✅ Total conversations: {totals.get('conversations', 0)}")
                print(f"✅ Total interactions: {totals.get('interactions', 0)}")
        
    except Exception as e:
        print(f"❌ Metrics endpoint failed: {e}")
        all_passed = False
    
    # Test /api/status endpoint
    print("\n--- Testing /api/status endpoint ---")
    try:
        response = requests.get(f"{API_BASE}/status", timeout=10)
        data = response.json()
        
        print_result("/api/status", response.status_code, data, test_name="Status Endpoint")
        
        if response.status_code == 200:
            if data.get("status") == "ok":
                print("✅ Service status is OK")
            else:
                print(f"❌ Service status is not OK: {data.get('status')}")
                all_passed = False
                
            if "timestamp" in data:
                print("✅ Timestamp included in status")
        
    except Exception as e:
        print(f"❌ Status endpoint failed: {e}")
        all_passed = False
    
    return all_passed

def test_rate_limiting():
    """Test rate limiting for chat endpoint"""
    print_test_header("Rate Limiting Tests")
    
    all_passed = True
    
    # Test chat endpoint rate limiting (MAX_CHAT_REQUESTS_PER_MINUTE = 20)
    print("\n--- Testing Chat Endpoint Rate Limiting (20 req/min) ---")
    
    session_id = f"rate-test-{uuid.uuid4()}"
    
    def make_chat_request(i):
        """Make a single chat request"""
        try:
            response = requests.post(
                f"{API_BASE}/chat",
                json={
                    "message": f"Test message {i}",
                    "session_id": session_id,
                    "site_id": "demo"
                },
                headers={"Content-Type": "application/json"},
                timeout=5
            )
            return response.status_code, i
        except Exception as e:
            return 500, i
    
    # Send 25 requests rapidly to test rate limiting
    print("Sending 25 rapid requests to test rate limiting...")
    
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(make_chat_request, i) for i in range(25)]
        results = [future.result() for future in futures]
    
    # Analyze results
    success_count = sum(1 for status, _ in results if status == 200)
    rate_limited_count = sum(1 for status, _ in results if status == 429)
    error_count = sum(1 for status, _ in results if status not in [200, 429])
    
    print(f"✅ Successful requests: {success_count}")
    print(f"✅ Rate limited requests (429): {rate_limited_count}")
    print(f"❌ Error requests: {error_count}")
    
    # Rate limiting should kick in after 20 requests
    if rate_limited_count > 0:
        print("✅ Rate limiting is working - some requests were rate limited")
    else:
        print("❌ Rate limiting may not be working - no 429 responses")
        all_passed = False
    
    if success_count <= 20:
        print("✅ Rate limiting appears to be enforcing the 20 req/min limit")
    else:
        print(f"❌ Too many successful requests ({success_count}) - rate limiting may not be working")
        all_passed = False
    
    # Test general API rate limiting
    print("\n--- Testing General API Rate Limiting (60 req/min) ---")
    
    def make_health_request(i):
        """Make a health check request"""
        try:
            response = requests.get(f"{API_BASE}/health", timeout=5)
            return response.status_code, i
        except Exception as e:
            return 500, i
    
    # Send 70 requests rapidly to test general rate limiting
    print("Sending 70 rapid health check requests to test general rate limiting...")
    
    with ThreadPoolExecutor(max_workers=15) as executor:
        futures = [executor.submit(make_health_request, i) for i in range(70)]
        results = [future.result() for future in futures]
    
    # Analyze results
    success_count = sum(1 for status, _ in results if status == 200)
    rate_limited_count = sum(1 for status, _ in results if status == 429)
    
    print(f"✅ Successful health requests: {success_count}")
    print(f"✅ Rate limited health requests (429): {rate_limited_count}")
    
    if rate_limited_count > 0:
        print("✅ General rate limiting is working")
    else:
        print("⚠️ General rate limiting may not be working as expected")
    
    return all_passed

def test_input_validation_and_sanitization():
    """Test input validation and sanitization"""
    print_test_header("Input Validation and Sanitization")
    
    all_passed = True
    session_id = f"validation-test-{uuid.uuid4()}"
    
    # Test cases for input validation
    test_cases = [
        {
            "name": "Empty Message",
            "payload": {"session_id": session_id, "site_id": "demo"},
            "expected_status": 400,
            "description": "Should reject empty message"
        },
        {
            "name": "Whitespace Only Message",
            "payload": {"message": "   ", "session_id": session_id, "site_id": "demo"},
            "expected_status": 400,
            "description": "Should reject whitespace-only message"
        },
        {
            "name": "Very Long Message (>1000 chars)",
            "payload": {
                "message": "A" * 1001,  # 1001 characters
                "session_id": session_id,
                "site_id": "demo"
            },
            "expected_status": 400,
            "description": "Should reject messages longer than MAX_MESSAGE_LENGTH (1000)"
        },
        {
            "name": "Normal Message",
            "payload": {
                "message": "This is a normal message that should work fine",
                "session_id": session_id,
                "site_id": "demo"
            },
            "expected_status": 200,
            "description": "Should accept normal messages"
        },
        {
            "name": "Message at Length Limit",
            "payload": {
                "message": "A" * 1000,  # Exactly 1000 characters
                "session_id": session_id,
                "site_id": "demo"
            },
            "expected_status": 200,
            "description": "Should accept messages at the length limit"
        }
    ]
    
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
            
            data = response.json() if response.content else {}
            print_result("/api/chat", response.status_code, data, test_case["expected_status"], test_case["name"])
            
            if response.status_code == test_case["expected_status"]:
                print(f"✅ {test_case['name']} handled correctly")
            else:
                print(f"❌ {test_case['name']} not handled correctly")
                all_passed = False
                
        except Exception as e:
            print(f"❌ {test_case['name']} test failed: {e}")
            all_passed = False
    
    return all_passed

def test_xss_protection():
    """Test XSS protection and content filtering"""
    print_test_header("XSS Protection and Content Filtering")
    
    all_passed = True
    session_id = f"xss-test-{uuid.uuid4()}"
    
    # XSS test cases
    xss_test_cases = [
        {
            "name": "Script Tag Injection",
            "payload": {
                "message": "<script>alert('XSS')</script>",
                "session_id": session_id,
                "site_id": "demo"
            },
            "description": "Should sanitize script tags"
        },
        {
            "name": "JavaScript URL",
            "payload": {
                "message": "Click here: javascript:alert('XSS')",
                "session_id": session_id,
                "site_id": "demo"
            },
            "description": "Should sanitize javascript: URLs"
        },
        {
            "name": "Event Handler Injection",
            "payload": {
                "message": "<img src='x' onerror='alert(1)'>",
                "session_id": session_id,
                "site_id": "demo"
            },
            "description": "Should sanitize event handlers"
        },
        {
            "name": "Eval Function",
            "payload": {
                "message": "eval('alert(1)')",
                "session_id": session_id,
                "site_id": "demo"
            },
            "description": "Should sanitize eval functions"
        },
        {
            "name": "Document Object Access",
            "payload": {
                "message": "document.cookie",
                "session_id": session_id,
                "site_id": "demo"
            },
            "description": "Should sanitize document object access"
        },
        {
            "name": "Window Object Access",
            "payload": {
                "message": "window.location = 'http://evil.com'",
                "session_id": session_id,
                "site_id": "demo"
            },
            "description": "Should sanitize window object access"
        }
    ]
    
    for test_case in xss_test_cases:
        print(f"\n--- Testing: {test_case['name']} ---")
        print(f"Description: {test_case['description']}")
        print(f"Input: {test_case['payload']['message']}")
        
        try:
            response = requests.post(
                f"{API_BASE}/chat",
                json=test_case["payload"],
                headers={"Content-Type": "application/json"},
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                ai_response = data.get("response", "")
                
                # Check if the malicious content was sanitized
                original_message = test_case["payload"]["message"]
                
                # The AI response should not contain the original malicious content
                # and the input should have been sanitized
                print(f"AI Response: {ai_response}")
                
                # Check for dangerous patterns in the response
                dangerous_patterns = [
                    r'<script[^>]*>',
                    r'javascript:',
                    r'on\w+\s*=',
                    r'eval\s*\(',
                    r'document\.',
                    r'window\.'
                ]
                
                found_dangerous = False
                for pattern in dangerous_patterns:
                    if re.search(pattern, ai_response, re.IGNORECASE):
                        found_dangerous = True
                        break
                
                if not found_dangerous:
                    print(f"✅ {test_case['name']} - XSS content properly sanitized")
                else:
                    print(f"❌ {test_case['name']} - Dangerous content found in response")
                    all_passed = False
                    
            elif response.status_code == 400:
                # Input validation rejected the malicious input
                print(f"✅ {test_case['name']} - Malicious input rejected by validation")
            else:
                print(f"❌ {test_case['name']} - Unexpected response: {response.status_code}")
                all_passed = False
                
        except Exception as e:
            print(f"❌ {test_case['name']} test failed: {e}")
            all_passed = False
    
    return all_passed

def test_spam_detection():
    """Test spam pattern detection"""
    print_test_header("Spam Pattern Detection")
    
    all_passed = True
    session_id = f"spam-test-{uuid.uuid4()}"
    
    # Spam test cases
    spam_test_cases = [
        {
            "name": "Repeated Characters",
            "payload": {
                "message": "aaaaaaaaaaaaaaaaaaaaaa",  # 22 repeated 'a's
                "session_id": session_id,
                "site_id": "demo"
            },
            "expected_status": 400,
            "description": "Should reject messages with excessive repeated characters"
        },
        {
            "name": "Excessive Caps",
            "payload": {
                "message": "THIS IS A VERY LONG MESSAGE WITH ALL CAPS THAT SHOULD BE DETECTED AS SPAM BECAUSE IT HAS TOO MANY CAPITAL LETTERS",
                "session_id": session_id,
                "site_id": "demo"
            },
            "expected_status": 400,
            "description": "Should reject messages with excessive capital letters"
        },
        {
            "name": "Multiple URLs",
            "payload": {
                "message": "Check out https://site1.com and https://site2.com and https://site3.com and https://site4.com and https://site5.com",
                "session_id": session_id,
                "site_id": "demo"
            },
            "expected_status": 400,
            "description": "Should reject messages with multiple URLs"
        },
        {
            "name": "Normal Message with Single URL",
            "payload": {
                "message": "Check out this website: https://example.com",
                "session_id": session_id,
                "site_id": "demo"
            },
            "expected_status": 200,
            "description": "Should accept normal messages with single URL"
        },
        {
            "name": "Normal Message",
            "payload": {
                "message": "This is a normal message that should be accepted",
                "session_id": session_id,
                "site_id": "demo"
            },
            "expected_status": 200,
            "description": "Should accept normal messages"
        }
    ]
    
    for test_case in spam_test_cases:
        print(f"\n--- Testing: {test_case['name']} ---")
        print(f"Description: {test_case['description']}")
        
        try:
            response = requests.post(
                f"{API_BASE}/chat",
                json=test_case["payload"],
                headers={"Content-Type": "application/json"},
                timeout=10
            )
            
            data = response.json() if response.content else {}
            print_result("/api/chat", response.status_code, data, test_case["expected_status"], test_case["name"])
            
            if response.status_code == test_case["expected_status"]:
                print(f"✅ {test_case['name']} handled correctly")
            else:
                print(f"❌ {test_case['name']} not handled correctly")
                all_passed = False
                
        except Exception as e:
            print(f"❌ {test_case['name']} test failed: {e}")
            all_passed = False
    
    return all_passed

def test_profanity_filter():
    """Test profanity filter in AI responses"""
    print_test_header("Profanity Filter Testing")
    
    all_passed = True
    session_id = f"profanity-test-{uuid.uuid4()}"
    
    # Test cases that might trigger profanity in responses
    test_cases = [
        {
            "name": "Normal Question",
            "message": "What is artificial intelligence?",
            "description": "Normal question should get clean response"
        },
        {
            "name": "Question About Inappropriate Content",
            "message": "Tell me about inappropriate content filtering",
            "description": "Should get clean response about content filtering"
        }
    ]
    
    for test_case in test_cases:
        print(f"\n--- Testing: {test_case['name']} ---")
        print(f"Description: {test_case['description']}")
        
        try:
            response = requests.post(
                f"{API_BASE}/chat",
                json={
                    "message": test_case["message"],
                    "session_id": session_id,
                    "site_id": "demo"
                },
                headers={"Content-Type": "application/json"},
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                ai_response = data.get("response", "")
                
                print(f"AI Response: {ai_response}")
                
                # Check for profanity patterns (these should be filtered to ***)
                profanity_words = [
                    'fuck', 'shit', 'damn', 'hell', 'bitch', 'ass', 'crap',
                    'piss', 'bastard', 'whore', 'slut', 'retard'
                ]
                
                found_profanity = False
                for word in profanity_words:
                    if word.lower() in ai_response.lower():
                        found_profanity = True
                        break
                
                if not found_profanity:
                    print(f"✅ {test_case['name']} - No profanity in response")
                else:
                    print(f"❌ {test_case['name']} - Profanity found in response")
                    all_passed = False
                
                # Check if response length is reasonable (should be limited to 500 chars for voice)
                if len(ai_response) <= 500:
                    print(f"✅ Response length appropriate for voice: {len(ai_response)} chars")
                else:
                    print(f"⚠️ Response might be too long for voice: {len(ai_response)} chars")
                    
            else:
                print(f"❌ {test_case['name']} - Unexpected response: {response.status_code}")
                all_passed = False
                
        except Exception as e:
            print(f"❌ {test_case['name']} test failed: {e}")
            all_passed = False
    
    return all_passed

def test_enhanced_logging():
    """Test enhanced logging with IP tracking"""
    print_test_header("Enhanced Logging and IP Tracking")
    
    all_passed = True
    session_id = f"logging-test-{uuid.uuid4()}"
    
    print("\n--- Testing Enhanced Logging ---")
    
    # Make a chat request to test logging
    try:
        response = requests.post(
            f"{API_BASE}/chat",
            json={
                "message": "Test message for logging",
                "session_id": session_id,
                "site_id": "demo"
            },
            headers={
                "Content-Type": "application/json",
                "User-Agent": "SecurityTestBot/1.0",
                "X-Forwarded-For": "192.168.1.100"  # Test IP forwarding
            },
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Chat request successful - logging should have captured:")
            print("   - Client IP address")
            print("   - User agent")
            print("   - Request timestamp")
            print("   - Session ID and site ID")
            print("   - Message content and AI response")
            print("   - Model used and token count")
            
            # Check if rate limit info is included
            if "rate_limit_remaining" in data:
                print(f"✅ Rate limit info included: {data['rate_limit_remaining']} requests remaining")
            else:
                print("⚠️ Rate limit info not included in response")
                
        else:
            print(f"❌ Chat request failed: {response.status_code}")
            all_passed = False
            
    except Exception as e:
        print(f"❌ Enhanced logging test failed: {e}")
        all_passed = False
    
    # Test analytics logging
    print("\n--- Testing Analytics Logging ---")
    
    try:
        response = requests.post(
            f"{API_BASE}/analytics/interaction",
            json={
                "site_id": "demo",
                "session_id": session_id,
                "type": "security_test",
                "user_message": "Test message",
                "ai_response": "Test response"
            },
            headers={
                "Content-Type": "application/json",
                "User-Agent": "SecurityTestBot/1.0"
            },
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get("status") == "logged":
                print("✅ Analytics interaction logged successfully")
                print("   - Should include IP address and user agent")
                print("   - Should include timestamp and interaction details")
            else:
                print("❌ Analytics logging failed")
                all_passed = False
        else:
            print(f"❌ Analytics logging request failed: {response.status_code}")
            all_passed = False
            
    except Exception as e:
        print(f"❌ Analytics logging test failed: {e}")
        all_passed = False
    
    return all_passed

def test_error_handling():
    """Test enhanced error handling"""
    print_test_header("Enhanced Error Handling")
    
    all_passed = True
    
    # Test various error scenarios
    error_test_cases = [
        {
            "name": "Invalid JSON",
            "url": f"{API_BASE}/chat",
            "method": "POST",
            "data": "invalid json",
            "headers": {"Content-Type": "application/json"},
            "expected_status": 400,
            "description": "Should handle invalid JSON gracefully"
        },
        {
            "name": "Missing Content-Type",
            "url": f"{API_BASE}/chat",
            "method": "POST",
            "data": json.dumps({"message": "test"}),
            "headers": {},
            "expected_status": 400,
            "description": "Should handle missing content type"
        },
        {
            "name": "Non-existent Endpoint",
            "url": f"{API_BASE}/nonexistent",
            "method": "GET",
            "data": None,
            "headers": {},
            "expected_status": 404,
            "description": "Should return 404 for non-existent endpoints"
        }
    ]
    
    for test_case in error_test_cases:
        print(f"\n--- Testing: {test_case['name']} ---")
        print(f"Description: {test_case['description']}")
        
        try:
            if test_case["method"] == "POST":
                response = requests.post(
                    test_case["url"],
                    data=test_case["data"],
                    headers=test_case["headers"],
                    timeout=10
                )
            else:
                response = requests.get(
                    test_case["url"],
                    headers=test_case["headers"],
                    timeout=10
                )
            
            print_result(test_case["url"], response.status_code, 
                        response.json() if response.content else {}, 
                        test_case["expected_status"], test_case["name"])
            
            if response.status_code == test_case["expected_status"]:
                print(f"✅ {test_case['name']} handled correctly")
            else:
                print(f"❌ {test_case['name']} not handled correctly")
                all_passed = False
                
        except Exception as e:
            print(f"❌ {test_case['name']} test failed: {e}")
            all_passed = False
    
    return all_passed

def main():
    """Run all security and infrastructure tests"""
    print("🔒 Starting Security and Production Infrastructure Tests")
    print(f"Testing against: {BASE_URL}")
    print(f"Timestamp: {datetime.now().isoformat()}")
    
    test_results = {}
    
    # Run security tests
    print("\n" + "="*70)
    print("SECURITY AND PRODUCTION INFRASTRUCTURE TESTS")
    print("="*70)
    
    test_results["enhanced_health_checks"] = test_enhanced_health_checks()
    test_results["rate_limiting"] = test_rate_limiting()
    test_results["input_validation"] = test_input_validation_and_sanitization()
    test_results["xss_protection"] = test_xss_protection()
    test_results["spam_detection"] = test_spam_detection()
    test_results["profanity_filter"] = test_profanity_filter()
    test_results["enhanced_logging"] = test_enhanced_logging()
    test_results["error_handling"] = test_error_handling()
    
    # Print summary
    print(f"\n{'='*70}")
    print("SECURITY TEST SUMMARY")
    print(f"{'='*70}")
    
    for test_name, result in test_results.items():
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"  {test_name.upper().replace('_', ' ')}: {status}")
    
    # Overall results
    total_tests = len(test_results)
    passed_tests = sum(1 for result in test_results.values() if result)
    
    print(f"\nOverall Security Test Result: {passed_tests}/{total_tests} tests passed")
    
    if passed_tests == total_tests:
        print("🎉 All security tests passed! Enhanced security features are working correctly.")
        return True
    else:
        print("⚠️  Some security tests failed. Please check the detailed output above.")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)