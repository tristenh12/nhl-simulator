# main.py
import streamlit as st
from free_sim_gui import run_free_sim
from streamlit_full_sim import run_full_sim
import streamlit as st
from supabase import create_client, Client

# Supabase credentials
SUPABASE_URL = "https://ufhjlyygntynwdgpeqbk.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InVmaGpseXlnbnR5bndkZ3BlcWJrIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTAyODAxNTAsImV4cCI6MjA2NTg1NjE1MH0.hPVEjp6Si3W8WTw_hPHPpEEpyqidt5bLezMtuwD9f2A"
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Auth logic
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
else:
    st.sidebar.success(f"Logged in as {st.session_state.user.email}")
    if st.sidebar.button("Logout"):
        del st.session_state.user
        st.rerun()

# Set page config once
st.set_page_config(
    page_title="NHL What-If Simulator",
    layout="wide"
)

# Global shrink: slightly reduce overall app size
global_css = """
<style>
  /* uniformly shrink entire app to 95% */
  .block-container {
    transform: scale(0.95) !important;
    transform-origin: top center !important;
  }
</style>
"""
st.markdown(global_css, unsafe_allow_html=True)

# Inject custom CSS for mobile responsiveness
mobile_css = """
<style>
  /* MOBILE-SPECIFIC TWEAKS */
  @media (max-width: 600px) {
    /* tighten up margins/containers */
    .block-container { padding: 1rem 0.5rem !important; }

    /* scale down headings */
    h1, h2, h3 { font-size: 1.3rem !important; }

    /* make buttons a bit smaller */
    .stButton>button { padding: 0.5rem 1rem !important; font-size: 0.9rem !important; }
  }
  /* ensure images/charts never overflow */
  .stImage img, .stChart>div { max-width: 100% !important; height: auto !important; }
</style>
"""
st.markdown(mobile_css, unsafe_allow_html=True)

# Sidebar to choose mode
mode = st.sidebar.radio(
    "Pick Simulation Mode:",
    ("Free", "Full")
)

# Run the selected simulation
if mode == "Free":
    run_free_sim()
else:
    run_full_sim()
