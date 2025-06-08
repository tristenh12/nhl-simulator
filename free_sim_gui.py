# free_sim_gui.py
import streamlit as st
import pandas as pd
import time
import re
from free_sim import simulate_one_game, simulate_best_of_7
import os

# Compile period header pattern at module level for reuse
period_pattern = re.compile(r"=== (\d+)(?:st|nd|rd) Period ===")


def run_free_sim():
    """
    Free NHL One-Game / Best-of-7 Simulator.
    """

    # ─────────────────────────────────────────────────────────────────
    # (A) Page title and description
    # ─────────────────────────────────────────────────────────────────
    st.title("🎮 Free NHL One-Game Simulator")
    st.markdown("Select two teams (and seasons), then simulate a single game or a best-of-7 series.")

    # ─────────────────────────────────────────────────────────────────
    # (B) Load data + build sidebar selectors
    # ─────────────────────────────────────────────────────────────────
    @st.cache_data
    def load_season_df():
        here = os.path.dirname(__file__)
        data_path = os.path.join(here, "data", "teams_alignment_complete.csv")
        return pd.read_csv(data_path)


    season_df = load_season_df()
    teams = sorted(season_df["Team"].unique())

    st.sidebar.header("Team Selection")
    t1 = st.sidebar.selectbox("Team 1", [""] + teams, index=0)
    t2 = st.sidebar.selectbox("Team 2", [""] + teams, index=1)
    s1 = st.sidebar.selectbox(
        "Season 1",
        sorted(season_df[season_df["Team"] == t1]["Season"].unique(), reverse=True)
    ) if t1 else ""
    s2 = st.sidebar.selectbox(
        "Season 2",
        sorted(season_df[season_df["Team"] == t2]["Season"].unique(), reverse=True)
    ) if t2 else ""

    # ─────────────────────────────────────────────────────────────────
    # (C) Buttons and simulation logic
    # ─────────────────────────────────────────────────────────────────
    c1, c2, c3 = st.columns(3)

    # ─── One-Game Simulation with live feed and controls ────────────
    if c1.button("▶️ Sim One Game"):
        # Clear old state
        for k in ("commentary_sorted","stats","full1","full2","full_box_df","feed_idx","playing"):  
            st.session_state.pop(k, None)

        # Validate
        if not (t1 and t2 and s1 and s2):
            st.error("❗ Select both teams and their seasons.")
            st.stop()
        if t1 == t2 and s1 == s2:
            st.error("❗ Cannot simulate a team against itself.")
            st.stop()

        full1 = f"{t1} ({s1})"
        full2 = f"{t2} ({s2})"
        # simulate_one_game must return commentary, stats, full_box_df
        commentary, stats, full_box_df = simulate_one_game(t1, s1, t2, s2)

        # Prepare grouping by period and sort within each by timestamp
        ts_match = re.compile(r"(\d+):(\d+)")
        def parse_ts(ln):
            m = ts_match.search(ln)
            return int(m.group(1))*60 + int(m.group(2)) if m else float('inf')

        period_order = []
        period_events = {}
        current = None
        for ln in commentary:
            if period_pattern.match(ln):
                p = period_pattern.match(ln).group(1)
                current = p
                if p not in period_order:
                    period_order.append(p)
                period_events[p] = []
            elif current:
                period_events[current].append(ln)

        # Build sorted commentary list
        commentary_sorted = []
        for p in period_order:
            suffix = 'st' if p=='1' else 'nd' if p=='2' else 'rd' if p=='3' else ''
            commentary_sorted.append(f"=== {p}{suffix} Period ===")
            evs = period_events.get(p, [])
            evs_sorted = sorted(evs, key=parse_ts)
            commentary_sorted.extend(evs_sorted)

        # Initialize playback state
        st.session_state.commentary_sorted = commentary_sorted
        st.session_state.stats = stats
        st.session_state.full1, st.session_state.full2 = full1, full2
        st.session_state.full_box_df = full_box_df
        st.session_state.feed_idx = 0
        st.session_state.playing = False

        st.rerun()

    # ─── Live feed + controls display ───────────────────────────────
    if "commentary_sorted" in st.session_state:
        comm = st.session_state.commentary_sorted
        stats = st.session_state.stats
        full1 = st.session_state.full1
        full2 = st.session_state.full2
        full_box_df = st.session_state.full_box_df
        idx = st.session_state.feed_idx

        speed = st.selectbox("Speed", ["1×","2×","4×"], index=0)
        delay_map = {"1×":.5, "2×":.25, "4×":.125}

        # Play/Pause/Skip
        p1,p2,p3 = st.columns(3)
        with p1:
            if st.button("▶ Play"):
                st.session_state.playing = True
        with p2:
            if st.button("⏸ Pause"):
                st.session_state.playing = False
        with p3:
            if st.button("⏭ Skip to End"):
                st.session_state.feed_idx = len(comm)

        # Render feed window
        st.subheader(f"{full1} vs {full2} — Live Feed")
        ph = st.empty()
        # show the last 10 lines instead of 5
        max_lines = 10
        start = max(0, idx - max_lines)
        ph.text("\n".join(comm[start:idx]))


        # Auto-advance
        if st.session_state.playing and idx < len(comm):
            time.sleep(delay_map[speed])
            st.session_state.feed_idx += 1
            st.rerun()

        # Final stats once done
        if idx >= len(comm):
            st.markdown("---")
            st.subheader("Final Stats")
            st.text(f"FINAL SCORE: {full1} {stats[full1]['Goals']} – {stats[full2]['Goals']} {full2}")
            st.text(f"SHOTS: {stats[full1]['Shots']} – {stats[full2]['Shots']}")
            st.text(f"HITS: {stats[full1]['Hits']} – {stats[full2]['Hits']}")
            st.text(f"PIM: {stats[full1]['PIM']} – {stats[full2]['PIM']}")
            st.text(f"PPG/PP: {stats[full1]['PPG']}/{stats[full1]['PP']} – {stats[full2]['PPG']}/{stats[full2]['PP']}")
            st.text(f"POSSESSION: {stats[full1]['Possession']} – {stats[full2]['Possession']}")

            if st.button("View Full Box Score"):
                # Rebuild DataFrame with period rows in correct place
                rows = []
                for ln in comm:
                    if period_pattern.match(ln):
                        rows.append({"Time": ln, "Team": "", "Event": ""})
                    else:
                        if " – " in ln:
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

    # ─── Best-of-7 & reset ─────────────────────────────────────────
    if c2.button("▶️ Sim Best of 7"):
        if not (t1 and t2 and s1 and s2):
            st.error("❗ Select both teams and seasons.")
            return
        if t1 == t2 and s1 == s2:
            st.error("❗ Cannot simulate a team against itself.")
            return

        full1 = f"{t1} ({s1})"
        full2 = f"{t2} ({s2})"
        wins, logs = simulate_best_of_7(t1, s1, t2, s2)

        st.subheader("🔁 Best-of-7 Results")
        st.text(f"{full1}: {wins[full1]} wins")
        st.text(f"{full2}: {wins[full2]} wins")
        champ = full1 if wins[full1] == 4 else full2
        st.success(f"🏆 {champ}")

        st.markdown("---")
        st.subheader("Game Logs")
        for g in logs:
            st.write(g)

    if c3.button("🔄 Reset Matchup"):
        for k in ("commentary_sorted","stats","full1","full2","full_box_df","feed_idx","playing"):  
            st.session_state.pop(k, None)
        st.rerun()

if __name__ == '__main__':
    run_free_sim()
