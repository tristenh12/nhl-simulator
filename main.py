import streamlit as st
from supabase import create_client, Client

from free_sim_gui import run_free_sim
from streamlit_full_sim import run_full_sim
from streamlit_sim_history import show_sim_history

# --- Supabase setup ---
SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
st.session_state["supabase_client"] = supabase

# --- Streamlit config ---
st.set_page_config(page_title="NHL What-If Simulator", layout="wide")

# --- Auth sidebar ---
st.sidebar.title("🔐 Login or Signup")

if "user" not in st.session_state:
    auth_mode = st.sidebar.radio("Auth Mode", ["Login", "Signup"])
    email = st.sidebar.text_input("Email")
    password = st.sidebar.text_input("Password", type="password")

    if st.sidebar.button(auth_mode):
        try:
            if auth_mode == "Signup":
                res = supabase.auth.sign_up({"email": email, "password": password})
                if res.user:
                    st.session_state.user = res.user
                    supabase.table("users").insert({"email": email, "paid": False}).execute()
                    st.rerun()
            else:
                res = supabase.auth.sign_in_with_password({"email": email, "password": password})
                if res.user:
                    st.session_state.user = res.user
                    st.rerun()
                else:
                    st.sidebar.error("Login failed.")
        except Exception as e:
            st.sidebar.error(str(e))
else:
    user = st.session_state.user
    st.sidebar.success(f"Logged in as {user.email}")

    if "is_paid" not in st.session_state:
        try:
            res = supabase.table("users").select("paid").eq("email", user.email).single().execute()
            st.session_state["is_paid"] = res.data.get("paid", False)
        except:
            st.session_state["is_paid"] = False

    if st.sidebar.button("Logout"):
        del st.session_state["user"]
        st.session_state.pop("is_paid", None)
        st.rerun()

# --- Main Tabs ---
tab1, tab2, tab3 = st.tabs(["🏒 Free Sim", "🧠 Full Sim", "📁 View Saved Sims"])

with tab1:
    run_free_sim()

with tab2:
    if "user" in st.session_state and st.session_state.get("is_paid", True):
        run_full_sim()
    elif "user" in st.session_state:
        st.warning("Please upgrade to use the Full Simulator.")
    else:
        st.warning("Log in to access the Full Simulator.")

with tab3:
    if "user" in st.session_state:
        show_sim_history(st.session_state.user.email)
    else:
        st.warning("Please log in to view your saved simulations.")
