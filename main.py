# main.py

import os
from dotenv import load_dotenv
import streamlit as st
from supabase import create_client, Client
import stripe
from free_sim_gui import run_free_sim
from streamlit_full_sim import run_full_sim

# Load environment variables
load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
STRIPE_SECRET_KEY = os.getenv("STRIPE_SECRET_KEY")

# Initialize clients
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
stripe.api_key = STRIPE_SECRET_KEY

# Set up page
st.set_page_config(page_title="NHL What-If Simulator", layout="wide")

# Apply custom CSS for responsive layout
st.markdown("""
<style>
  .block-container {
    transform: scale(0.95) !important;
    transform-origin: top center !important;
  }
  @media (max-width: 600px) {
    .block-container { padding: 1rem 0.5rem !important; }
    h1, h2, h3 { font-size: 1.3rem !important; }
    .stButton>button { padding: 0.5rem 1rem !important; font-size: 0.9rem !important; }
  }
  .stImage img, .stChart>div {
    max-width: 100% !important;
    height: auto !important;
  }
</style>
""", unsafe_allow_html=True)

# --- AUTH ---
if "user" not in st.session_state:
    st.sidebar.title("🔐 Login or Signup")
    mode = st.sidebar.radio("Select Mode", ["Login", "Signup"])
    email = st.sidebar.text_input("Email")
    password = st.sidebar.text_input("Password", type="password")

    if st.sidebar.button(mode):
        try:
            if mode == "Signup":
                res = supabase.auth.sign_up({"email": email, "password": password})
            else:
                res = supabase.auth.sign_in_with_password({"email": email, "password": password})

            if res.user:
                st.session_state.user = res.user
                st.rerun()
            else:
                st.sidebar.error("Failed to authenticate.")
        except Exception as e:
            st.sidebar.error(str(e))
    st.stop()

else:
    st.sidebar.success(f"Logged in as {st.session_state.user.email}")
    if st.sidebar.button("Logout"):
        del st.session_state.user
        st.rerun()

# --- PAID CHECK ---
email = st.session_state.user.email
user_check = supabase.table("users").select("paid").eq("email", email).execute()
is_paid = user_check.data and user_check.data[0].get("paid", False)

# --- SELECT MODE ---
mode = st.sidebar.radio("Pick Simulation Mode:", ("Free", "Full"))

# --- RUN SIM ---
if mode == "Free":
    run_free_sim()

elif mode == "Full":
    if is_paid:
        run_full_sim()
    else:
        st.warning("🚫 Full simulation mode requires a one-time upgrade.")
        if st.button("Upgrade Now"):
            st.markdown("[Go to Pricing Page](https://www.nhlwhatif.com/pricing)")

