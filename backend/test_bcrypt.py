import sys
import os

# Add backend to path
sys.path.insert(0, "C:/programming/scanctum/backend")

from app.core.security import hash_password

try:
    print("Test 1: Normal password")
    pw = "secret"
    h = hash_password(pw)
    print(f"Hash of '{pw}': {h[:10]}... (len: {len(h)})")
    
    print("\nTest 2: Long password > 72 chars")
    pw_long = "a" * 80
    h_long = hash_password(pw_long)
    print(f"Hash of long pw: {h_long[:10]}... (len: {len(h_long)})")

except Exception as e:
    print(f"\nERROR: {e}")
    import traceback
    traceback.print_exc()
