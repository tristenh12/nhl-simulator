import streamlit as st
from supabase import create_client, Client
import stripe

from free_sim_gui import run_free_sim
from streamlit_full_sim import run_full_sim
from streamlit_sim_history import show_sim_history

# Supabase setup
SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
st.session_state["supabase_client"] = supabase

# Streamlit setup
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

# Sidebar login
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
                    try:
                        supabase.table("users").insert({
                            "email": email,
                            "paid": False
                        }).execute()
                    except:
                        st.sidebar.warning("Signup worked, but user DB entry failed.")
                    st.session_state.user = res.user
                    st.rerun()
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

    # Check payment status
    if "is_paid" not in st.session_state:
        try:
            res = supabase.table("users").select("paid").eq("email", user.email).single().execute()
            paid = res.data.get("paid", False) if res.data else False
            st.session_state["is_paid"] = paid
        except Exception as e:
            st.session_state["is_paid"] = False
            st.error("Could not check payment status.")

    if st.sidebar.button("🔄 Refresh Access"):
        try:
            res = supabase.table("users").select("paid").eq("email", user.email).single().execute()
            paid = res.data.get("paid", False) if res.data else False
            st.session_state["is_paid"] = paid
            st.rerun()
        except:
            st.error("Error refreshing payment status.")

    if st.sidebar.button("Logout"):
        del st.session_state["user"]
        st.session_state.pop("is_paid", None)
        st.rerun()

# Tabs
tab1, tab2, tab3 = st.tabs(["🏒 Free Sim", "🧠 Full Sim", "📁 View Saved Sims"])

with tab1:
    run_free_sim()

with tab2:
    if "user" in st.session_state:
        if st.session_state.get("is_paid", False):
            run_full_sim()
        else:
            st.warning("You must pay to access the full simulation.")
            st.markdown("👉 [Go to Pricing Page](https://www.nhlwhatif.com/pricing)")
    else:
        st.warning("Please log in to access the Full Simulator.")

with tab3:
    if "user" in st.session_state:
        show_sim_history(st.session_state.user.email)
    else:
        st.warning("Please log in to view your saved simulations.")
