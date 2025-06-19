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
            st.rerun()

# Run appropriate simulator
if mode == "Free":
    run_free_sim()
elif "user" in st.session_state:
    run_full_sim()
else:
    st.warning("You must be logged in to access the Full Simulation mode.")
