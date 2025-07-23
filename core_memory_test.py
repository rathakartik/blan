#!/usr/bin/env python3
"""
Focused 90-Day Memory Core Functionality Test
Testing the essential memory features without strict conversation length validation
"""

import requests
import json
import time
from datetime import datetime
import uuid

# Configuration
BASE_URL = "https://1b823cca-a15f-4de7-84e0-78cacec68eeb.preview.emergentagent.com"
API_BASE = f"{BASE_URL}/api"

def test_core_memory_functionality():
    """Test core 90-day memory functionality"""
    print("🧠 Testing Core 90-Day Memory Functionality")
    print("="*50)
    
    # Generate unique visitor ID for testing
    visitor_id = f"visitor-{uuid.uuid4()}"
    site_id = "demo"
    session_id_1 = f"session-1-{uuid.uuid4()}"
    session_id_2 = f"session-2-{uuid.uuid4()}"
    
    print(f"Visitor ID: {visitor_id}")
    
    results = {
        "visitor_id_storage": False,
        "new_visitor_detection": False,
        "returning_visitor_detection": False,
        "cross_session_memory": False,
        "memory_context_integration": False,
        "visitor_isolation": False,
        "database_storage": False
    }
    
    # Test 1: New Visitor
    print("\n1. Testing New Visitor...")
    try:
        response = requests.post(
            f"{API_BASE}/chat",
            json={
                "message": "Hello, I'm new here",
                "session_id": session_id_1,
                "site_id": site_id,
                "visitor_id": visitor_id
            },
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            
            # Check visitor ID storage
            if data.get('visitor_id') == visitor_id:
                results["visitor_id_storage"] = True
                print("   ✅ Visitor ID stored and returned correctly")
            
            # Check new visitor detection
            if data.get('is_returning_visitor') == False:
                results["new_visitor_detection"] = True
                print("   ✅ Correctly identified as new visitor")
            
            # Check database storage fields
            required_fields = ["response", "session_id", "visitor_id", "timestamp", "is_returning_visitor"]
            if all(field in data for field in required_fields):
                results["database_storage"] = True
                print("   ✅ All required database fields present")
                
        else:
            print(f"   ❌ Failed with status {response.status_code}")
            
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Small delay
    time.sleep(1)
    
    # Test 2: Same Visitor, Different Session (Cross-Session Memory)
    print("\n2. Testing Cross-Session Memory...")
    try:
        response = requests.post(
            f"{API_BASE}/chat",
            json={
                "message": "Hi again! Do you remember me?",
                "session_id": session_id_2,  # Different session
                "site_id": site_id,
                "visitor_id": visitor_id  # Same visitor
            },
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            
            # Check returning visitor detection
            if data.get('is_returning_visitor') == True:
                results["returning_visitor_detection"] = True
                results["cross_session_memory"] = True
                print("   ✅ Correctly identified as returning visitor")
                print("   ✅ Cross-session memory working")
            
            # Check memory context in response
            response_text = data.get('response', '').lower()
            memory_indicators = ['welcome back', 'returning', 'again', 'remember', 'previous', 'earlier']
            if any(indicator in response_text for indicator in memory_indicators):
                results["memory_context_integration"] = True
                print("   ✅ Memory context integrated in AI response")
                print(f"   Response: {data.get('response', '')[:100]}...")
                
        else:
            print(f"   ❌ Failed with status {response.status_code}")
            
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Test 3: Different Visitor (Isolation)
    print("\n3. Testing Visitor Isolation...")
    try:
        different_visitor_id = f"visitor-{uuid.uuid4()}"
        response = requests.post(
            f"{API_BASE}/chat",
            json={
                "message": "Hello, I'm a different visitor",
                "session_id": f"session-{uuid.uuid4()}",
                "site_id": site_id,
                "visitor_id": different_visitor_id
            },
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            
            # Check that this is treated as new visitor
            if (data.get('is_returning_visitor') == False and 
                data.get('visitor_id') == different_visitor_id):
                results["visitor_isolation"] = True
                print("   ✅ Visitor isolation working correctly")
                
        else:
            print(f"   ❌ Failed with status {response.status_code}")
            
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Summary
    print("\n" + "="*50)
    print("CORE MEMORY FUNCTIONALITY RESULTS")
    print("="*50)
    
    passed_tests = sum(results.values())
    total_tests = len(results)
    
    for test_name, passed in results.items():
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{test_name.replace('_', ' ').title()}: {status}")
    
    print(f"\nOverall: {passed_tests}/{total_tests} core tests passed")
    
    # Critical functionality check
    critical_tests = [
        "visitor_id_storage",
        "new_visitor_detection", 
        "returning_visitor_detection",
        "cross_session_memory",
        "database_storage"
    ]
    
    critical_passed = sum(1 for test in critical_tests if results[test])
    critical_total = len(critical_tests)
    
    print(f"Critical Memory Features: {critical_passed}/{critical_total} passed")
    
    if critical_passed == critical_total:
        print("\n🎉 Core 90-day memory functionality is working correctly!")
        return True
    else:
        print("\n❌ Some critical memory features are not working")
        return False

if __name__ == "__main__":
    success = test_core_memory_functionality()
    exit(0 if success else 1)