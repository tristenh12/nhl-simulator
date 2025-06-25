import streamlit as st
from supabase import create_client, Client
import stripe

# Load credentials
SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
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
from streamlit_sim_history import show_sim_history

tabs = st.tabs(["🏒 Free Sim", "📊 Full Sim", "📁 Saved Sims"])

# --- FREE SIM ---
with tabs[0]:
    run_free_sim()

# --- FULL SIM (Requires login & payment) ---
with tabs[1]:
    if "user" not in st.session_state:
        st.warning("🔐 Please log in to access Full Sim.")
        auth_mode = st.radio("Auth Mode", ["Login", "Signup"])
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")
        if st.button(auth_mode):
            try:
                if auth_mode == "Signup":
                    res = supabase.auth.sign_up({"email": email, "password": password})
                    if res.user:
                        supabase.table("users").insert({"email": email, "paid": False}).execute()
                        st.session_state.user = res.user
                        st.rerun()
                else:
                    res = supabase.auth.sign_in_with_password({"email": email, "password": password})
                    if res.user:
                        st.session_state.user = res.user
                        st.rerun()
                    else:
                        st.error("Authentication failed.")
            except Exception as e:
                st.error(str(e))
    else:
        user = st.session_state.user
        st.success(f"✅ Logged in as {user.email}")
        if st.button("Logout"):
            del st.session_state["user"]
            st.session_state.pop("is_paid", None)
            st.rerun()

        # Fetch paid status once on login
        if "is_paid" not in st.session_state:
            try:
                res = supabase.table("users").select("paid").eq("email", user.email).single().execute()
                st.session_state["is_paid"] = res.data.get("paid", False)
            except:
                st.session_state["is_paid"] = False

        if st.session_state["is_paid"]:
            run_full_sim(supabase)
        else:
            st.warning("You must pay to access the full simulation.")
            st.markdown("👉 [Go to Pricing Page](https://www.nhlwhatif.com/pricing)")

# --- SAVED SIMS TAB ---
with tabs[2]:
    if "user" not in st.session_state:
        st.warning("🔐 Please log in to view your saved simulations.")
    else:
        show_sim_history(supabase)
