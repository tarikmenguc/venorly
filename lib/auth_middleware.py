import os
import jwt
from fastapi import HTTPException, Request

# DEV_MODE: CLERK_PUBLIC_KEY tanımlı değilse local geliştirme için auth bypass
_DEV_MODE = not bool(os.getenv("CLERK_PUBLIC_KEY"))

def verify_clerk_token(request: Request) -> dict:
    """
    Clerk JWT token doğrulama middleware'i.
    CLERK_PUBLIC_KEY env değişkeni yoksa (local dev) auth bypass yapılır
    ve {"sub": "dev_user", "dev_mode": True} döner.
    """
    if _DEV_MODE:
        return {"sub": "dev_user", "dev_mode": True}

    authorization = request.headers.get("Authorization")
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Authorization header gerekli")

    token = authorization.split(" ")[1]
    clerk_public_key = os.getenv("CLERK_PUBLIC_KEY", "")

    try:
        payload = jwt.decode(
            token,
            clerk_public_key,
            algorithms=["RS256"],
            options={"verify_signature": True}
        )
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token süresi dolmuş")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Geçersiz token")

def verify_api_key(request: Request, required: bool = True) -> bool:
    """
    Chrome Extension için API key doğrulama
    X-API-Key header'ından key'i alır ve doğrular
    """
    api_key = request.headers.get("X-API-Key")
    expected_key = os.getenv("EXTENSION_API_KEY", "")
    
    if not expected_key:
        # API key yapılandırılmamışsa, doğrulama yapma
        return True
    
    if not api_key:
        if required:
            raise HTTPException(status_code=401, detail="API key gerekli")
        return False
    
    if api_key != expected_key:
        raise HTTPException(status_code=401, detail="Geçersiz API key")
    
    return True
