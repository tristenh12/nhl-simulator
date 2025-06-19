import streamlit as st
from supabase import create_client
import pandas as pd
import os

# --- Load Supabase ---
SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

st.set_page_config(page_title="Your Simulation History", layout="wide")
st.title("📜 Your Saved Simulations")

# --- AUTH CHECK ---
if "user" not in st.session_state:
    st.warning("Please log in to view your simulation history.")
    st.stop()

user_email = st.session_state["user"].email

# --- FETCH SIMS ---
with st.spinner("Loading your simulations..."):
    try:
        res = supabase.table("simulations").select("*").eq("email", user_email).order("timestamp", desc=True).limit(10).execute()
        sims = res.data if res.data else []
    except Exception as e:
        st.error(f"Error fetching simulations: {e}")
        sims = []

# --- DISPLAY ---
if not sims:
    st.info("No simulations saved yet.")
else:
    for sim in sims:
        st.markdown(f"### 🗓 {sim['timestamp'][:19]}")
        st.markdown("**Teams:** " + ", ".join(sim["teams"]))
        df = pd.DataFrame(sim["standings"])
        st.dataframe(df[["Team", "W", "L", "OTL", "PTS", "Win%"]], use_container_width=True)
        st.markdown("---")
