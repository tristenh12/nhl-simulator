import streamlit as st
import pandas as pd
import time
import re
import random
from free_sim import simulate_one_game, simulate_best_of_7
import os

# Compile period header pattern once
period_pattern = re.compile(r"=== (\d+)(?:st|nd|rd) Period ===")

def run_free_sim():
    st.title("🎮 Free NHL One-Game Simulator")
    st.markdown("Select two teams (and seasons), then simulate a single game or a best-of-7 series.")

    @st.cache_data
    def load_season_df():
        here = os.path.dirname(__file__)
        data_path = os.path.join(here, "data", "teams_alignment_complete.csv")
        return pd.read_csv(data_path)

    season_df = load_season_df()
    teams = sorted(season_df["Team"].unique())

    tab_game, tab_series = st.tabs(["Single Game", "Best of 7 Series"])

    # ─── Single Game Tab ─────────────────────────────────────────────
    with tab_game:
        col1, col2 = st.columns(2)
        with col1:
            t1 = st.selectbox("Team 1", [""] + teams, key="game_team1")
            if st.button("🎲 Random Team 1", key="game_rand1"):
                st.session_state["game_team1"] = random.choice(teams)
            s1 = st.selectbox(
                "Season 1",
                sorted(season_df[season_df["Team"] == t1]["Season"].unique(), reverse=True)
                if t1 else [],
                key="game_season1"
            )
        with col2:
            t2 = st.selectbox("Team 2", [""] + teams, key="game_team2")
            if st.button("🎲 Random Team 2", key="game_rand2"):
                st.session_state["game_team2"] = random.choice(teams)
            s2 = st.selectbox(
                "Season 2",
                sorted(season_df[season_df["Team"] == t2]["Season"].unique(), reverse=True)
                if t2 else [],
                key="game_season2"
            )

        if st.button("▶️ Sim One Game", key="game_sim"):
            # validate inputs
            if not (t1 and t2 and s1 and s2):
                st.error("❗ Select both teams and their seasons.")
                st.stop()
            if t1 == t2 and s1 == s2:
                st.error("❗ Cannot simulate a team against itself.")
                st.stop()

            full1 = f"{t1} ({s1})"
            full2 = f"{t2} ({s2})"
            commentary, stats, full_box_df = simulate_one_game(t1, s1, t2, s2)

            # group commentary by period & sort
            ts_match = re.compile(r"(\d+):(\d+)")
            def parse_ts(ln):
                m = ts_match.search(ln)
                return int(m.group(1))*60 + int(m.group(2)) if m else float('inf')

            period_order = []
            period_events = {}
            current = None
            for ln in commentary:
                m = period_pattern.match(ln)
                if m:
                    p = m.group(1)
                    current = p
                    if p not in period_order:
                        period_order.append(p)
                    period_events[p] = []
                elif current:
                    period_events[current].append(ln)

            commentary_sorted = []
            for p in period_order:
                suffix = { '1':'st','2':'nd','3':'rd' }.get(p,'')
                commentary_sorted.append(f"=== {p}{suffix} Period ===")
                commentary_sorted.extend(sorted(period_events[p], key=parse_ts))

            # stash in session
            st.session_state["game_commentary"] = commentary_sorted
            st.session_state["game_stats"] = stats
            st.session_state["game_full1"] = full1
            st.session_state["game_full2"] = full2
            st.session_state["game_box"] = full_box_df
            st.session_state["game_idx"] = 0
            st.session_state["game_play"] = False
            st.rerun()

        # live feed + controls
        if "game_commentary" in st.session_state:
            comm = st.session_state["game_commentary"]
            stats = st.session_state["game_stats"]
            full1 = st.session_state["game_full1"]
            full2 = st.session_state["game_full2"]
            idx = st.session_state["game_idx"]

            speed = st.selectbox("Speed", ["1×","2×","4×"], index=0, key="game_speed")
            delay_map = {"1×":.5, "2×":.25, "4×":.125}
            delay = delay_map[speed]

            p1,p2,p3 = st.columns(3)
            with p1:
                if st.button("▶ Play", key="game_play"):
                    st.session_state["game_play"] = True
            with p2:
                if st.button("⏸ Pause", key="game_pause"):
                    st.session_state["game_play"] = False
            with p3:
                if st.button("⏭ Skip to End", key="game_skip"):
                    st.session_state["game_idx"] = len(comm)

            st.subheader(f"{full1} vs {full2} — Live Feed")
            st.text("\n".join(comm[max(0, idx-10):idx]))

            if st.session_state["game_play"] and idx < len(comm):
                time.sleep(delay)
                st.session_state["game_idx"] += 1
                st.rerun()

            if idx >= len(comm):
                st.markdown("---")
                st.subheader("Final Stats")
                st.text(f"FINAL SCORE: {full1} {stats[full1]['Goals']} – {stats[full2]['Goals']} {full2}")
                st.text(f"SHOTS: {stats[full1]['Shots']} – {stats[full2]['Shots']}")
                st.text(f"HITS: {stats[full1]['Hits']} – {stats[full2]['Hits']}")
                st.text(f"PIM: {stats[full1]['PIM']} – {stats[full2]['PIM']}")
                st.text(f"PPG/PP: {stats[full1]['PPG']}/{stats[full1]['PP']} – {stats[full2]['PPG']}/{stats[full2]['PP']}")
                st.text(f"POSSESSION: {stats[full1]['Possession']} – {stats[full2]['Possession']}")

                if st.button("📊 View Full Box Score", key="game_box"):
                    rows = []
                    for ln in comm:
                        if period_pattern.match(ln):
                            rows.append({"Time": ln, "Team": "", "Event": ""})
                        elif " – " in ln:
                            time_str, rest = ln.split(" – ", 1)
                            if ": " in rest:
                                tm, ev = rest.split(": ", 1)
                            else:
                                tm, ev = rest, ""
                            rows.append({"Time": time_str, "Team": tm, "Event": ev})
                        else:
                            rows.append({"Time": "", "Team": "", "Event": ln})
                    df = pd.DataFrame(rows)
                    st.dataframe(df, use_container_width=True)

    # ─── Best of 7 Tab ───────────────────────────────────────────────
    with tab_series:
        col1, col2 = st.columns(2)
        with col1:
            t1s = st.selectbox("Team 1", [""] + teams, key="series_team1")
            if st.button("🎲 Random Team 1", key="series_rand1"):
                st.session_state["series_team1"] = random.choice(teams)
            s1s = st.selectbox(
                "Season 1",
                sorted(season_df[season_df["Team"] == t1s]["Season"].unique(), reverse=True)
                if t1s else [],
                key="series_season1"
            )
        with col2:
            t2s = st.selectbox("Team 2", [""] + teams, key="series_team2")
            if st.button("🎲 Random Team 2", key="series_rand2"):
                st.session_state["series_team2"] = random.choice(teams)
            s2s = st.selectbox(
                "Season 2",
                sorted(season_df[season_df["Team"] == t2s]["Season"].unique(), reverse=True)
                if t2s else [],
                key="series_season2"
            )

        if st.button("▶️ Sim Best of 7", key="series_sim"):
            if not (t1s and t2s and s1s and s2s):
                st.error("❗ Select both teams and their seasons.")
                st.stop()
            if t1s == t2s and s1s == s2s:
                st.error("❗ Cannot simulate a team against itself.")
                st.stop()

            full1s = f"{t1s} ({s1s})"
            full2s = f"{t2s} ({s2s})"
            wins, logs = simulate_best_of_7(t1s, s1s, t2s, s2s)

            st.subheader("🔁 Best-of-7 Results")
            st.text(f"{full1s}: {wins[full1s]} wins")
            st.text(f"{full2s}: {wins[full2s]} wins")
            champ = full1s if wins[full1s] == 4 else full2s
            st.success(f"🏆 {champ}")

            st.markdown("---")
            st.subheader("Game Logs")
            for g in logs:
                st.write(g)

    # ─── Reset Matchup (only clears Single Game state) ────────────
    if st.button("🔄 Reset Matchup", key="reset"):
        for k in list(st.session_state.keys()):
            if k.startswith("game_"):
                st.session_state.pop(k)
        st.rerun()

if __name__ == "__main__":
    run_free_sim()
