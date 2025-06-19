import streamlit as st
from supabase import create_client, Client
import stripe

# Load credentials
SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
stripe.api_key = st.secrets["STRIPE_SECRET_KEY"]
PRICE_ID = st.secrets.get("PRICE_ID")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# UI setup
st.set_page_config(page_title="NHL What-If Simulator", layout="wide")
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

# Sim modules
from free_sim_gui import run_free_sim
from streamlit_full_sim import run_full_sim

# Mode selector
mode = st.sidebar.radio("Pick Simulation Mode:", ("Free", "Full"))

if mode == "Free":
    run_free_sim()

elif mode == "Full":
    # --- AUTH ---
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

    # --- LOGGED IN ---
    else:
        user = st.session_state.user
        st.sidebar.success(f"Logged in as {user.email}")
        if st.sidebar.button("Logout"):
            del st.session_state["user"]
            st.session_state.pop("is_paid", None)
            st.rerun()

        # --- CHECK PAYMENT STATUS ---
        if "is_paid" not in st.session_state:
            try:
                res = supabase.table("users").select("paid").eq("email", user.email).single().execute()
                paid = res.data.get("paid", False) if res.data else False
                st.session_state["is_paid"] = paid
            except Exception as e:
                st.session_state["is_paid"] = False
                st.error("Could not check payment status.")

        # --- IF PAID ---
        if st.session_state["is_paid"]:
            run_full_sim()

        # --- IF NOT PAID ---
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

                st.subheader("✅ Stripe Checkout Session Created")
                st.write("Stripe checkout URL:", checkout_session.url)

                st.markdown(f"""
                    <meta http-equiv="refresh" content="0; url={checkout_session.url}" />
                    [Click here if not redirected]({checkout_session.url})
                """, unsafe_allow_html=True)
                st.stop()

            except Exception as e:
                st.subheader("🚨 Stripe Checkout Failed")
                st.exception(e)
