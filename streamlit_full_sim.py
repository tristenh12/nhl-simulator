import streamlit as st
import pandas as pd
import random
import os
import datetime

from sim_engine import simulate_season, build_dataframe
from playoff import simulate_playoffs_streamlit, display_bracket_table_v4

def run_full_sim(supabase):
    # ─────────────────────────────────────────────────────────────────
    # 0) PAGE CONFIG & TITLE
    # ─────────────────────────────────────────────────────────────────
    st.title("📅 NHL Full-Season What-If Simulator")
    st.markdown("Fill 32 slots (team + season), simulate an 82-game schedule, then view standings + playoffs.")

    # ─────────────────────────────────────────────────────────────────
    # A) LOAD DATA + INITIALIZE STATE
    # ─────────────────────────────────────────────────────────────────
    @st.cache_data
    def load_season_df():
        here = os.path.dirname(__file__)
        return pd.read_csv(os.path.join(here, "data", "teams_alignment_complete.csv"))

    season_df = load_season_df()
    all_teams = sorted(season_df["Team"].unique())
    available_seasons = sorted(season_df["Season"].unique(), reverse=True)
    default_season = available_seasons[0]

    if "show_preview" not in st.session_state:
        st.session_state.show_preview = False

    if "team_slots" not in st.session_state:
        teams_def = sorted(season_df[season_df["Season"] == default_season]["Team"].unique())
        st.session_state.team_slots = [
            {"team": teams_def[i], "season": default_season} if i < len(teams_def)
            else {"team": "", "season": ""}
            for i in range(32)
        ]

    def get_seasons_for_team(team):
        return sorted(season_df[season_df["Team"] == team]["Season"].unique(), reverse=True) if team else []

    all_valid_pairs = [(r.Team, r.Season) for _, r in season_df.iterrows()]

    # ─────────────────────────────────────────────────────────────────
    # B) INNER TABS: remember active_tab in session_state
    # ─────────────────────────────────────────────────────────────────
    all_tabs = ["1) Team Selector", "2) Tools", "3) Results"]
    if "active_tab" not in st.session_state:
        st.session_state.active_tab = all_tabs[0]
    # reorder so active_tab is first
    ordered = [st.session_state.active_tab] + [t for t in all_tabs if t != st.session_state.active_tab]
    tab_objs = st.tabs(ordered)
    tabs_map = {label: tab for label, tab in zip(ordered, tab_objs)}

    # ─────────────────────────────────────────────────────────────────
    # 1) TEAM SELECTOR
    # ─────────────────────────────────────────────────────────────────
    with tabs_map["1) Team Selector"]:
        st.markdown("### Customize Your 32-Team League")
        if not st.session_state.get("show_all_slots", False):
            if st.button("🔽 Show All 32 Slots"):
                st.session_state.show_all_slots = True
                st.rerun()
        else:
            if st.button("🔼 Collapse to 4 Slots"):
                st.session_state.show_all_slots = False
                st.rerun()

        num_slots = 32 if st.session_state.get("show_all_slots") else 4
        col1, col2 = st.columns(2)
        for i in range(num_slots // 2):
            with col1:
                slot = st.session_state.team_slots[i]
                t = st.selectbox(
                    f"– Team {i+1:02d}", [""] + all_teams,
                    index=(all_teams.index(slot["team"]) + 1) if slot["team"] in all_teams else 0,
                    key=f"team_{i}"
                )
                s = st.selectbox(
                    f"– Season {i+1:02d}", [""] + get_seasons_for_team(t),
                    index=(get_seasons_for_team(t).index(slot["season"]) + 1)
                          if slot["season"] in get_seasons_for_team(t) else 0,
                    key=f"season_{i}"
                )
                st.session_state.team_slots[i] = {"team": t, "season": s}

        for i in range(num_slots // 2, num_slots):
            with col2:
                slot = st.session_state.team_slots[i]
                t = st.selectbox(
                    f"– Team {i+1:02d}", [""] + all_teams,
                    index=(all_teams.index(slot["team"]) + 1) if slot["team"] in all_teams else 0,
                    key=f"team_{i}"
                )
                s = st.selectbox(
                    f"– Season {i+1:02d}", [""] + get_seasons_for_team(t),
                    index=(get_seasons_for_team(t).index(slot["season"]) + 1)
                          if slot["season"] in get_seasons_for_team(t) else 0,
                    key=f"season_{i}"
                )
                st.session_state.team_slots[i] = {"team": t, "season": s}

    # ─────────────────────────────────────────────────────────────────
    # 2) TOOLS
    # ─────────────────────────────────────────────────────────────────
    with tabs_map["2) Tools"]:
        st.markdown("### League-Wide Controls / Load-Save / Run Simulation")

        user_email = st.session_state["user"].email
        sims = supabase.table("simulations")\
                       .select("name, teams")\
                       .eq("email", user_email)\
                       .order("timestamp", desc=True)\
                       .execute().data
        names = [s["name"] for s in sims]

        # Load saved
        sel = st.selectbox("🔁 Load Saved Simulation", [""] + names, key="sel_saved")
        if st.button("📥 Load into Slots"):
            if sel:
                sim = next(s for s in sims if s["name"] == sel)
                new = []
                for t in sim["teams"]:
                    team, yr = t.rsplit(" (", 1)
                    new.append({"team": team, "season": yr.rstrip(")")})
                while len(new) < 32:
                    new.append({"team": "", "season": ""})
                st.session_state.team_slots = new
                st.session_state.active_tab = "1) Team Selector"
                st.rerun()

        # Fill full season
        season_to_fill = st.selectbox(
            "📅 Fill Full Season → Select Season", available_seasons,
            index=available_seasons.index(default_season), key="fill_season"
        )
        if st.button("📅 Fill Full Season"):
            teams_year = sorted(season_df[season_df["Season"] == season_to_fill]["Team"].unique())
            for i in range(32):
                if i < len(teams_year):
                    st.session_state.team_slots[i] = {"team": teams_year[i], "season": season_to_fill}
                else:
                    st.session_state.team_slots[i] = {"team": "", "season": ""}
            st.session_state.active_tab = "1) Team Selector"
            st.rerun()

        # Fill each slot by year
        one_team = st.selectbox("🗓 Fill Each Slot by Team", [""] + all_teams, key="one_team")
        if st.button("🗓 Fill Each Slot by Year"):
            if one_team:
                yrs = sorted(season_df[season_df["Team"] == one_team]["Season"].unique(), reverse=True)
                for i in range(32):
                    if i < len(yrs):
                        st.session_state.team_slots[i] = {"team": one_team, "season": yrs[i]}
                    else:
                        st.session_state.team_slots[i] = {"team": "", "season": ""}
            st.session_state.active_tab = "1) Team Selector"
            st.rerun()

        st.markdown("---")
        st.markdown(
            """<style>div.stButton>button{padding:4px 8px!important;font-size:0.85rem!important;}</style>""",
            unsafe_allow_html=True
        )

        c1, c2, c3, c4 = st.columns(4)
        with c1:
            if st.button("♻ Reset to Default"):
                st.session_state.pop("team_slots", None)
                st.session_state.active_tab = "1) Team Selector"
                st.rerun()
        with c2:
            if st.button("🔀 Randomize All Slots"):
                sample = random.sample(all_valid_pairs, 32)
                st.session_state.team_slots = [{"team": t, "season": s} for t, s in sample]
                st.session_state.active_tab = "1) Team Selector"
                st.rerun()
        with c3:
            if st.button("👀 Toggle Preview"):
                st.session_state.show_preview = not st.session_state.show_preview
                st.rerun()
        with c4:
            if st.button("✅ Run Full-Season Simulation"):
                st.session_state.pop("playoff_bracket", None)
                st.session_state.show_preview = False

                sel = [
                    {
                        "RawTeam": slot["team"],
                        "Season": slot["season"],
                        **season_df[
                            (season_df["Team"] == slot["team"]) &
                            (season_df["Season"] == slot["season"])
                        ].iloc[0][["Division","Conference","Rating"]].to_dict()
                    }
                    for slot in st.session_state.team_slots
                    if slot["team"] and slot["season"]
                ]
                if len(sel) < 10:
                    st.warning("Please select at least 10 valid teams before simulating.")
                else:
                    modern_divs = {"Atlantic":[], "Metropolitan":[], "Central":[], "Pacific":[]}
                    ratings = {}
                    for ts in sel:
                        uid = f"{ts['RawTeam']} ({ts['Season']})"
                        ratings[uid] = ts["Rating"]
                        div = ts["Division"]
                        if div in modern_divs:
                            modern_divs[div].append(uid)
                        else:
                            modern_divs[min(modern_divs, key=lambda d: len(modern_divs[d]))].append(uid)

                    with st.spinner("Simulating season…"):
                        stats = simulate_season(modern_divs, ratings)
                    df, auto_flag = build_dataframe(
                        stats, modern_divs, season_df,
                        team_to_season_map={ts["RawTeam"]: ts["Season"] for ts in sel}
                    )
                    if auto_flag:
                        st.info("Some teams were auto-assigned to balance divisions.")
                    df["Rating"] = df["RawTeam"].map(ratings).fillna(0).astype(int)
                    st.session_state["last_df"] = df

                    # jump to Results
                    st.session_state.active_tab = "3) Results"
                    st.rerun()

        # inline preview
        if st.session_state.show_preview:
            selected = [
                (slot["team"], slot["season"])
                for slot in st.session_state.team_slots
                if slot["team"] and slot["season"]
            ]
            if len(selected) != 32:
                st.warning(f"⚠️ You have filled {len(selected)}/32 slots.")
            else:
                divisions = {"Atlantic":[], "Metropolitan":[], "Central":[], "Pacific":[]}
                for team, y in selected:
                    row = season_df[(season_df["Team"]==team)&(season_df["Season"]==y)]
                    div = (
                        row.iloc[0]["Division"]
                        if not row.empty and row.iloc[0]["Division"] in divisions
                        else min(divisions, key=lambda k: len(divisions[k]))
                    )
                    divisions[div].append(f"{team} ({y})")

                st.subheader("Custom League Preview")
                c1, c2 = st.columns(2)
                with c1:
                    st.write("**Atlantic**");    [st.write(f"- {t}") for t in divisions["Atlantic"]]
                    st.write("**Metropolitan**");[st.write(f"- {t}") for t in divisions["Metropolitan"]]
                with c2:
                    st.write("**Central**");     [st.write(f"- {t}") for t in divisions["Central"]]
                    st.write("**Pacific**");     [st.write(f"- {t}") for t in divisions["Pacific"]]

    # ─────────────────────────────────────────────────────────────────
    # 3) RESULTS
    # ─────────────────────────────────────────────────────────────────
    with tabs_map["3) Results"]:
        if "last_df" in st.session_state:
            df = st.session_state["last_df"]
            st.markdown("---")
            st.subheader("4) View Standings / Playoffs")
            view = st.selectbox(
                "Select View",
                ["By Division","By Conference","Entire League","Playoffs"],
                key="view_mode"
            )
            if view != "Playoffs":
                group = ("Division" if view=="By Division" else
                         "Conference" if view=="By Conference" else None)
                sort_cols = [group,"PTS","Win%"] if group else ["PTS","Win%"]
                tbl = df.sort_values(sort_cols, ascending=[True,False,False])
                st.dataframe(
                    tbl[["Team","GP","W","L","OTL","PTS","Win%"]]
                    .reset_index(drop=True),
                    use_container_width=True
                )
            else:
                if "playoff_bracket" not in st.session_state:
                    with st.spinner("Simulating playoffs…"):
                        ratings = {r["Team"]:r["Rating"] for _,r in df.iterrows()}
                        st.session_state.playoff_bracket = simulate_playoffs_streamlit(df, ratings)
                display_bracket_table_v4(st.session_state.playoff_bracket)

                st.markdown("### 💾 Save This Simulation")
                name = st.text_input("Simulation Name", key="save_name")
                if st.button("Save Simulation"):
                    if not name.strip():
                        st.error("Enter a name.")
                    else:
                        email = st.session_state["user"].email
                        teams = [f"{s['team']} ({s['season']})" for s in st.session_state.team_slots]
                        standings = df.to_dict("records")
                        playoffs = st.session_state.playoff_bracket
                        exists = supabase.table("simulations")\
                                        .select("*")\
                                        .eq("email", email)\
                                        .eq("name", name)\
                                        .execute().data
                        if exists:
                            st.error("You already have a sim with that name.")
                        else:
                            ts = datetime.datetime.utcnow().isoformat()
                            res = supabase.table("simulations").insert({
                                "email": email,
                                "name": name,
                                "timestamp": ts,
                                "teams": teams,
                                "standings": standings,
                                "playoffs": playoffs
                            }).execute()
                            if res.data:
                                st.success("Saved!")
                            else:
                                st.error("Save failed.")
