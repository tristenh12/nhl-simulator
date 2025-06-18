from fastapi import FastAPI, Request
from supabase import create_client, Client
from dotenv import load_dotenv
import stripe
import os

# Load secrets from .env
load_dotenv()

app = FastAPI()

# Supabase config
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Stripe config
stripe.api_key = os.getenv("STRIPE_SECRET_KEY")
endpoint_secret = os.getenv("STRIPE_WEBHOOK_SECRET")

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
