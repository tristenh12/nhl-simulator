import streamlit as st
import pandas as pd
import random
import os
import datetime

from sim_engine import simulate_season, build_dataframe
from playoff import simulate_playoffs_streamlit, display_bracket_table_v4

def run_full_sim(supabase):
    # ─────────────────────────────────
    # 0) PAGE CONFIG & TITLE
    # ─────────────────────────────────
    st.title("📅 NHL Full-Season What-If Simulator")
    st.markdown("Fill 32 slots (team + season), simulate an 82-game schedule, then view standings + playoffs.")

    # ─────────────────────────────────────────────────────────────────────
    # A) LOAD MASTER CSV + INITIALIZE STATE
    # ─────────────────────────────────────────────────────────────────────
    @st.cache_data
    def load_season_df():
        here = os.path.dirname(__file__)
        data_path = os.path.join(here, "data", "teams_alignment_complete.csv")
        return pd.read_csv(data_path)

    season_df = load_season_df()
    all_teams = sorted(season_df["Team"].unique())
    available_seasons = sorted(season_df["Season"].unique(), reverse=True)
    default_season = available_seasons[0]

    # Initialize preview toggle
    if "show_preview" not in st.session_state:
        st.session_state.show_preview = False

    # Initialize slots
    if "team_slots" not in st.session_state:
        teams_in_default = sorted(season_df[season_df["Season"] == default_season]["Team"].unique())
        slots = []
        for i in range(32):
            if i < len(teams_in_default):
                slots.append({"team": teams_in_default[i], "season": default_season})
            else:
                slots.append({"team": "", "season": ""})
        st.session_state.team_slots = slots

    def get_seasons_for_team(t):
        return sorted(season_df[season_df["Team"] == t]["Season"].unique(), reverse=True) if t else []

    # Build full list for randomize
    all_valid_pairs = [(row.Team, row.Season) for _, row in season_df.iterrows()]

    # ─────────────────────────────────────────────────────────────────────
    # B) INNER TABS: Teams | Tools | Results
    # ─────────────────────────────────────────────────────────────────────
    tab_teams, tab_tools, tab_results = st.tabs([
        "1) Team Selector", "2) Tools", "3) Results"
    ])

    # ─────────────────────────────────────────────────────────────────────
    # 1) TEAM SELECTOR
    # ─────────────────────────────────────────────────────────────────────
    with tab_teams:
        st.markdown("### Customize Your 32-Team League")
        # show/hide all slots
        if not st.session_state.get("show_all_slots", False):
            if st.button("🔽 Show All 32 Slots"):
                st.session_state.show_all_slots = True
        else:
            if st.button("🔼 Collapse to 4 Slots"):
                st.session_state.show_all_slots = False

        num_slots = 32 if st.session_state.get("show_all_slots", False) else 4
        col1, col2 = st.columns(2)
        for i in range(num_slots // 2):
            with col1:
                slot = st.session_state.team_slots[i]
                t = st.selectbox(f"– Team {i+1:02d}", [""] + all_teams,
                                 index=(all_teams.index(slot["team"]) + 1) if slot["team"] in all_teams else 0,
                                 key=f"team_{i}")
                s = st.selectbox(f"– Season {i+1:02d}", [""] + get_seasons_for_team(t),
                                 index=(get_seasons_for_team(t).index(slot["season"]) + 1) if slot["season"] in get_seasons_for_team(t) else 0,
                                 key=f"season_{i}")
                st.session_state.team_slots[i] = {"team": t, "season": s}

        for i in range(num_slots // 2, num_slots):
            with col2:
                slot = st.session_state.team_slots[i]
                t = st.selectbox(f"– Team {i+1:02d}", [""] + all_teams,
                                 index=(all_teams.index(slot["team"]) + 1) if slot["team"] in all_teams else 0,
                                 key=f"team_{i}")
                s = st.selectbox(f"– Season {i+1:02d}", [""] + get_seasons_for_team(t),
                                 index=(get_seasons_for_team(t).index(slot["season"]) + 1) if slot["season"] in get_seasons_for_team(t) else 0,
                                 key=f"season_{i}")
                st.session_state.team_slots[i] = {"team": t, "season": s}

    # ─────────────────────────────────────────────────────────────────────
    # 2) TOOLS
    # ─────────────────────────────────────────────────────────────────────
    with tab_tools:
        st.markdown("### League-Wide Controls / Load-Save / Run Simulation")

        # — Load Saved Simulation
        user_email = st.session_state["user"].email
        sims = supabase.table("simulations") \
                        .select("name, teams") \
                        .eq("email", user_email) \
                        .order("timestamp", desc=True) \
                        .execute().data
        names = [s["name"] for s in sims]
        sel = st.selectbox("🔁 Load Saved Simulation", [""] + names, key="sel_saved")
        if st.button("📥 Load into Slots"):
            if sel:
                sim = next(s for s in sims if s["name"] == sel)
                new_slots = []
                for t in sim["teams"]:
                    team, yr = t.rsplit(" (", 1)
                    yr = yr.rstrip(")")
                    new_slots.append({"team": team, "season": yr})
                while len(new_slots) < 32:
                    new_slots.append({"team": "", "season": ""})
                st.session_state.team_slots = new_slots
                st.experimental_rerun()

        # — Fill Full Season
        season_to_fill = st.selectbox("📅 Fill Full Season → Select Season", available_seasons,
                                      index=available_seasons.index(default_season), key="fill_season")
        if st.button("📅 Fill Full Season"):
            teams_that_year = sorted(season_df[season_df["Season"] == season_to_fill]["Team"].unique())
            for i in range(32):
                if i < len(teams_that_year):
                    st.session_state.team_slots[i] = {"team": teams_that_year[i], "season": season_to_fill}
                else:
                    st.session_state.team_slots[i] = {"team": "", "season": ""}
            st.experimental_rerun()

        # — Fill Each Slot by Year
        one_team = st.selectbox("🗓 Fill Each Slot by Team", [""] + all_teams, key="one_team")
        if st.button("🗓 Fill Each Slot by Year"):
            if one_team:
                years = sorted(season_df[season_df["Team"] == one_team]["Season"].unique(), reverse=True)
                for i in range(32):
                    if i < len(years):
                        st.session_state.team_slots[i] = {"team": one_team, "season": years[i]}
                    else:
                        st.session_state.team_slots[i] = {"team": "", "season": ""}
                st.experimental_rerun()

        st.markdown("---")
        # optional CSS for small buttons
        st.markdown("""
        <style>
          div.stButton > button { padding:4px 8px !important; font-size:0.85rem !important; }
        </style>""", unsafe_allow_html=True)

        # — Quick Actions
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            if st.button("♻ Reset to Default"):
                st.session_state.pop("team_slots", None)
                st.experimental_rerun()
        with c2:
            if st.button("🔀 Randomize All Slots"):
                sample = random.sample(all_valid_pairs, 32)
                st.session_state.team_slots = [{"team": t, "season": s} for t, s in sample]
                st.experimental_rerun()
        with c3:
            if st.button("👀 Toggle Preview"):
                st.session_state.show_preview = not st.session_state.show_preview
        with c4:
            if st.button("✅ Run Full-Season Simulation"):
                # clear old playoff state
                st.session_state.pop("playoff_bracket", None)
                st.session_state.show_preview = False

                # gather valid selections
                sel = [
                    {"RawTeam": slot["team"],
                     "Season": slot["season"],
                     **season_df[(season_df["Team"] == slot["team"]) & (season_df["Season"] == slot["season"])].iloc[0][["Division","Conference","Rating"]].to_dict()}
                    for slot in st.session_state.team_slots
                    if slot["team"] and slot["season"]
                ]
                if len(sel) < 10:
                    st.warning("Please select at least 10 valid teams before simulating.")
                else:
                    # build divisions & ratings
                    modern_divs = {"Atlantic": [], "Metropolitan": [], "Central": [], "Pacific": []}
                    ratings = {}
                    for ts in sel:
                        uid = f"{ts['RawTeam']} ({ts['Season']})"
                        ratings[uid] = ts["Rating"]
                        div = ts["Division"]
                        if div in modern_divs:
                            modern_divs[div].append(uid)
                        else:
                            modern_divs[min(modern_divs, key=lambda d: len(modern_divs[d]))].append(uid)

                    # simulate
                    with st.spinner("Simulating season…"):
                        stats = simulate_season(modern_divs, ratings)
                    df, auto_flag = build_dataframe(stats, modern_divs, season_df,
                                                    team_to_season_map={ts["RawTeam"]: ts["Season"] for ts in sel})
                    if auto_flag:
                        st.info("Some teams were auto-assigned to balance divisions.")
                    df["Rating"] = df["RawTeam"].map(ratings).fillna(0).astype(int)
                    st.session_state["last_df"] = df

    # ─────────────────────────────────────────────────────────────────────
    # 3) RESULTS
    # ─────────────────────────────────────────────────────────────────────
    with tab_results:
        # league preview
        if st.session_state.show_preview:
            st.subheader("🔍 Custom League Preview")
            divs = {"Atlantic": [], "Metropolitan": [], "Central": [], "Pacific": []}
            for slot in st.session_state.team_slots:
                t, s = slot["team"], slot["season"]
                if t and s:
                    row = season_df[(season_df["Team"]==t)&(season_df["Season"]==s)]
                    d = row.iloc[0]["Division"] if not row.empty else min(divs, key=lambda d: len(divs[d]))
                    divs[d].append(f"{t} ({s})")
            cols = st.columns(2)
            for idx, name in enumerate(["Atlantic","Metropolitan"]):
                with cols[0 if idx==0 else 1]:
                    st.write(f"**{name}**")
                    st.write("\n".join(divs[name]))
            cols = st.columns(2)
            for idx, name in enumerate(["Central","Pacific"]):
                with cols[0 if idx==0 else 1]:
                    st.write(f"**{name}**")
                    st.write("\n".join(divs[name]))

        # standings & playoffs
        if "last_df" in st.session_state:
            df = st.session_state["last_df"]
            st.markdown("---")
            st.subheader("4) View Standings / Playoffs")
            view = st.selectbox("Select View", ["By Division","By Conference","Entire League","Playoffs"], key="view_mode")
            if view != "Playoffs":
                group = "Division" if view=="By Division" else ("Conference" if view=="By Conference" else None)
                table = df if not group else df.sort_values(group)
                table = table.sort_values(by=["PTS","Win%"], ascending=[False,False])
                st.dataframe(table[["Team","GP","W","L","OTL","PTS","Win%"]].reset_index(drop=True), use_container_width=True)
            else:
                if "playoff_bracket" not in st.session_state:
                    with st.spinner("Simulating playoffs…"):
                        r = {row["Team"]: row["Rating"] for _,row in df.iterrows()}
                        st.session_state.playoff_bracket = simulate_playoffs_streamlit(df, r)
                bracket = st.session_state.playoff_bracket
                display_bracket_table_v4(bracket)
                # … you can re-use your detailed checkbox logic here …

                # Save block
                st.markdown("### 💾 Save This Simulation")
                name = st.text_input("Simulation Name", key="save_name")
                if st.button("Save Simulation"):
                    if not name.strip():
                        st.error("Enter a name.")
                    else:
                        email = st.session_state["user"].email
                        teams = [f"{slot['team']} ({slot['season']})" for slot in st.session_state.team_slots]
                        standings = df.to_dict("records")
                        playoffs = bracket
                        exists = supabase.table("simulations") \
                                         .select("*") \
                                         .eq("email", email) \
                                         .eq("name", name) \
                                         .execute().data
                        if exists:
                            st.error("You already have a sim with that name.")
                        else:
                            ts = datetime.datetime.utcnow().isoformat()
                            res = supabase.table("simulations").insert({
                                "email": email, "name": name, "timestamp": ts,
                                "teams": teams, "standings": standings, "playoffs": playoffs
                            }).execute()
                            if res.data:
                                st.success("Saved!")
                            else:
                                st.error("Save failed.")
