import streamlit as st
import pandas as pd
from playoff import display_bracket_table_v4

def show_sim_history(supabase):
    user_email = st.session_state["user"].email
    sims = supabase.table("simulations").select("*").eq("email", user_email).order("timestamp", desc=True).execute().data

    # Load season data to match team-season to division
    @st.cache_data
    def load_season_df(path="data/teams_alignment_complete.csv"):
        return pd.read_csv(path)

    season_df = load_season_df()

    if not sims:
        st.info("You haven’t saved any simulations yet.")
        return

    for sim in sims:
        with st.expander(f"{sim['name']} — {sim['timestamp'][:19].replace('T', ' ')}"):

            # Nicely organized team view grouped by division
            st.markdown("### 🧩 Teams by Division")
            division_map = {}
            for entry in sim["teams"]:
                if " (" not in entry:
                    continue
                team = entry.split(" (")[0]
                season = entry.split(" (")[1].rstrip(")")
                row = season_df[(season_df["Team"] == team) & (season_df["Season"] == season)]
                if not row.empty:
                    division = row.iloc[0]["Division"]
                else:
                    division = "Unknown"
                division_map.setdefault(division, []).append(entry)

            for division, team_list in division_map.items():
                st.write(f"#### {division}")
                st.write(", ".join(team_list))

            # Buttons to load/delete
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
                    st.experimental_rerun()

            # Standings
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

            # Playoff bracket
            if "playoffs" in sim and sim["playoffs"]:
                st.markdown("### 🏆 Playoff Bracket")
                display_bracket_table_v4(sim["playoffs"])
