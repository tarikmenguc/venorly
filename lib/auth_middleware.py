import os
import jwt
from fastapi import HTTPException, Request

# AUTH BYPASS: Local geliştirme veya API key tanımlanmamışsa
_AUTH_BYPASS = not bool(os.getenv("CLERK_PUBLIC_KEY")) and not bool(os.getenv("SUPABASE_JWT_SECRET"))

def verify_user_token(request: Request) -> dict:
    """
    Kullanıcı token doğrulama middleware'i (Supabase & Clerk destekler).
    """
    if _AUTH_BYPASS:
        return {"sub": "dev_user", "dev_mode": True}

    authorization = request.headers.get("Authorization")
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Authorization header gerekli")

    token = authorization.split(" ")[1]

    # 1. Supabase Doğrulaması (Öncelikli)
    try:
        from lib.supabase_client import supabase
        user_res = supabase.auth.get_user(token)
        if user_res and user_res.user:
            # Pydantic modelini dict'e çevir
            return user_res.user.__dict__
    except Exception:
        pass

    # 2. Clerk Fallback (Eski sistem uyumluluğu için)
    clerk_public_key = os.getenv("CLERK_PUBLIC_KEY", "")
    if clerk_public_key:
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

    raise HTTPException(status_code=401, detail="Geçersiz veya eksik kimlik bilgisi")

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
