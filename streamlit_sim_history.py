import streamlit as st
import pandas as pd
from playoff import display_bracket_table_v4

def show_sim_history(supabase):
    user_email = st.session_state["user"].email
    sims = supabase.table("simulations").select("*").eq("email", user_email).order("timestamp", desc=True).execute().data

    if not sims:
        st.info("You haven’t saved any simulations yet.")
        return

    for sim in sims:
        with st.expander(f"{sim['name']} — {sim['timestamp'][:19].replace('T', ' ')}"):
            st.write("**Teams:**")
            st.write(sim["teams"])

            col1, col2 = st.columns(2)
            with col1:
                if st.button("Load", key=f"load_{sim['name']}_{sim['timestamp']}"):
                    try:
                        parsed_slots = []
                        for t in sim["teams"]:
                            if " (" in t and t.endswith(")"):
                                team = t.split(" (")[0]
                                season = t.split(" (")[1].rstrip(")")
                                parsed_slots.append({"team": team, "season": season})
                            else:
                                raise ValueError(f"Invalid team format: {t}")
                        st.session_state["team_slots"] = parsed_slots
                        st.session_state["load_trigger"] = True
                        st.success("Loaded into Full Sim tab.")
                    except Exception as e:
                        st.error(f"Error loading this simulation: {e}")

            with col2:
                if st.button("Delete", key=f"del_{sim['name']}_{sim['timestamp']}"):
                    supabase.table("simulations").delete().eq("email", user_email).eq("name", sim["name"]).execute()
                    st.success("Deleted.")
                    st.rerun()

            # ────────────────────────────────────────
            # 📊 Show Standings if Available
            # ────────────────────────────────────────
            if "standings" in sim:
                st.markdown("### 📊 Final Standings")
                df = pd.DataFrame(sim["standings"])
                df["PTS"] = pd.to_numeric(df["PTS"], errors="coerce")
                for d in df["Division"].unique():
                    div_df = df[df["Division"] == d].sort_values(by=["PTS", "Win%"], ascending=[False, False])
                    div_df = div_df.reset_index(drop=True)
                    div_df.index += 1
                    st.write(f"#### {d}")
                    st.dataframe(div_df[["Team", "GP", "W", "L", "OTL", "PTS", "Win%"]], use_container_width=True)

            # ────────────────────────────────────────
            # 🏆 Show Playoff Bracket if Available
            # ────────────────────────────────────────
            if "playoffs" in sim and sim["playoffs"]:
                st.markdown("### 🏆 Playoff Bracket")
                display_bracket_table_v4(sim["playoffs"])
