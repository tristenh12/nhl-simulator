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

    if "team_slots" not in st.session_state:
        teams_def = sorted(season_df[season_df["Season"] == default_season]["Team"].unique())
        st.session_state.team_slots = [
            {"team": teams_def[i], "season": default_season} if i < len(teams_def) else {"team": "", "season": ""}
            for i in range(32)
        ]
    if "show_preview" not in st.session_state:
        st.session_state.show_preview = False
    if "active_tab" not in st.session_state:
        st.session_state.active_tab = "teams"

    def seasons_for(team):
        return sorted(season_df[season_df["Team"] == team]["Season"].unique(), reverse=True) if team else []

    all_valid_pairs = [(r.Team, r.Season) for _, r in season_df.iterrows()]

    # ─────────────────────────────────────────────────────────────────
    # B) DRAW TAB BAR
    # ─────────────────────────────────────────────────────────────────
    t1, t2, t3 = st.columns([1,1,1])
    with t1:
        if st.button("1) Team Selector"):
            st.session_state.active_tab = "teams"
    with t2:
        if st.button("2) Tools"):
            st.session_state.active_tab = "tools"
    with t3:
        if st.button("3) Results"):
            st.session_state.active_tab = "results"
    st.markdown("---")

    # ─────────────────────────────────────────────────────────────────
    # 1) TEAM SELECTOR
    # ─────────────────────────────────────────────────────────────────
    if st.session_state.active_tab == "teams":
        st.markdown("## Customize Your 32-Team League")
        # toggle show all / collapse
        if not st.session_state.get("show_all_slots", False):
            if st.button("🔽 Show All 32 Slots"):
                st.session_state.show_all_slots = True
        else:
            if st.button("🔼 Collapse to 4 Slots"):
                st.session_state.show_all_slots = False

        num = 32 if st.session_state.get("show_all_slots") else 4
        colA, colB = st.columns(2)
        for i in range(num//2):
            with colA:
                slot = st.session_state.team_slots[i]
                t = st.selectbox(f"– Team {i+1}", [""]+all_teams,
                                 index=(all_teams.index(slot["team"])+1) if slot["team"] in all_teams else 0,
                                 key=f"team_{i}")
                s = st.selectbox(f"  Season", [""]+seasons_for(t),
                                 index=(seasons_for(t).index(slot["season"])+1)
                                       if slot["season"] in seasons_for(t) else 0,
                                 key=f"season_{i}")
                st.session_state.team_slots[i] = {"team": t, "season": s}
        for i in range(num//2, num):
            with colB:
                slot = st.session_state.team_slots[i]
                t = st.selectbox(f"– Team {i+1}", [""]+all_teams,
                                 index=(all_teams.index(slot["team"])+1) if slot["team"] in all_teams else 0,
                                 key=f"team_{i}")
                s = st.selectbox(f"  Season", [""]+seasons_for(t),
                                 index=(seasons_for(t).index(slot["season"])+1)
                                       if slot["season"] in seasons_for(t) else 0,
                                 key=f"season_{i}")
                st.session_state.team_slots[i] = {"team": t, "season": s}

    # ─────────────────────────────────────────────────────────────────
    # 2) TOOLS
    # ─────────────────────────────────────────────────────────────────
    if st.session_state.active_tab == "tools":
        st.markdown("## League-Wide Controls / Load-Save / Run Simulation")

        # Load saved
        user_email = st.session_state["user"].email
        sims = (supabase.table("simulations")
                        .select("name, teams")
                        .eq("email", user_email)
                        .order("timestamp", desc=True)
                        .execute().data)
        names = [s["name"] for s in sims]
        sel = st.selectbox("🔁 Load Saved Simulation", [""]+names, key="sel_saved")
        if st.button("📥 Load into Slots"):
            if sel:
                sim = next(x for x in sims if x["name"] == sel)
                new = []
                for t in sim["teams"]:
                    tm, yr = t.rsplit(" (",1)
                    new.append({"team": tm, "season": yr.rstrip(")")})
                while len(new)<32:
                    new.append({"team":"", "season":""})
                st.session_state.team_slots = new
                st.session_state.active_tab="teams"
                st.rerun()

        # Fill full season
        sf = st.selectbox("📅 Fill Full Season → Select Season", available_seasons,
                          index=available_seasons.index(default_season), key="sf")
        if st.button("📅 Fill Full Season"):
            year_teams = sorted(season_df[season_df["Season"]==sf]["Team"].unique())
            for i in range(32):
                if i < len(year_teams):
                    st.session_state.team_slots[i] = {"team":year_teams[i],"season":sf}
                else:
                    st.session_state.team_slots[i] = {"team":"","season":""}
            st.session_state.active_tab="teams"
            st.rerun()

        # Fill each slot by year
        ot = st.selectbox("🗓 Fill Each Slot by Team", [""]+all_teams, key="ot")
        if st.button("🗓 Fill Each Slot by Year"):
            if ot:
                yrs = sorted(season_df[season_df["Team"]==ot]["Season"].unique(), reverse=True)
                for i in range(32):
                    if i<len(yrs):
                        st.session_state.team_slots[i] = {"team":ot,"season":yrs[i]}
                    else:
                        st.session_state.team_slots[i] = {"team":"","season":""}
            st.session_state.active_tab="teams"
            st.rerun()

        st.markdown("---")
        st.markdown(
            "<style>div.stButton>button{padding:4px 8px!important;font-size:0.85rem!important;}</style>",
            unsafe_allow_html=True
        )
        c1,c2,c3,c4 = st.columns(4)
        with c1:
            if st.button("♻ Reset to Default"):
                st.session_state.pop("team_slots",None)
                st.session_state.active_tab="teams"
                st.rerun()
        with c2:
            if st.button("🔀 Randomize All Slots"):
                sample = random.sample(all_valid_pairs,32)
                st.session_state.team_slots=[{"team":t,"season":s} for t,s in sample]
                st.session_state.active_tab="teams"
                st.rerun()
        with c3:
            if st.button("👀 Toggle Preview"):
                st.session_state.show_preview = not st.session_state.show_preview
                st.rerun()
        with c4:
            if st.button("✅ Run Full-Season Simulation"):
                st.session_state.pop("playoff_bracket",None)
                st.session_state.show_preview=False

                sel = [
                    {
                        "RawTeam":slot["team"], "Season":slot["season"],
                        **season_df[
                            (season_df["Team"]==slot["team"]) &
                            (season_df["Season"]==slot["season"])
                        ].iloc[0][["Division","Conference","Rating"]].to_dict()
                    }
                    for slot in st.session_state.team_slots
                    if slot["team"] and slot["season"]
                ]
                if len(sel)<10:
                    st.warning("Please select at least 10 valid teams.")
                else:
                    modern_divs={"Atlantic":[],"Metropolitan":[],"Central":[],"Pacific":[]}
                    ratings={}
                    for ts in sel:
                        uid=f"{ts['RawTeam']} ({ts['Season']})"
                        ratings[uid]=ts["Rating"]
                        d=ts["Division"]
                        if d in modern_divs:
                            modern_divs[d].append(uid)
                        else:
                            modern_divs[min(modern_divs, key=lambda k:len(modern_divs[k]))].append(uid)
                    with st.spinner("Simulating…"):
                        stats=simulate_season(modern_divs,ratings)
                    df,af=build_dataframe(stats,modern_divs,season_df,
                                          team_to_season_map={ts["RawTeam"]:ts["Season"] for ts in sel})
                    if af:
                        st.info("Some teams auto-assigned.")
                    df["Rating"]=df["RawTeam"].map(ratings).fillna(0).astype(int)
                    st.session_state["last_df"]=df

                    st.session_state.active_tab="results"
                    st.rerun()

        # inline preview in Tools
        if st.session_state.show_preview:
            selected=[(s["team"],s["season"]) for s in st.session_state.team_slots if s["team"] and s["season"]]
            if len(selected)!=32:
                st.warning(f"⚠️ You have filled {len(selected)}/32 slots.")
            else:
                divs={"Atlantic":[],"Metropolitan":[],"Central":[],"Pacific":[]}
                for tm,yr in selected:
                    row=season_df[(season_df["Team"]==tm)&(season_df["Season"]==yr)]
                    d=row.iloc[0]["Division"] if not row.empty and row.iloc[0]["Division"] in divs else min(divs,key=lambda k:len(divs[k]))
                    divs[d].append(f"{tm} ({yr})")
                st.subheader("Custom League Preview")
                cA,cB=st.columns(2)
                with cA:
                    st.write("**Atlantic**");    [st.write(f"- {t}") for t in divs["Atlantic"]]
                    st.write("**Metropolitan**");[st.write(f"- {t}") for t in divs["Metropolitan"]]
                with cB:
                    st.write("**Central**");     [st.write(f"- {t}") for t in divs["Central"]]
                    st.write("**Pacific**");     [st.write(f"- {t}") for t in divs["Pacific"]]

    # ─────────────────────────────────────────────────────────────────
    # 3) RESULTS
    # ─────────────────────────────────────────────────────────────────
    if st.session_state.active_tab == "results":
        if "last_df" not in st.session_state:
            st.info("No simulation run yet.")
            return

        df = st.session_state["last_df"]
        st.markdown("---")
        st.subheader("4) View Standings / Playoffs")
        view = st.selectbox("Select View",
                            ["By Division", "By Conference", "Entire League", "Playoffs"],
                            key="view_mode")

        # — By Division
        if view == "By Division":
            st.write("### NHL STANDINGS (By Division)")
            for d in df["Division"].unique():
                div_df = (
                    df[df["Division"] == d]
                      .sort_values(by=["PTS", "Win%"], ascending=[False, False])
                      .reset_index(drop=True)
                )
                div_df.index += 1
                st.write(f"#### {d}")
                st.dataframe(div_df[["Team","GP","W","L","OTL","PTS","Win%"]], use_container_width=True)

        # — By Conference
        elif view == "By Conference":
            st.write("### NHL STANDINGS (By Conference)")
            for c in df["Conference"].unique():
                conf_df = (
                    df[df["Conference"] == c]
                      .sort_values(by=["PTS", "Win%"], ascending=[False, False])
                      .reset_index(drop=True)
                )
                conf_df.index += 1
                st.write(f"#### {c}")
                st.dataframe(conf_df[["Team","GP","W","L","OTL","PTS","Win%"]], use_container_width=True)

        # — Entire League
        elif view == "Entire League":
            st.write("### NHL STANDINGS (Entire League)")
            league_df = (
                df.sort_values(by=["PTS", "Win%"], ascending=[False, False])
                  .reset_index(drop=True)
            )
            league_df.index += 1
            st.dataframe(league_df[["Team","GP","W","L","OTL","PTS","Win%"]], use_container_width=True)

        # — Playoffs
        else:
            st.write("### Playoff Bracket")
            if "playoff_bracket" not in st.session_state:
                with st.spinner("Simulating playoffs…"):
                    ratings_for_playoffs = {row["Team"]: row["Rating"] for _, row in df.iterrows()}
                    st.session_state.playoff_bracket = simulate_playoffs_streamlit(df, ratings_for_playoffs)

            bracket = st.session_state["playoff_bracket"]
            display_bracket_table_v4(bracket)

            st.markdown("---")
            st.subheader("Series Details (click to reveal)")

            # Eastern Conference
            ec, wc = st.columns(2)
            with ec:
                st.write("#### Eastern Conference")
                for rnd_idx, round_series in enumerate(bracket["east"], start=1):
                    for sidx, m in enumerate(round_series, start=1):
                        key = f"chk_east_{rnd_idx}_{sidx}"
                        if key not in st.session_state:
                            st.session_state[key] = False
                        if st.checkbox(f"East R{rnd_idx} – {m['home']} vs {m['away']}", key=key):
                            wins, winner = m["wins"], m["winner"]
                            st.write(f"• Result → {m['home']} ({wins[m['home']]}) vs {m['away']} ({wins[m['away']]}) → **{winner}**")
                            for g, w in enumerate(m.get("log", []), start=1):
                                st.write(f"   – Game {g}: {w}")

            # Western Conference
            with wc:
                st.write("#### Western Conference")
                for rnd_idx, round_series in enumerate(bracket["west"], start=1):
                    for sidx, m in enumerate(round_series, start=1):
                        key = f"chk_west_{rnd_idx}_{sidx}"
                        if key not in st.session_state:
                            st.session_state[key] = False
                        if st.checkbox(f"West R{rnd_idx} – {m['home']} vs {m['away']}", key=key):
                            wins, winner = m["wins"], m["winner"]
                            st.write(f"• Result → {m['home']} ({wins[m['home']]}) vs {m['away']} ({wins[m['away']]}) → **{winner}**")
                            for g, w in enumerate(m.get("log", []), start=1):
                                st.write(f"   – Game {g}: {w}")

            # Stanley Cup Final
            st.markdown("<br>", unsafe_allow_html=True)
            _, center, _ = st.columns([1,2,1])
            with center:
                st.write("#### Stanley Cup Final")
                final = bracket["final"][0]
                key = "chk_final_1_1"
                if key not in st.session_state:
                    st.session_state[key] = False
                if st.checkbox(f"Final – {final['home']} vs {final['away']}", key=key):
                    wins, winner = final["wins"], final["winner"]
                    st.write(f"• Result → {final['home']} ({wins[final['home']]}) vs {final['away']} ({wins[final['away']]}) → **{winner}**")
                    for g, w in enumerate(final.get("log", []), start=1):
                        st.write(f"   – Game {g}: {w}")
