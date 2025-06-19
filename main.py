import os
from dotenv import load_dotenv
import streamlit as st
from supabase import create_client, Client
from free_sim_gui import run_free_sim
from streamlit_full_sim import run_full_sim

# Load environment variables
load_dotenv()

# Supabase setup
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Set page config
st.set_page_config(page_title="NHL What-If Simulator", layout="wide")

# Apply global styles (optional: your CSS block goes here)

# Mode selector
mode = st.sidebar.radio("Pick Simulation Mode:", ("Free", "Full"))

if mode == "Free":
    # Run Free Sim with no login required
    run_free_sim()

elif mode == "Full":
    # Require login or signup
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
        # Logged in
        st.sidebar.success(f"Logged in as {st.session_state.user.email}")
        if st.sidebar.button("Logout"):
            del st.session_state.user
            st.rerun()

        # OPTIONAL: Paywall logic
        email = st.session_state.user.email
        user_data = supabase.table("users").select("paid").eq("email", email).execute()
        paid = user_data.data[0]["paid"] if user_data.data else False

        if paid:
            run_full_sim()
        else:
            st.warning("🚫 You must purchase access to use Full Sim.")
            st.markdown("[Click here to upgrade](https://your-checkout-link.com)")
