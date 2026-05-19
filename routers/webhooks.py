import os
from fastapi import APIRouter, Request, HTTPException
from lib.supabase_client import supabase
from lib.logger import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/webhooks", tags=["webhooks"])

@router.post("/clerk")
async def clerk_webhook(request: Request):
    """
    Clerk user.created event'ini dinler, Supabase'deki users tablosuna ekler.
    Gerçek senaryoda svix kütüphanesiyle imza doğrulaması (verify_webhook) yapılmalıdır.
    """
    payload = await request.json()
    event_type = payload.get("type")
    
    if event_type == "user.created":
        data = payload.get("data", {})
        clerk_id = data.get("id")
        email_addresses = data.get("email_addresses", [])
        email = email_addresses[0].get("email_address") if email_addresses else ""
        
        try:
            # Users tablosuna yeni kaydı ekle, free planda 5 kredi ver.
            supabase.table("users").insert({
                "clerk_id": clerk_id,
                "email": email,
                "plan_type": "free",
                "credits": 5
            }).execute()
            logger.info(f"Yeni kullanici Supabase'e kaydedildi: {email}")
        except Exception as e:
            logger.error(f"Kullanici eklenirken hata: {e}")
            raise HTTPException(status_code=500, detail="User creation failed")
            
    return {"status": "success"}


@router.post("/stripe")
async def stripe_webhook(request: Request):
    """
    Stripe checkout.session.completed veya invoice.payment_succeeded event'ini dinler,
    kullanıcıya kredi yükler. Gerçek senaryoda stripe.Webhook.construct_event kullanılmalıdır.
    """
    payload = await request.json()
    event_type = payload.get("type")
    
    if event_type == "checkout.session.completed":
        data = payload.get("data", {}).get("object", {})
        customer_email = data.get("customer_details", {}).get("email")
        stripe_customer_id = data.get("customer")
        
        if customer_email:
            try:
                # Kullanıcıyı email'den bul ve kredisini güncelle (Örnek: 100 kredi)
                supabase.table("users").update({
                    "plan_type": "pro",
                    "credits": 100,
                    "stripe_customer_id": stripe_customer_id
                }).eq("email", customer_email).execute()
                
                logger.info(f"Stripe ödemesi alındı, krediler güncellendi: {customer_email}")
            except Exception as e:
                logger.error(f"Kredi güncellenirken hata: {e}")
                
    return {"status": "success"}
