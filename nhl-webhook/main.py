from fastapi import FastAPI, Request
from supabase import create_client, Client
import stripe
import os

app = FastAPI()

# Supabase config
SUPABASE_URL = "https://ufhjlyygntynwdgpeqbk.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InVmaGpseXlnbnR5bndkZ3BlcWJrIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTAyODAxNTAsImV4cCI6MjA2NTg1NjE1MH0.hPVEjp6Si3W8WTw_hPHPpEEpyqidt5bLezMtuwD9f2A"
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Stripe config
stripe.api_key = "REMOVED_SECRET"
endpoint_secret = "whsec_BA2zsHNvAvG3EDkEA1jtjYkbjb7ryPJ8"

@app.post("/webhook")
async def stripe_webhook(request: Request):
    payload = await request.body()
    sig_header = request.headers.get('stripe-signature')

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, endpoint_secret
        )
    except Exception as e:
        print("Webhook error:", e)
        return {"error": str(e)}

    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']
        customer_email = session.get('customer_email')

        if customer_email:
            print(f"✅ Marking {customer_email} as paid")
            supabase.table("users").update({"paid": True}).eq("email", customer_email).execute()

    return {"status": "success"}
