import streamlit as st
from supabase import create_client, Client
import stripe

# Load secrets
SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
STRIPE_SECRET_KEY = st.secrets["STRIPE_SECRET_KEY"]
PRICE_ID = st.secrets["PRICE_ID"]

stripe.api_key = STRIPE_SECRET_KEY
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Dummy sim functions
def run_free_sim():
    st.header("🏒 Free Simulation")
    st.write("This is the free mode. Enjoy!")

def run_full_sim():
    st.header("💸 Full Simulation")
    st.success("Welcome to the premium simulation!")

# UI Setup
st.set_page_config(page_title="NHL What-If Simulator", layout="wide")
mode = st.sidebar.radio("Pick Simulation Mode:", ("Free", "Full"))

if mode == "Free":
    run_free_sim()

elif mode == "Full":
    if "user" not in st.session_state:
        st.sidebar.title("🔐 Login / Signup")
        auth_mode = st.sidebar.radio("Auth Mode", ["Login", "Signup"])
        email = st.sidebar.text_input("Email")
        password = st.sidebar.text_input("Password", type="password")

        if st.sidebar.button(auth_mode):
            try:
                if auth_mode == "Signup":
                    res = supabase.auth.sign_up({"email": email, "password": password})
                else:
                    res = supabase.auth.sign_in_with_password({"email": email, "password": password})

                if res.user:
                    st.session_state.user = res.user
                    st.rerun()
                else:
                    st.sidebar.error("Authentication failed.")
            except Exception as e:
                st.sidebar.error(str(e))
    else:
        user = st.session_state.user
        st.sidebar.success(f"Logged in as {user.email}")
        if st.sidebar.button("Logout"):
            del st.session_state.user
            st.session_state.pop("is_paid", None)
            st.rerun()

        # Payment check
        if "is_paid" not in st.session_state:
            try:
                res = supabase.table("users").select("paid").eq("email", user.email).single().execute()
                paid = res.data.get("paid", False)
                st.session_state["is_paid"] = paid
            except Exception as e:
                st.session_state["is_paid"] = False
                st.error("Could not check payment status.")

        if st.session_state["is_paid"]:
            run_full_sim()
        else:
            st.warning("You must pay to access the full simulation.")
            try:
                checkout_session = stripe.checkout.Session.create(
                    payment_method_types=["card"],
                    line_items=[{"price": PRICE_ID, "quantity": 1}],
                    mode="payment",
                    customer_email=user.email,
                    success_url="https://www.nhlwhatif.com/success",
                    cancel_url="https://www.nhlwhatif.com/cancelled"
                )

                # Debug info before redirect
                st.subheader("🔍 Stripe Checkout Session Created")
                st.json(checkout_session)
                st.markdown(f"👉 [Click here to open Stripe Checkout]({checkout_session.url})", unsafe_allow_html=True)

                st.stop()

            except Exception as e:
                st.subheader("🚨 Stripe Checkout Failed")
                st.exception(e)
