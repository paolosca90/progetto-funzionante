#!/usr/bin/env python3
"""
Test script to verify all Railway dependencies are installable
"""
import sys
import subprocess

def test_import(package_name):
    """Test if a package can be imported"""
    try:
        __import__(package_name)
        print(f"[OK] {package_name}")
        return True
    except ImportError as e:
        print(f"[FAIL] {package_name} - {e}")
        return False

def main():
    """Test all critical dependencies"""
    print("Testing Railway Dependencies...")
    print("=" * 50)
    
    # Critical dependencies that were failing
    test_packages = [
        'aiofiles',
        'aiosqlite',
        'fastapi',
        'uvicorn',
        'sqlalchemy',
        'psycopg2',
        'pandas',
        'numpy',
        'requests',
        'httpx',
        'google.generativeai',
        'sklearn',
        'bs4',
        'lxml'
    ]
    
    failed = []
    for package in test_packages:
        if not test_import(package):
            failed.append(package)
    
    print("\n" + "=" * 50)
    if failed:
        print(f"[FAILED] {len(failed)} packages failed: {', '.join(failed)}")
        print("\nTo install missing packages:")
        print("pip install " + " ".join(failed))
        sys.exit(1)
    else:
        print(f"[SUCCESS] All {len(test_packages)} packages imported successfully!")
        sys.exit(0)

if __name__ == "__main__":
    main()
