#!/usr/bin/env python3
"""
Debug conversation memory functionality
"""

import requests
import json
import time
import uuid

BASE_URL = "https://7c22ebce-6df8-4589-98e2-2d39a78cddd6.preview.emergentagent.com"
API_BASE = f"{BASE_URL}/api"

def debug_conversation_memory():
    """Debug conversation memory step by step"""
    print("🔍 Debugging Conversation Memory")
    
    session_id = f"debug-{uuid.uuid4()}"
    site_id = "demo"
    
    messages = [
        "Hello, this is message 1",
        "This is message 2, can you remember message 1?",
        "This is message 3, do you remember our conversation?"
    ]
    
    for i, message in enumerate(messages, 1):
        print(f"\n--- Sending Message {i}: {message} ---")
        
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
                print(f"✅ Response: {data.get('response', 'No response')}")
                print(f"   Session ID: {data.get('session_id', 'Unknown')}")
                print(f"   Model: {data.get('model', 'Unknown')}")
                print(f"   Conversation Length: {data.get('conversation_length', 0)}")
                print(f"   Timestamp: {data.get('timestamp', 'Unknown')}")
                
                # Check if the response shows awareness of previous messages
                response_text = data.get('response', '').lower()
                if i > 1:
                    if any(word in response_text for word in ['remember', 'previous', 'earlier', 'conversation', 'mentioned']):
                        print("✅ Response shows conversation awareness")
                    else:
                        print("⚠️ Response may not show conversation awareness")
                
            else:
                print(f"❌ Request failed with status {response.status_code}")
                if response.content:
                    print(f"   Error: {response.json()}")
                    
        except Exception as e:
            print(f"❌ Request failed: {e}")
        
        # Wait a bit to ensure database write completes
        time.sleep(1)
    
    print(f"\n--- Final Test: Ask about conversation history ---")
    try:
        response = requests.post(
            f"{API_BASE}/chat",
            json={
                "message": "Can you summarize our conversation so far?",
                "session_id": session_id,
                "site_id": site_id
            },
            headers={"Content-Type": "application/json"},
            timeout=15
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Summary Response: {data.get('response', 'No response')}")
            print(f"   Conversation Length: {data.get('conversation_length', 0)}")
            
            # Check if the summary mentions previous messages
            response_text = data.get('response', '').lower()
            if any(word in response_text for word in ['message 1', 'message 2', 'message 3', 'conversation', 'discussed']):
                print("✅ Summary shows conversation memory")
            else:
                print("⚠️ Summary may not show conversation memory")
                
        else:
            print(f"❌ Summary request failed with status {response.status_code}")
            
    except Exception as e:
        print(f"❌ Summary request failed: {e}")

if __name__ == "__main__":
    debug_conversation_memory()