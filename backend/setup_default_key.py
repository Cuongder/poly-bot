#!/usr/bin/env python3
"""Setup default API key for testing"""
import hashlib
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.database import Database

def setup_default_api_key():
    db = Database()

    # Create a default API key
    api_key = "demo-api-key-123456789"
    key_hash = hashlib.sha256(api_key.encode()).hexdigest()

    # Check if already exists using the proper method
    key_data = db.validate_api_key(key_hash)
    if key_data:
        print(f"Default API key already exists: {api_key}")
        return api_key

    # Insert new key using the proper method
    key_id = db.add_api_key(key_hash, "frontend-default", "write")
    print(f"Created default API key: {api_key}")
    return api_key

if __name__ == "__main__":
    setup_default_api_key()
