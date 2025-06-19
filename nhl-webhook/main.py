from fastapi import FastAPI, Request, Header
from supabase import create_client, Client
from dotenv import load_dotenv
import stripe
import os

# Load .env for local or Render environment
load_dotenv()

app = FastAPI()

# --- Supabase config ---
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# --- Stripe config ---
stripe.api_key = os.getenv("STRIPE_SECRET_KEY")
WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET")
PRICE_ID = os.getenv("PRICE_ID")  # Optional, or hardcoded below

# --- Stripe webhook listener ---
@app.post("/webhook")
async def stripe_webhook(request: Request, stripe_signature: str = Header(None)):
    payload = await request.body()

    try:
        event = stripe.Webhook.construct_event(
            payload=payload,
            sig_header=stripe_signature,
            secret=WEBHOOK_SECRET
        )

        if event["type"] == "checkout.session.completed":
            session = event["data"]["object"]
            email = session.get("customer_email")

            if email:
                print(f"✅ Marking {email} as paid in Supabase")
                supabase.table("users").update({"paid": True}).eq("email", email).execute()
            else:
                print("⚠️ No email found in session")

    except Exception as e:
        print(f"❌ Webhook error: {e}")
        return {"error": str(e)}

    return {"status": "success"}

# --- Stripe Checkout session creation ---
@app.post("/create-checkout-session")
async def create_checkout_session(request: Request):
    try:
        data = await request.json()
        email = data.get("email")

        session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            line_items=[{
                "price": PRICE_ID or "price_1RbUgFLh041OrJKozeN9eQJh",
                "quantity": 1
            }],
            mode="payment",
            customer_email=email,
            success_url="https://www.nhlwhatif.com/app",
            cancel_url="https://www.nhlwhatif.com/cancelled"
        )

        print(f"✅ Created Stripe Checkout session for {email or '[no email]'}")
        return {"id": session.id}

    except Exception as e:
        print(f"❌ Checkout session creation failed: {e}")
        return {"error": str(e)}
