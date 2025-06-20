# streamlit_full_sim.py

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
    

    # Two‐column layout: left = intro text + “#top” anchor, right = “Go to Tools” button
    col_main, col_topbtn = st.columns([9, 1])
    with col_main:
        # Anchor for “Back to Top”
        st.markdown("<a id='top'></a>", unsafe_allow_html=True)
        # Intro text beneath the title
        st.markdown("Fill 32 slots (team + season), simulate an 82-game schedule, then view standings + playoffs.")
    with col_topbtn:
        st.markdown(
            """
            <a href="#tools" 
            style="
                display: inline-block;
                padding: 4px 8px;
                font-size: 0.9rem;
                background-color: #fafafa;
                border: 1px solid #ccc;
                border-radius: 4px;
                text-decoration: none;
                color: black;
            ">
            🔧 Go to Tools
            </a>
            """,
            unsafe_allow_html=True,
        )

    # ─────────────────────────────────────────────────────────────────────
    # A) LOAD MASTER CSV + INITIALIZE 32 SLOTS
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

    if "show_preview" not in st.session_state:
        st.session_state.show_preview = False

    # … rest of your code …



    # Build a list of all valid (Team, Season) pairs in the CSV
    all_valid_pairs = [(row.Team, row.Season) for _, row in season_df.iterrows()]

    if "team_slots" not in st.session_state:
        # Pull all teams from the default season (e.g. 2023-24) and fill those into slots 0–<n-1>.
        teams_in_default = sorted(
            season_df[season_df["Season"] == default_season]["Team"].unique()
        )
        slots = []
        for i in range(32):
            if i < len(teams_in_default):
                slots.append({"team": teams_in_default[i], "season": default_season})
            else:
                slots.append({"team": "", "season": ""})
        st.session_state.team_slots = slots


    def get_seasons_for_team(team_name):
        if not team_name:
            return []
        return sorted(season_df[season_df["Team"] == team_name]["Season"].unique(), reverse=True)

    # ──────────────────────────────────────────────────────────────
    # (B) 32-slot pickers (two columns of 16 each), no “Slot” labels
    # ──────────────────────────────────────────────────────────────

    # Inject CSS to reduce vertical spacing (keep the same as before)
    st.markdown(
        """
        <style>
        /* Shrink selectbox widgets: less vertical margin */
        [data-baseweb="select"] {
            margin-top: 2px !important;
            margin-bottom: 2px !important;
        }
        /* Shrink generic markdown blocks if you use them elsewhere */
        .tight-markdown {
            margin-top: 2px;
            margin-bottom: 2px;
        }
        /* Thinner <hr> spacing instead of ### or '---' */
        hr.tight-hr {
            border: none;
            border-top: 1px solid #CCC;
            margin: 4px 0;
        }
        </style>
        """,
        unsafe_allow_html=True
    )


    st.markdown("### 1) Customize Your 32-Team League")

    # Toggle button
    if "show_all_slots" not in st.session_state:
        st.session_state.show_all_slots = False

    if not st.session_state.show_all_slots:
        if st.button("🔽 Show All 32 Slots"):
            st.session_state.show_all_slots = True
            st.rerun()

    # Scrollable wrapper CSS (when collapsed)
    if not st.session_state.show_all_slots:
        st.markdown(
            """
            <style>
            .scroll-box {
                max-height: 500px;
                overflow-y: auto;
                padding-right: 10px;
            }
            </style>
            <div class="scroll-box">
            """,
            unsafe_allow_html=True,
        )

    # How many slots to show
    num_slots = 32 if st.session_state.show_all_slots else 4

    # Render the team + season pickers
    col1, col2 = st.columns(2)
    for i in range(num_slots // 2):
        with col1:
            slot = st.session_state.team_slots[i]
            st.selectbox(
                f"– Team {i+1:02d}",
                [""] + all_teams,
                index=(all_teams.index(slot["team"]) + 1) if slot["team"] in all_teams else 0,
                key=f"team_select_{i}"
            )
            season_options = [""] + get_seasons_for_team(slot["team"])
            st.selectbox(
                f"– Season {i+1:02d}",
                season_options,
                index=season_options.index(slot["season"]) if slot["season"] in season_options else 0,
                key=f"season_select_{i}"
            )
            st.markdown("<hr class='tight-hr' />", unsafe_allow_html=True)

    for i in range(num_slots // 2, num_slots):
        with col2:
            slot = st.session_state.team_slots[i]
            st.selectbox(
                f"– Team {i+1:02d}",
                [""] + all_teams,
                index=(all_teams.index(slot["team"]) + 1) if slot["team"] in all_teams else 0,
                key=f"team_select_{i}"
            )
            season_options = [""] + get_seasons_for_team(slot["team"])
            st.selectbox(
                f"– Season {i+1:02d}",
                season_options,
                index=season_options.index(slot["season"]) if slot["season"] in season_options else 0,
                key=f"season_select_{i}"
            )
            st.markdown("<hr class='tight-hr' />", unsafe_allow_html=True)

    # Close scroll-box div
    if not st.session_state.show_all_slots:
        st.markdown("</div>", unsafe_allow_html=True)

    # Collapse button at bottom
    if st.session_state.show_all_slots:
        if st.button("🔼 Collapse to 4 Slots"):
            st.session_state.show_all_slots = False
            st.rerun()

    # ──────────────────────────────────────────────────────────────────
    # C/D/E) LEAGUE-WIDE CONTROLS (buttons on top row, dropdowns below)
    st.markdown("<a id='tools'></a>", unsafe_allow_html=True)
    # ──────────────────────────────────────────────────────────────────
    st.markdown("### 2) League-Wide Controls / Preview / Run Simulation")
    # (Optional) If you still want smaller buttons, you can keep the CSS snippet:
    st.markdown(
        """
        <style>
        /* Shrink all Streamlit buttons: smaller padding, smaller font, no wrapping */
        div.stButton > button {
            padding: 4px 8px !important;
            font-size: 0.85rem !important;
            white-space: nowrap;
        }
        </style>
        """,
        unsafe_allow_html=True
    )



    # ──────────────────────────────────────────────────────────────────
    # ROW 1: SIX BUTTONS SIDE-BY-SIDE
    # ──────────────────────────────────────────────────────────────────
    b1, b2, b3, b4, b5, b6 = st.columns([1, 1, 1, 1, 1, 1])

    # — Control 1: “Reset to Default (2023-24)”
    with b1:
        if st.button("♻ Reset to Default (2023-24)"):
            teams_in_default = sorted(
                season_df[season_df["Season"] == default_season]["Team"].unique()
            )
            for i in range(32):
                if i < len(teams_in_default):
                    st.session_state.team_slots[i] = {
                        "team":   teams_in_default[i],
                        "season": default_season
                    }
                else:
                    st.session_state.team_slots[i] = {"team": "", "season": ""}
            st.rerun()

    # — Control 2: “Fill Full Season” (button only on this row)
    with b2:
        if st.button("📅 Fill Full Season"):
            # Read the season selected in Row 2, col 2
            season_to_fill = st.session_state.get("full_season_selector", default_season)
            teams_that_year = sorted(
                season_df[season_df["Season"] == season_to_fill]["Team"].unique()
            )
            for i in range(32):
                if i < len(teams_that_year):
                    st.session_state.team_slots[i] = {
                        "team":   teams_that_year[i],
                        "season": season_to_fill
                    }
                else:
                    st.session_state.team_slots[i] = {"team": "", "season": ""}
            st.rerun()

    # — Control 3: “Same Team by Year” (button only on this row)
    with b3:
        if st.button("🗓 Fill Each Slot by Year"):
            t = st.session_state.get("one_team_selector", "")
            if t:
                years = sorted(
                    season_df[season_df["Team"] == t]["Season"].unique(),
                    reverse=True
                )
                for i in range(32):
                    if i < len(years):
                        st.session_state.team_slots[i] = {"team": t, "season": years[i]}
                    else:
                        st.session_state.team_slots[i] = {"team": "", "season": ""}
            st.rerun()

    # — Control 4: “Randomize All Slots”
    with b4:
        if st.button("🔀 Randomize All Slots"):
            if len(all_valid_pairs) >= 32:
                chosen_pairs = random.sample(all_valid_pairs, 32)
            else:
                chosen_pairs = all_valid_pairs.copy()
            for i, (t, se) in enumerate(chosen_pairs):
                st.session_state.team_slots[i] = {"team": t, "season": se}
            st.rerun()

    # — Control 5: “Preview League”
    with b5:
        if st.button("👀 Preview League"):
            st.session_state.show_preview = not st.session_state.show_preview
            st.rerun()

            selected_pairs = [
                (s["team"], s["season"])
                for s in st.session_state.team_slots
                if s["team"] and s["season"]
            ]
            if len(selected_pairs) != 32:
                st.warning(
                    f"⚠️ You have filled {len(selected_pairs)}/32 slots. "
                    "Please fill all 32 to preview."
                )
                st.stop()

            divisions = {"Atlantic": [], "Metropolitan": [], "Central": [], "Pacific": []}
            for (tm, se) in selected_pairs:
                row = season_df[(season_df["Team"] == tm) & (season_df["Season"] == se)]
                if not row.empty:
                    div = row.iloc[0]["Division"]
                    if div not in divisions:
                        div = min(divisions, key=lambda d: len(divisions[d]))
                else:
                    div = min(divisions, key=lambda d: len(divisions[d]))
                divisions[div].append(f"{tm} ({se})")

            st.subheader("=== Custom League Preview (By Division) ===")
            for div_name, teams_list in divisions.items():
                st.write(f"**--- {div_name} ---**")
                for t in teams_list:
                    st.write(f"- {t}")
                st.write(" ")
            st.stop()

    # — Control 6: “Run Full-Season Simulation”
    with b6:
        if st.button("✅ Run Full-Season Simulation"):

                        # (1) Clear old playoff keys so a fresh bracket can be generated later
            if "playoff_bracket" in st.session_state:
                del st.session_state["playoff_bracket"]
            for key in list(st.session_state.keys()):
                if key.startswith("chk_east_") or key.startswith("chk_west_") or key.startswith("chk_final_"):
                    del st.session_state[key]
                    
            selected_teams = []
            team_to_season = {}

            for slot in st.session_state.team_slots:
                t, se = slot["team"], slot["season"]
                if t and se:
                    row = season_df[(season_df["Team"] == t) & (season_df["Season"] == se)]
                    if not row.empty:
                        selected_teams.append({
                            "RawTeam":    t,
                            "Season":     se,
                            "Division":   row.iloc[0]["Division"],
                            "Conference": row.iloc[0]["Conference"],
                            "Rating":     row.iloc[0]["Rating"]
                        })
                        team_to_season[t] = se

            if len(selected_teams) < 10:
                st.warning("⚠️ Please select at least 10 teams (with valid years) before simulating.")
                st.stop()

            # Build modern_divs & ratings_dict
            modern_divs = {"Atlantic": [], "Metropolitan": [], "Central": [], "Pacific": []}
            ratings_dict = {}
            all_raws = set(ts["RawTeam"] for ts in selected_teams)

            if len(all_raws) == 1:
                # Same‐Team‐by‐Year: round‐robin distribute into four divisions
                div_keys = list(modern_divs.keys())
                raw = selected_teams[0]["RawTeam"]
                for idx, ts in enumerate(selected_teams):
                    se = ts["Season"]
                    uid = f"{raw} ({se})"
                    ratings_dict[uid] = ts["Rating"]
                    target_div = div_keys[idx % len(div_keys)]
                    modern_divs[target_div].append(uid)
            else:
                # Normal: match historical division if possible, else defer
                to_auto = []
                for ts in selected_teams:
                    raw, se = ts["RawTeam"], ts["Season"]
                    hist_div = ts["Division"]
                    uid = f"{raw} ({se})"
                    ratings_dict[uid] = ts["Rating"]
                    if hist_div in modern_divs:
                        modern_divs[hist_div].append(uid)
                    else:
                        to_auto.append(uid)
                for uid in to_auto:
                    smallest = min(modern_divs.items(), key=lambda kv: len(kv[1]))[0]
                    modern_divs[smallest].append(uid)

            # Run the 82‐game season
            with st.spinner("Simulating season…"):
                stats = simulate_season(modern_divs, ratings_dict)

            # Build standings DataFrame
            df, auto_flag = build_dataframe(
                stats, modern_divs, season_df, team_to_season_map=team_to_season
            )
            if auto_flag:
                st.info("⚠️ Some teams were auto-assigned to East/West to balance the simulation.\n")

            df["Rating"] = df["RawTeam"].map(ratings_dict).fillna(0).astype(int)
            st.session_state["last_df"] = df

            # ← Add this line to hide preview when simulation runs:
            st.session_state.show_preview = False



    # ──────────────────────────────────────────────────────────────────
    # ROW 2: TWO DROPDOWNS (directly under their buttons) + Back-to-Top
    # ──────────────────────────────────────────────────────────────────
    d1, d2, d3, d4, d5, d6 = st.columns([.8, .6, .2, .6, 2, .6])

    with d1:
        st.write("")  # empty spacer

    with d2:
        st.selectbox(
            "Select a Season → Fill All 32 Slots",
            options=available_seasons,
            index=available_seasons.index(default_season),
            key="full_season_selector",
        )

    with d3:
        st.write("")  # empty spacer


    with d4:
        st.selectbox(
            "Select Team to Fill",
            options=[""] + all_teams,
            key="one_team_selector",
        )

    with d5:
        st.write("")  # empty spacer

    with d6:
        st.markdown(
            """
            <a href="#top" 
            style="
                display: inline-block;
                padding: 4px 8px;
                font-size: 0.9rem;
                background-color: #fafafa;
                border: 1px solid #ccc;
                border-radius: 4px;
                text-decoration: none;
                color: black;
            ">
            ⬆ Back to Top
            </a>
            """,
            unsafe_allow_html=True,
        )



    # ────────────────────────────────────────────────────────────────────
    # (NEW) Preview‐toggle block: 2×2 grid of divisions
    # ────────────────────────────────────────────────────────────────────
    if st.session_state.show_preview:
        # Gather all selected (team, season) pairs:
        selected_pairs = [
            (s["team"], s["season"])
            for s in st.session_state.team_slots
            if s["team"] and s["season"]
        ]

        # If not exactly 32 filled, warn and do nothing else
        if len(selected_pairs) != 32:
            st.warning(
                f"⚠️ You have filled {len(selected_pairs)}/32 slots. "
                "Please fill all 32 to preview."
            )
        else:
            # Build a temporary divisions‐by‐division dictionary:
            divisions = {"Atlantic": [], "Metropolitan": [], "Central": [], "Pacific": []}
            for (tm, se) in selected_pairs:
                row = season_df[(season_df["Team"] == tm) & (season_df["Season"] == se)]
                if not row.empty:
                    div = row.iloc[0]["Division"]
                    if div not in divisions:
                        # If historical division doesn’t match any modern key:
                        div = min(divisions, key=lambda d: len(divisions[d]))
                else:
                    div = min(divisions, key=lambda d: len(divisions[d]))
                divisions[div].append(f"{tm} ({se})")

            # Render the preview in a centered 2×2 grid:
            st.markdown(
                "<h2 style='text-align: center;'>Custom League Preview (By Division)</h2>",
                unsafe_allow_html=True
            )


            div_keys = list(divisions.keys())
            # First row: “Atlantic” & “Metropolitan”
            cols = st.columns([2, 2, 2, 1])
            # cols[0] is a left‐spacer; place divisions in cols[1] and cols[2]; cols[3] is right‐spacer
            with cols[1]:
                st.write(f"{div_keys[0]} ")
                for t in divisions[div_keys[0]]:
                    st.write(f"- {t}")
            with cols[2]:
                st.write(f" {div_keys[1]} ")
                for t in divisions[div_keys[1]]:
                    st.write(f"- {t}")

            # Second row: “Central” & “Pacific”
            cols = st.columns([2, 2, 2, 1])
            with cols[1]:
                st.write(f"{div_keys[2]} ")
                for t in divisions[div_keys[2]]:
                    st.write(f"- {t}")
            with cols[2]:
                st.write(f" {div_keys[3]} ")
                for t in divisions[div_keys[3]]:
                    st.write(f"- {t}")




    # ──────────────────────────────────────────────────────────────────
    # (F) VIEW STANDINGS / PLAYOFFS
    # ──────────────────────────────────────────────────────────────────
    if "last_df" in st.session_state:
        df = st.session_state["last_df"]
        st.markdown("---")
        st.subheader("4) View Standings / Playoffs")

        view_mode = st.selectbox(
            "Select View",
            options=["By Division", "By Conference", "Entire League", "Playoffs"],
            index=0,
        )

        if view_mode == "By Division":
            st.write("### NHL STANDINGS (By Division)")
            for d in df["Division"].unique():
                div_df = (
                    df[df["Division"] == d]
                    .sort_values(by=["PTS", "Win%"], ascending=[False, False])
                    .reset_index(drop=True)
                )
                div_df.index = div_df.index + 1
                display_df = div_df[["Team", "GP", "W", "L", "OTL", "PTS", "Win%"]]
                st.write(f"#### {d}")
                st.dataframe(display_df, use_container_width=True)

        elif view_mode == "By Conference":
            st.write("### NHL STANDINGS (By Conference)")
            for c in df["Conference"].unique():
                conf_df = (
                    df[df["Conference"] == c]
                    .sort_values(by=["PTS", "Win%"], ascending=[False, False])
                    .reset_index(drop=True)
                )
                conf_df.index = conf_df.index + 1
                display_df = conf_df[["Team", "GP", "W", "L", "OTL", "PTS", "Win%"]]
                st.write(f"#### {c}")
                st.dataframe(display_df, use_container_width=True)

        elif view_mode == "Entire League":
            st.write("### NHL STANDINGS (Entire League)")
            league_df = (
                df.sort_values(by=["PTS", "Win%"], ascending=[False, False])
                .reset_index(drop=True)
            )
            league_df.index = league_df.index + 1
            display_df = league_df[["Team", "GP", "W", "L", "OTL", "PTS", "Win%"]]
            st.dataframe(display_df, use_container_width=True)

        else:  # Playoffs
            st.write("### Playoff Bracket")

            # ─── 1) Only generate a brand-new bracket once, then store in session_state ───
            if "playoff_bracket" not in st.session_state:
                # run the simulation exactly once:
                with st.spinner("Simulating playoffs…"):
                    ratings_for_playoffs = {row["Team"]: row["Rating"] for _, row in df.iterrows()}
                    st.session_state.playoff_bracket = simulate_playoffs_streamlit(df, ratings_for_playoffs)

            # Retrieve the same bracket on every rerun:
            bracket = st.session_state.playoff_bracket
            display_bracket_table_v4(bracket)

            # ────────────────────────────────────────────────────────────────────
            # 2) Now create one checkbox per series in fixed bracket order.
            #    If a series‐checkbox is checked, show its details.
            # ────────────────────────────────────────────────────────────────────

            # … (earlier code that simulates and displays bracket) …

            # ─────────────────────────────────────────────────────────────────
            # Series Details (East on the left, West on the right)
            # ─────────────────────────────────────────────────────────────────
            st.markdown("---")
            st.subheader("Series Details (click to reveal)")

            # Create two side‐by‐side columns:
            spacer_left, col_east, col_west, spacer_right = st.columns([2, 2, 2, 2])

            # ─── Eastern Conference Series ─────────────────────────────────
            with col_east:
                st.write("#### Eastern Conference")
                for rnd_idx, east_round in enumerate(bracket["east"], start=1):
                    for series_idx, m in enumerate(east_round, start=1):
                        key = f"chk_east_{rnd_idx}_{series_idx}"
                        label = f"East R{rnd_idx} – {m['home']} vs {m['away']}"
                        if key not in st.session_state:
                            st.session_state[key] = False
                        checked = st.checkbox(label, key=key)
                        if checked:
                            wins = m["wins"]
                            winner = m["winner"]
                            st.write(
                                f"• Result → {m['home']} ({wins[m['home']]}) vs "
                                f"{m['away']} ({wins[m['away']]}) → 🏆 **{winner}**"
                            )
                            log_lines = m.get("log", [])
                            if log_lines:
                                st.write("  Game-by-game winners:")
                                for g, w in enumerate(log_lines, start=1):
                                    st.write(f"   – Game {g}: {w}")
                            st.markdown("")  # small gap

            # ─── Western Conference Series ─────────────────────────────────
            with col_west:
                st.write("#### Western Conference")
                for rnd_idx, west_round in enumerate(bracket["west"], start=1):
                    for series_idx, m in enumerate(west_round, start=1):
                        key = f"chk_west_{rnd_idx}_{series_idx}"
                        label = f"West R{rnd_idx} – {m['home']} vs {m['away']}"
                        if key not in st.session_state:
                            st.session_state[key] = False
                        checked = st.checkbox(label, key=key)
                        if checked:
                            wins = m["wins"]
                            winner = m["winner"]
                            st.write(
                                f"• Result → {m['home']} ({wins[m['home']]}) vs "
                                f"{m['away']} ({wins[m['away']]}) → 🏆 **{winner}**"
                            )
                            log_lines = m.get("log", [])
                            if log_lines:
                                st.write("  Game-by-game winners:")
                                for g, w in enumerate(log_lines, start=1):
                                    st.write(f"   – Game {g}: {w}")
                            st.markdown("")  # small gap

            # ─── Stanley Cup Final (put it underneath both columns, centered) ─────────────────────
            st.markdown("<br>", unsafe_allow_html=True)

            # Re-use those four columns, putting the Final in the middle two units:
            _, final_center, _, _ = st.columns([6, 3, 1, 6])
            with final_center:
                st.write("#### Stanley Cup Final")

                final_series = bracket["final"][0]
                key = "chk_final_1_1"
                label = f"Final – {final_series['home']} vs {final_series['away']}"
                if key not in st.session_state:
                    st.session_state[key] = False
                checked = st.checkbox(label, key=key)

                if checked:
                    wins = final_series["wins"]
                    winner = final_series["winner"]
                    st.write(
                        f"• Result → {final_series['home']} ({wins[final_series['home']]}) vs "
                        f"{final_series['away']} ({wins[final_series['away']]}) → 🏆 **{winner}**"
                    )
                    log_lines = final_series.get("log", [])
                    if log_lines:
                        st.write("  Game-by-game winners:")
                        for g, w in enumerate(log_lines, start=1):
                            st.write(f"   – Game {g}: {w}")
                    st.markdown("")  # ← Paste after this, same indentation as above

                # 💾 Save block starts here (same indentation level as `if checked:`)
                if "last_df" in st.session_state and st.session_state["last_df"] is not None:
                    st.markdown("### 💾 Save This Simulation")
                    sim_name = st.text_input("Simulation Name")
                    if st.button("Save Simulation"):
                        user_email = st.session_state["user"].email
                        team_slots = [f"{slot['team']} ({slot['season']})" for slot in st.session_state["team_slots"]]
                        standings = st.session_state["last_df"].to_dict(orient="records")
                        playoffs = st.session_state.get("playoff_bracket", None)

                        if sim_name.strip() == "":
                            st.error("Please enter a name.")
                        else:
                            existing = supabase.table("simulations").select("*").eq("email", user_email).eq("name", sim_name).execute()
                            if existing.data:
                                st.error("You already saved a simulation with this name.")
                            else:
                                timestamp = datetime.datetime.utcnow().isoformat()
                                result = supabase.table("simulations").insert({
                                    "email": user_email,
                                    "name": sim_name,
                                    "timestamp": timestamp,
                                    "teams": team_slots,
                                    "standings": standings,
                                    "playoffs": playoffs
                                }).execute()
                                if result.data:
                                    st.success("Simulation saved successfully!")
                                else:
                                    st.error("Something went wrong saving the simulation.")
