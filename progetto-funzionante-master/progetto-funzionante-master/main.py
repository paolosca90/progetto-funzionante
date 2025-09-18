#!/usr/bin/env python
"""
Railway Main Entrypoint
Imports the main FastAPI application from frontend/
"""

import sys
import os

# Add current directory and frontend to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'frontend'))

# Import and run the main app from frontend directory
from frontend.main import app

# Export the app for Railway to use
__all__ = ['app']

# Also make the variable available directly for Railway
app = app
