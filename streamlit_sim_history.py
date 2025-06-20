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
            st.write("**Teams (by Division):**")

            # Assign teams to modern divisions (fallback to balance)
            divisions = {"Atlantic": [], "Metropolitan": [], "Central": [], "Pacific": []}
            for team_entry in sim["teams"]:
                if " (" in team_entry and team_entry.endswith(")"):
                    team = team_entry.split(" (")[0]
                    season = team_entry.split(" (")[1].rstrip(")")
                    # Try to infer division from saved standings if possible
                    matched_rows = [
                        row for row in sim["standings"]
                        if row["RawTeam"] == team and str(row.get("Season", "")) == season
                    ]
                    if matched_rows:
                        div = matched_rows[0].get("Division", "")
                        if div not in divisions:
                            div = min(divisions, key=lambda d: len(divisions[d]))
                    else:
                        div = min(divisions, key=lambda d: len(divisions[d]))
                    divisions[div].append(f"{team} ({season})")

            st.markdown("**Teams (Grouped by Division):**")
            div_keys = list(divisions.keys())

            # First row: Atlantic & Metropolitan
            row1 = st.columns(2)
            with row1[0]:
                st.markdown(f"**{div_keys[0]}**")
                for t in divisions[div_keys[0]]:
                    st.write(f"- {t}")
            with row1[1]:
                st.markdown(f"**{div_keys[1]}**")
                for t in divisions[div_keys[1]]:
                    st.write(f"- {t}")

            # Second row: Central & Pacific
            row2 = st.columns(2)
            with row2[0]:
                st.markdown(f"**{div_keys[2]}**")
                for t in divisions[div_keys[2]]:
                    st.write(f"- {t}")
            with row2[1]:
                st.markdown(f"**{div_keys[3]}**")
                for t in divisions[div_keys[3]]:
                    st.write(f"- {t}")


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
                        st.session_state["last_df"] = pd.DataFrame(sim["standings"])
                        st.session_state["playoff_bracket"] = sim["playoffs"]
                        st.success("Simulation loaded! Scroll down to view results.")
                    except Exception as e:
                        st.error(f"Error loading this simulation: {e}")

            with col2:
                if st.button("Delete", key=f"del_{sim['name']}_{sim['timestamp']}"):
                    supabase.table("simulations").delete().eq("email", user_email).eq("name", sim["name"]).execute()
                    st.success("Deleted.")
                    st.experimental_rerun()

            # Show results inline if available
            if "standings" in sim and sim["standings"]:
                st.markdown("### 🏒 Standings")
                df = pd.DataFrame(sim["standings"])
                view_mode = st.selectbox(
                    f"View Mode for '{sim['name']}'",
                    ["By Division", "By Conference", "Entire League", "Playoffs"],
                    key=f"view_mode_{sim['name']}"
                )

                if view_mode == "By Division":
                    for div in df["Division"].unique():
                        st.write(f"#### {div}")
                        div_df = df[df["Division"] == div].sort_values(by=["PTS", "Win%"], ascending=[False, False])
                        st.dataframe(div_df[["Team", "GP", "W", "L", "OTL", "PTS", "Win%"]], use_container_width=True)

                elif view_mode == "By Conference":
                    for conf in df["Conference"].unique():
                        st.write(f"#### {conf}")
                        conf_df = df[df["Conference"] == conf].sort_values(by=["PTS", "Win%"], ascending=[False, False])
                        st.dataframe(conf_df[["Team", "GP", "W", "L", "OTL", "PTS", "Win%"]], use_container_width=True)

                elif view_mode == "Entire League":
                    league_df = df.sort_values(by=["PTS", "Win%"], ascending=[False, False])
                    st.dataframe(league_df[["Team", "GP", "W", "L", "OTL", "PTS", "Win%"]], use_container_width=True)

                else:  # Playoffs
                    from playoff import display_bracket_table_v4
                    st.subheader("🏆 Playoff Bracket")
                    display_bracket_table_v4(sim["playoffs"])
