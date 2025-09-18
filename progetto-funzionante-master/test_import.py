#!/usr/bin/env python
"""
Test script to verify main.py imports work correctly
"""

import os
import sys

# Set environment to development before importing anything
os.environ["ENVIRONMENT"] = "development"

# Add paths for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'frontend'))

try:
    # Test the import that main.py does
    from frontend.main import app
    print("✓ Successfully imported FastAPI app from frontend.main")
    print(f"✓ App type: {type(app)}")
    print("✓ Railway deployment structure is working correctly!")

    # Test if app has the expected attributes
    if hasattr(app, 'routes'):
        print(f"✓ App has {len(app.routes)} routes configured")

    print("\n=== IMPORT TEST PASSED ===")

except Exception as e:
    print(f"X Import failed: {e}")
    print("\n=== IMPORT TEST FAILED ===")
    import traceback
    traceback.print_exc()