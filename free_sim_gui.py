import streamlit as st
import pandas as pd
import time
import re
import random
from free_sim import simulate_one_game, simulate_best_of_7
import os

# Compile period header pattern at module level for reuse
period_pattern = re.compile(r"=== (\d+)(?:st|nd|rd) Period ===")

def run_free_sim():
    """
    Free NHL One-Game / Best-of-7 Simulator.
    """
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

    # ─── Single-Game Tab ─────────────────────────────────────────────
    with tab_game:
        col1, col2 = st.columns(2)
        with col1:
            def pick_rand1_game():
                t = random.choice(teams)
                st.session_state["game_team1"] = t
                seasons = sorted(
                    season_df[season_df["Team"] == t]["Season"].unique(),
                    reverse=True
                )
                if seasons:
                    st.session_state["game_season1"] = random.choice(seasons)
            st.button("🎲 Random Team + Season 1", on_click=pick_rand1_game, key="btn_rand1_game")

            t1 = st.selectbox("Team 1", [""] + teams, key="game_team1")
            s1 = st.selectbox(
                "Season 1",
                sorted(season_df[season_df["Team"] == t1]["Season"].unique(), reverse=True)
                if t1 else [],
                key="game_season1"
            )

        with col2:
            def pick_rand2_game():
                t = random.choice(teams)
                st.session_state["game_team2"] = t
                seasons = sorted(
                    season_df[season_df["Team"] == t]["Season"].unique(),
                    reverse=True
                )
                if seasons:
                    st.session_state["game_season2"] = random.choice(seasons)
            st.button("🎲 Random Team + Season 2", on_click=pick_rand2_game, key="btn_rand2_game")

            t2 = st.selectbox("Team 2", [""] + teams, key="game_team2")
            s2 = st.selectbox(
                "Season 2",
                sorted(season_df[season_df["Team"] == t2]["Season"].unique(), reverse=True)
                if t2 else [],
                key="game_season2"
            )

        # simulate one game
        if st.button("▶️ Sim One Game", key="btn_one_game"):
            # clear any previous game-run state
            for k in list(st.session_state.keys()):
                if k.startswith("game_"):
                    st.session_state.pop(k)
            # re-read after clear
            t1 = st.session_state.get("game_team1", "")
            t2 = st.session_state.get("game_team2", "")
            s1 = st.session_state.get("game_season1", "")
            s2 = st.session_state.get("game_season2", "")

            if not (t1 and t2 and s1 and s2):
                st.error("❗ Select both teams and their seasons.")
                st.stop()
            if t1 == t2 and s1 == s2:
                st.error("❗ Cannot simulate a team against itself.")
                st.stop()

            full1 = f"{t1} ({s1})"
            full2 = f"{t2} ({s2})"
            commentary, stats, full_box_df = simulate_one_game(t1, s1, t2, s2)

            # sort commentary by period and timestamp
            ts_match = re.compile(r"(\d+):(\d+)")
            def parse_ts(ln):
                m = ts_match.search(ln)
                return int(m.group(1)) * 60 + int(m.group(2)) if m else float('inf')

            period_order, period_events, current = [], {}, None
            for ln in commentary:
                if period_pattern.match(ln):
                    p = period_pattern.match(ln).group(1)
                    current = p
                    if p not in period_order:
                        period_order.append(p)
                        period_events[p] = []
                elif current:
                    period_events[current].append(ln)

            commentary_sorted = []
            for p in period_order:
                suffix = 'st' if p=='1' else 'nd' if p=='2' else 'rd' if p=='3' else ''
                commentary_sorted.append(f"=== {p}{suffix} Period ===")
                commentary_sorted.extend(sorted(period_events[p], key=parse_ts))

            # stash into session state
            st.session_state["game_commentary"] = commentary_sorted
            st.session_state["game_stats"] = stats
            st.session_state["game_full1"] = full1
            st.session_state["game_full2"] = full2
            st.session_state["game_full_box_df"] = full_box_df
            st.session_state["game_feed_idx"] = 0
            st.session_state["game_playing"] = False
            st.experimental_rerun()

        # live feed + final stats
        if "game_commentary" in st.session_state:
            comm = st.session_state["game_commentary"]
            stats = st.session_state["game_stats"]
            full1 = st.session_state["game_full1"]
            full2 = st.session_state["game_full2"]
            idx = st.session_state["game_feed_idx"]

            speed = st.selectbox("Speed", ["1×","2×","4×"], index=0, key="game_speed")
            delay_map = {"1×":.5, "2×":.25, "4×":.125}

            p1, p2, p3 = st.columns(3)
            with p1:
                if st.button("▶ Play", key="game_play"):
                    st.session_state["game_playing"] = True
            with p2:
                if st.button("⏸ Pause", key="game_pause"):
                    st.session_state["game_playing"] = False
            with p3:
                if st.button("⏭ Skip to End", key="game_skip"):
                    st.session_state["game_feed_idx"] = len(comm)

            st.subheader(f"{full1} vs {full2} — Live Feed")
            st.text("\n".join(comm[max(0, idx-10):idx]))

            if st.session_state["game_playing"] and idx < len(comm):
                time.sleep(delay_map[speed])
                st.session_state["game_feed_idx"] += 1
                st.experimental_rerun()

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
                                team_part, ev_part = rest.split(": ", 1)
                            else:
                                team_part, ev_part = rest, ""
                            rows.append({"Time": time_str, "Team": team_part, "Event": ev_part})
                        else:
                            rows.append({"Time": "", "Team": "", "Event": ln})
                    df_display = pd.DataFrame(rows)
                    st.dataframe(df_display, use_container_width=True)


    # ─── Best-of-7 Tab ───────────────────────────────────────────────
    with tab_series:
        col1, col2 = st.columns(2)
        with col1:
            def pick_rand1_series():
                t = random.choice(teams)
                st.session_state["series_team1"] = t
                seasons = sorted(
                    season_df[season_df["Team"] == t]["Season"].unique(),
                    reverse=True
                )
                if seasons:
                    st.session_state["series_season1"] = random.choice(seasons)
            st.button("🎲 Random Team + Season 1", on_click=pick_rand1_series, key="btn_rand1_series")

            t1s = st.selectbox("Team 1", [""] + teams, key="series_team1")
            s1s = st.selectbox(
                "Season 1",
                sorted(season_df[season_df["Team"] == t1s]["Season"].unique(), reverse=True)
                if t1s else [],
                key="series_season1"
            )

        with col2:
            def pick_rand2_series():
                t = random.choice(teams)
                st.session_state["series_team2"] = t
                seasons = sorted(
                    season_df[season_df["Team"] == t]["Season"].unique(),
                    reverse=True
                )
                if seasons:
                    st.session_state["series_season2"] = random.choice(seasons)
            st.button("🎲 Random Team + Season 2", on_click=pick_rand2_series, key="btn_rand2_series")

            t2s = st.selectbox("Team 2", [""] + teams, key="series_team2")
            s2s = st.selectbox(
                "Season 2",
                sorted(season_df[season_df["Team"] == t2s]["Season"].unique(), reverse=True)
                if t2s else [],
                key="series_season2"
            )

        if st.button("▶️ Sim Best of 7", key="btn_best_of_7"):
            # no shared state to clear here
            if not (t1s and t2s and s1s and s2s):
                st.error("❗ Select both teams and their seasons.")
                st.stop()
            if t1s == t2s and s1s == s2s:
                st.error("❗ Cannot simulate a team against itself.")
                st.stop()

            full1 = f"{t1s} ({s1s})"
            full2 = f"{t2s} ({s2s})"
            wins, logs = simulate_best_of_7(t1s, s1s, t2s, s2s)

            st.subheader("🔁 Best-of-7 Results")
            st.text(f"{full1}: {wins[full1]} wins")
            st.text(f"{full2}: {wins[full2]} wins")
            champ = full1 if wins[full1] == 4 else full2
            st.success(f"🏆 {champ}")

            st.markdown("---")
            st.subheader("Game Logs")
            for g in logs:
                st.write(g)

    # ─── Reset Button ────────────────────────────────────────────────
    if st.button("🔄 Reset All Matchups", key="btn_reset"):
        for k in list(st.session_state.keys()):
            if k.startswith("game_") or k.startswith("series_"):
                del st.session_state[k]
        st.experimental_rerun()


if __name__ == '__main__':
    run_free_sim()
