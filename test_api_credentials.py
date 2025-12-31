#!/usr/bin/env python3
"""Test if credentials are loading correctly"""
import os
import sys
from pathlib import Path

# Load .env
try:
    from dotenv import load_dotenv
    load_dotenv()
    print("✅ load_dotenv() called")
except:
    print("❌ load_dotenv() failed")

# Check credentials
key = os.getenv("ALPACA_KEY") or os.getenv("ALPACA_API_KEY", "")
secret = os.getenv("ALPACA_SECRET") or os.getenv("ALPACA_API_SECRET", "")

print(f"ALPACA_KEY: {'✅ Present' if key else '❌ Missing'} (length: {len(key)})")
print(f"ALPACA_SECRET: {'✅ Present' if secret else '❌ Missing'} (length: {len(secret)})")

# Check .env file
env_path = Path(".env")
print(f".env file exists: {env_path.exists()}")

if key and secret:
    print("\n✅ Credentials loaded successfully!")
    sys.exit(0)
else:
    print("\n❌ Credentials NOT loaded")
    sys.exit(1)
