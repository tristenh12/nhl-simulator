import streamlit as st
from supabase import create_client, Client
import stripe
import os

# Securely pull in environment variables from st.secrets
SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
stripe.api_key = st.secrets["STRIPE_SECRET_KEY"]

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Set Streamlit app layout
st.set_page_config(
    page_title="NHL What-If Simulator",
    layout="wide"
)

# CSS Tweaks
st.markdown("""
<style>
  .block-container { transform: scale(0.95); transform-origin: top center; }
  @media (max-width: 600px) {
    .block-container { padding: 1rem 0.5rem !important; }
    h1, h2, h3 { font-size: 1.3rem !important; }
    .stButton>button { padding: 0.5rem 1rem !important; font-size: 0.9rem !important; }
  }
  .stImage img, .stChart>div { max-width: 100% !important; height: auto !important; }
</style>
""", unsafe_allow_html=True)

# Load simulation modules
from free_sim_gui import run_free_sim
from streamlit_full_sim import run_full_sim

# Sidebar: Auth only if Full Sim is selected
mode = st.sidebar.radio("Pick Simulation Mode:", ("Free", "Full"))

if mode == "Full":
    if "user" not in st.session_state:
        st.sidebar.title("🔐 Login or Signup")
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
        st.sidebar.success(f"Logged in as {st.session_state.user.email}")
        if st.sidebar.button("Logout"):
            del st.session_state.user
            if "is_paid" in st.session_state:
                del st.session_state["is_paid"]
            st.rerun()

        # Check if user is paid only once
        if "is_paid" not in st.session_state:
            email = st.session_state.user.email
            res = supabase.table("users").select("paid").eq("email", email).single().execute()
            is_paid = res.data.get("paid", False) if res.data else False
            st.session_state["is_paid"] = is_paid

# Run appropriate simulator
elif "user" in st.session_state:
    # Check paid status only once
    if "is_paid" not in st.session_state:
        try:
            email = st.session_state.user.email
            res = supabase.table("users").select("paid").eq("email", email).execute()

            if res.data and len(res.data) > 0:
                is_paid = res.data[0].get("paid", False)
            else:
                is_paid = False

            st.session_state["is_paid"] = is_paid
        except Exception as e:
            st.error("Unable to verify payment status.")
            st.session_state["is_paid"] = False

    if st.session_state["is_paid"]:
        run_full_sim()
    else:
        st.warning("Redirecting you to payment...")

        import stripe

        # Replace with your test or live price ID
        PRICE_ID = "price_1RbUgFLh041OrJKozeN9eQJh"

        try:
            checkout_session = stripe.checkout.Session.create(
                payment_method_types=["card"],
                line_items=[{"price": PRICE_ID, "quantity": 1}],
                mode="payment",
                customer_email=st.session_state.user.email,
                success_url="https://www.nhlwhatif.com",
                cancel_url="https://www.nhlwhatif.com/cancelled"
            )

            st.markdown("Please wait... redirecting to Stripe.")
            st.stop()
            st.experimental_redirect(checkout_session.url)

        except Exception as e:
            st.error(f"Checkout failed: {e}")
