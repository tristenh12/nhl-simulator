import streamlit as st
import pandas as pd
import time
import re
import random
import os
from free_sim import simulate_one_game, simulate_best_of_7

# Compile period header pattern once
period_pattern = re.compile(r"=== (\d+)(?:st|nd|rd) Period ===")

def run_free_sim():
    st.title("🎮 Free NHL One-Game Simulator")
    st.markdown("Select two teams (and seasons), then simulate a single game or a best-of-7 series.")

    @st.cache_data
    def load_season_df():
        here = os.path.dirname(__file__)
        return pd.read_csv(os.path.join(here, "data", "teams_alignment_complete.csv"))

    season_df = load_season_df()
    teams = sorted(season_df["Team"].unique())

    tab_game, tab_series = st.tabs(["Single Game", "Best of 7 Series"])

    # ─── Single Game Tab ─────────────────────────────────────────────
    with tab_game:
        col1, col2 = st.columns(2)
        with col1:
            # 🎲 Random Team 1
            def pick_rand1():
                st.session_state["game_team1"] = random.choice(teams)
            st.button("🎲 Random Team 1", on_click=pick_rand1, key="btn_rand1_game")

            t1 = st.selectbox("Team 1", [""] + teams, key="game_team1")
            s1_opts = sorted(season_df[season_df["Team"] == t1]["Season"].unique(), reverse=True) if t1 else []
            s1 = st.selectbox("Season 1", s1_opts, key="game_season1")

        with col2:
            # 🎲 Random Team 2
            def pick_rand2():
                st.session_state["game_team2"] = random.choice(teams)
            st.button("🎲 Random Team 2", on_click=pick_rand2, key="btn_rand2_game")

            t2 = st.selectbox("Team 2", [""] + teams, key="game_team2")
            s2_opts = sorted(season_df[season_df["Team"] == t2]["Season"].unique(), reverse=True) if t2 else []
            s2 = st.selectbox("Season 2", s2_opts, key="game_season2")

        if st.button("▶️ Sim One Game", key="btn_sim_game"):
            # clear old game-state keys
            for k in ["game_commentary", "game_stats", "game_full1", "game_full2", "game_box", "game_idx", "game_play"]:
                st.session_state.pop(k, None)

            # validation
            if not (t1 and t2 and s1 and s2):
                st.error("❗ Select both teams and their seasons.")
                st.stop()
            if t1 == t2 and s1 == s2:
                st.error("❗ Cannot simulate a team against itself.")
                st.stop()

            full1 = f"{t1} ({s1})"
            full2 = f"{t2} ({s2})"
            commentary, stats, full_box_df = simulate_one_game(t1, s1, t2, s2)

            # group by period and sort
            time_re = re.compile(r"(\d+):(\d+)")
            def parse_ts(ln):
                m = time_re.search(ln)
                return int(m.group(1)) * 60 + int(m.group(2)) if m else float("inf")

            order, events, current = [], {}, None
            for ln in commentary:
                m = period_pattern.match(ln)
                if m:
                    p = m.group(1)
                    current = p
                    if p not in order:
                        order.append(p)
                    events[p] = []
                elif current:
                    events[current].append(ln)

            sorted_feed = []
            for p in order:
                suffix = {"1":"st","2":"nd","3":"rd"}.get(p,"")
                sorted_feed.append(f"=== {p}{suffix} Period ===")
                sorted_feed.extend(sorted(events[p], key=parse_ts))

            # stash in session_state
            st.session_state["game_commentary"] = sorted_feed
            st.session_state["game_stats"] = stats
            st.session_state["game_full1"] = full1
            st.session_state["game_full2"] = full2
            st.session_state["game_box"] = full_box_df
            st.session_state["game_idx"] = 0
            st.session_state["game_play"] = False
            st.rerun()

        # Live feed / final stats
        if "game_commentary" in st.session_state:
            comm = st.session_state["game_commentary"]
            stats = st.session_state["game_stats"]
            full1 = st.session_state["game_full1"]
            full2 = st.session_state["game_full2"]
            idx = st.session_state["game_idx"]

            speed = st.selectbox("Speed", ["1×","2×","4×"], index=0, key="game_speed")
            delay = {"1×":0.5, "2×":0.25, "4×":0.125}[speed]

            # callbacks for play/pause/skip
            def play_cb():
                st.session_state["game_play"] = True
            def pause_cb():
                st.session_state["game_play"] = False
            def skip_cb():
                st.session_state["game_idx"] = len(comm)

            b1, b2, b3 = st.columns(3)
            with b1:
                st.button("▶ Play", key="btn_play_game", on_click=play_cb)
            with b2:
                st.button("⏸ Pause", key="btn_pause_game", on_click=pause_cb)
            with b3:
                st.button("⏭ Skip to End", key="btn_skip_game", on_click=skip_cb)

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

                if st.button("📊 View Full Box Score", key="btn_box_game"):
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
                    st.dataframe(pd.DataFrame(rows), use_container_width=True)

    # ─── Best of 7 Tab (stateless) ───────────────────────────────────
    with tab_series:
        col1, col2 = st.columns(2)
        with col1:
            def pick_r1s():
                st.session_state["series_team1"] = random.choice(teams)
            st.button("🎲 Random Team 1", on_click=pick_r1s, key="btn_rand1_series")

            t1s = st.selectbox("Team 1", [""] + teams, key="series_team1")
            s1s_opts = sorted(season_df[season_df["Team"] == t1s]["Season"].unique(), reverse=True) if t1s else []
            s1s = st.selectbox("Season 1", s1s_opts, key="series_season1")

        with col2:
            def pick_r2s():
                st.session_state["series_team2"] = random.choice(teams)
            st.button("🎲 Random Team 2", on_click=pick_r2s, key="btn_rand2_series")

            t2s = st.selectbox("Team 2", [""] + teams, key="series_team2")
            s2s_opts = sorted(season_df[season_df["Team"] == t2s]["Season"].unique(), reverse=True) if t2s else []
            s2s = st.selectbox("Season 2", s2s_opts, key="series_season2")

        if st.button("▶️ Sim Best of 7", key="btn_sim_series"):
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

    # ─── Reset Single-Game State Only ────────────────────────────────
    if st.button("🔄 Reset Matchup", key="btn_reset"):
        for k in list(st.session_state.keys()):
            if k.startswith("game_"):
                del st.session_state[k]
        st.rerun()

if __name__ == "__main__":
    run_free_sim()
