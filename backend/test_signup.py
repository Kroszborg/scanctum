import asyncio
import sys
from sqlalchemy.ext.asyncio import AsyncSession

# Add the backend directory to the path
sys.path.insert(0, "C:/programming/scanctum/backend")

from app.db.session import get_async_session
from app.schemas.auth import RegisterRequest
from app.services.auth_service import AuthService


async def test_signup():
    """Test the signup functionality to see what error occurs."""
    try:
        # Get a database session
        async for session in get_async_session():
            service = AuthService(session)
            
            # Try to register a user
            data = RegisterRequest(
                email="test@example.com",
                password="testpass123",
                full_name="Test User"
            )
            
            print("Attempting to register user...")
            user = await service.register_public(data)
            print(f"User registered successfully: {user.email}")
            
            # Try to login
            print("Attempting to login...")
            result = await service.login(user.email, data.password)
            print(f"Login successful! Token: {result.access_token[:20]}...")
            
    except Exception as e:
        print(f"Error occurred: {type(e).__name__}")
        print(f"Error message: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_signup())
