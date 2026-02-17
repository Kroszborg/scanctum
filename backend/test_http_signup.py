import requests
import json

url = "http://localhost:8000/api/v1/auth/signup"
headers = {
    "Content-Type": "application/json",
    "Origin": "http://localhost:3000"
}
data = {
    "email": "admin@scanctum.com",
    "password": "admin123",
    "full_name": "Admin User"
}

print(f"Sending POST request to {url}")
print(f"Data: {json.dumps(data, indent=2)}")

try:
    response = requests.post(url, json=data, headers=headers)
    print(f"\nStatus Code: {response.status_code}")
    print(f"Headers: {dict(response.headers)}")
    print(f"Response: {response.text}")
    
    if response.status_code == 200:
        print("\n✅ SUCCESS! Signup worked!")
        result = response.json()
        print(f"Access Token: {result.get('access_token', 'N/A')[:50]}...")
        print(f"User: {result.get('user', {})}")
    else:
        print(f"\n❌ FAILED with status {response.status_code}")
        
except Exception as e:
    print(f"\n❌ ERROR: {e}")
    import traceback
    traceback.print_exc()
