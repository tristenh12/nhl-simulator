# streamlit_sim_history.py

import streamlit as st
import pandas as pd
from supabase import create_client, Client

# Ensure supabase connection is available
SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def show_sim_history(user_email):
    st.title("🕓 My Simulation History")

    try:
        response = supabase.table("simulations") \
            .select("*") \
            .eq("email", user_email) \
            .order("timestamp", desc=True) \
            .execute()

        data = response.data
        if not data:
            st.info("No simulations found.")
            return

        for sim in data:
            st.markdown("---")
            st.write(f"**Date**: {sim.get('timestamp', 'Unknown')}")
            st.write("**Teams**:")
            teams = sim.get("teams", [])
            if teams:
                for t in teams:
                    st.write(f"- {t}")
            else:
                st.write("_No team data_")

            if "standings" in sim and sim["standings"]:
                df = pd.DataFrame(sim["standings"])
                st.dataframe(df, use_container_width=True)
            else:
                st.warning("⚠️ No standings data available for this simulation.")

    except Exception as e:
        st.error(f"❌ Failed to load history: {e}")
