#!/usr/bin/env python3
"""Entry point for running the API server"""
import sys
import os

# Ensure backend is in path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import directly to ensure we get the right module
import api.main

# Get the app object
app = api.main.app

# Print route info for debugging
print(f"Starting server with {len(app.routes)} routes...")
for r in app.routes:
    if hasattr(r, 'path'):
        print(f"  - {r.path}")

if __name__ == "__main__":
    import uvicorn
    # Use the app object directly, not a string reference
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
