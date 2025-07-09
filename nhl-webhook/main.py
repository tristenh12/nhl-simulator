from fastapi import FastAPI, Request, Header
from fastapi.middleware.cors import CORSMiddleware
from supabase import create_client, Client
from dotenv import load_dotenv
import stripe
import os

load_dotenv()
app = FastAPI()

# 👇 Add CORS support for Webflow domain
origins = [
    "https://www.nhlwhatif.com",
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Supabase config ---
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# --- Stripe config ---
stripe.api_key     = os.getenv("STRIPE_SECRET_KEY")
WEBHOOK_SECRET     = os.getenv("STRIPE_WEBHOOK_SECRET")
PRICE_ID           = os.getenv("PRICE_ID")  # now pulled from env

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
        # attempt to read an email from the request body (optional)
        try:
            data = await request.json()
            email = data.get("email")
        except:
            email = None

        # Create the session using your PRICE_ID env var
        session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            line_items=[{
                "price": PRICE_ID,      # ← now using the env var
                "quantity": 1
            }],
            mode="payment",
            customer_creation="if_required",
            success_url="https://www.nhlwhatif.com/simulator",
            cancel_url="https://www.nhlwhatif.com/pricing"
        )

        print(f"✅ Created Stripe Checkout session for {email or '[no email]'}")
        return {"id": session.id}

    except Exception as e:
        print(f"❌ Checkout session creation failed: {e}")
        return {"error": str(e)}
