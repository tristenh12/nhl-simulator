import streamlit as st
from supabase import create_client, Client
import stripe

# Supabase setup
SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# UI config
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

# Import simulator modules
from free_sim_gui import run_free_sim
from streamlit_full_sim import run_full_sim
from streamlit_sim_history import show_sim_history

# Helper: get token from URL and authenticate
def authenticate_with_token():
    if "user" not in st.session_state:
        token = st.query_params.get("token")
        if token:
            try:
                supabase.auth.set_session(access_token=token, refresh_token=token)
                user = supabase.auth.get_user().user
                if user:
                    st.session_state["user"] = user
            except Exception as e:
                st.error("Login session invalid or expired.")
    return st.session_state.get("user")

# Authenticate once
user = authenticate_with_token()

# Tabs
tabs = st.tabs(["🏒 Free Sim", "📊 Full Sim", "📁 Saved Sims"])

# --- FREE SIM TAB ---
with tabs[0]:
    run_free_sim()

# --- FULL SIM TAB ---
with tabs[1]:
    if not user:
        st.markdown("""
        <style>
        .login-alert {
            padding: 1rem;
            margin-top: 1rem;
            border-left: 6px solid #0d6efd;
            border-radius: 6px;
            font-size: 1rem;
        }

        @media (prefers-color-scheme: dark) {
            .login-alert {
                background-color: #1e1e1e;
                color: #f0f0f0;
            }
            .login-alert a {
                color: #66b2ff;
            }
        }

        @media (prefers-color-scheme: light) {
            .login-alert {
                background-color: #f0f8ff;
                color: #000000;
            }
            .login-alert a {
                color: #0d6efd;
            }
        }
        </style>

        <div class="login-alert">
            🔐 <strong>You must be logged in to access Full Sim.</strong><br><br>
            👉 <a href="https://www.nhlwhatif.com/login" target="_blank">Go to Login/Signup</a>
        </div>
        """, unsafe_allow_html=True)
        st.stop()


    else:
        st.success(
    f"✅ Logged in as {user.email} — [Manage Account](https://www.nhlwhatif.com/account)"
)


        if "is_paid" not in st.session_state:
            try:
                res = supabase.table("users").select("paid").eq("email", user.email).single().execute()
                st.session_state["is_paid"] = res.data.get("paid", False)
            except:
                st.session_state["is_paid"] = False

        if st.session_state["is_paid"]:
            run_full_sim(supabase)
        else:
            st.warning("🚫 You must purchase access to use the Full Sim.")
            st.markdown("👉 [Go to Pricing Page](https://www.nhlwhatif.com/pricing)")

# --- SAVED SIMS TAB ---
with tabs[2]:
    if not user:
        st.warning("🔐 You must be logged in to view Saved Simulations.")
        st.markdown("👉 [Login to Access](https://www.nhlwhatif.com/login)")
        st.stop()
    elif not st.session_state.get("is_paid", False):
        st.warning("🚫 Saved Simulations are only available to paid users.")
        st.markdown("👉 [Go to Pricing Page](https://www.nhlwhatif.com/pricing)")
    else:
        show_sim_history(supabase)
