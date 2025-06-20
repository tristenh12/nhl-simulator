import streamlit as st
import pandas as pd
from supabase import create_client

SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

def show_sim_history(user_email):
    st.title("📂 Saved Simulations")

    try:
        response = supabase.table("simulations").select("*").eq("email", user_email).order("timestamp", desc=True).execute()
        data = response.data

        if not data:
            st.info("No saved simulations found.")
            return

        for sim in data:
            st.markdown("---")
            st.write(f"**📝 Name**: {sim['name']}")
            st.write(f"**📅 Date**: {sim.get('timestamp', 'Unknown')}")

            with st.expander("📊 View Standings"):
                df = pd.DataFrame(sim.get("standings", []))
                st.dataframe(df, use_container_width=True)

            col1, col2 = st.columns([1, 1])
            with col1:
                if st.button(f"↩ Load Into Full Sim", key=f"load_{sim['id']}"):
                    st.session_state.team_slots = [
                        {"team": entry.split(" (")[0], "season": entry.split("(")[-1].replace(")", "")}
                        for entry in sim.get("teams", [])
                    ]
                    st.success("✅ Loaded into Full Sim. Go to the Full Sim tab to view.")
            with col2:
                if st.button("🗑 Delete", key=f"delete_{sim['id']}"):
                    supabase.table("simulations").delete().eq("id", sim["id"]).execute()
                    st.warning(f"🗑 Deleted simulation: {sim['name']}")
                    st.rerun()

    except Exception as e:
        st.error(f"Failed to load history: {e}")
