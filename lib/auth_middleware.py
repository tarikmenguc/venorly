import os
import hmac
import logging
from fastapi import HTTPException, Request

logger = logging.getLogger(__name__)

# AUTH BYPASS: Sadece APP_ENV=local|test|development ortaminda aktif.
_APP_ENV = os.getenv("APP_ENV", "production").lower()
_DEV_ENVS = {"local", "test", "development"}
_AUTH_BYPASS = _APP_ENV in _DEV_ENVS

if _AUTH_BYPASS:
    logger.warning(
        "[AuthMiddleware] DEV MODE: Kimlik dogrulama devre disi (APP_ENV=%s). "
        "Production'da bu log gorulmemeli.", _APP_ENV
    )


def verify_user_token(request: Request) -> dict:
    """
    Supabase JWT ile kullanici dogrulama.
    """
    if _AUTH_BYPASS:
        return {"sub": "dev_user", "dev_mode": True}

    authorization = request.headers.get("Authorization")
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Authorization header gerekli")

    token = authorization.split(" ")[1]

    try:
        from lib.supabase_client import supabase
        user_res = supabase.auth.get_user(token)
        if user_res and user_res.user:
            return user_res.user.__dict__
    except Exception as e:
        logger.debug("Supabase token dogrulama hatasi: %s", e)

    raise HTTPException(status_code=401, detail="Gecersiz veya suresi dolmus token")


def verify_api_key(request: Request, required: bool = True) -> bool:
    """
    Chrome Extension icin API key dogrulama.
    Timing attack'a karsi hmac.compare_digest kullanir.
    """
    api_key  = request.headers.get("X-API-Key", "")
    expected = os.getenv("EXTENSION_API_KEY", "")

    if not expected:
        if _AUTH_BYPASS:
            return True
        if required:
            raise HTTPException(status_code=500, detail="API key yapilandirilmamis")
        return False

    if not api_key:
        if required:
            raise HTTPException(status_code=401, detail="API key gerekli")
        return False

    if not hmac.compare_digest(api_key.encode("utf-8"), expected.encode("utf-8")):
        raise HTTPException(status_code=401, detail="Gecersiz API key")

    return True
