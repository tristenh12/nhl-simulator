# streamlit_sim_history.py
import streamlit as st
from supabase import create_client
import os

SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

def show_sim_history(email):
    st.subheader("🕓 Your Simulation History")
    try:
        res = supabase.table("simulations").select("*").eq("email", email).order("timestamp", desc=True).execute()
        if res.data:
            for sim in res.data:
                st.write(f"**Date:** {sim['timestamp']}")
                st.json(sim["data"])
        else:
            st.info("You have no saved simulations yet.")
    except Exception as e:
        st.error(f"Failed to load history: {e}")
