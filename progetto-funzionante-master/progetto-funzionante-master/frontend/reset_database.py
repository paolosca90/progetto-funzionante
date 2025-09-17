#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Reset database script per Railway
Elimina e ricrea tutte le tabelle con il nuovo schema
"""

from database import engine
from models import Base
import os
import sys

def reset_database():
    """Reset completo database"""
    print("Eliminando tutte le tabelle...")
    
    # Drop all tables
    Base.metadata.drop_all(bind=engine)
    print("Tabelle eliminate")
    
    # Recreate all tables
    print("Creando tutte le tabelle con nuovo schema...")
    Base.metadata.create_all(bind=engine)
    print("Tabelle create con successo")
    
    print("Database reset completato!")

if __name__ == "__main__":
    print("RAILWAY DATABASE RESET")
    print("=" * 40)
    
    # Check if we're on Railway
    if os.getenv("DATABASE_URL"):
        print("Detected Railway environment")
        print("Resetting database schema...")
        reset_database()
    else:
        print("Railway DATABASE_URL not found")
        print("This script should run on Railway deployment")