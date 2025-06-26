# stats_updater.py
import streamlit as st

def update_user_stats(supabase, bracket, standings_df, user_email):
    st.write("[DEBUG] Starting stats update for", user_email)

    # ─── 0) Seed every team with defaults ─────────────────────────────────────
    all_teams = (
        standings_df["RawTeam"]
          .str.replace(r"\s\(\d{4}.\d{2}\)$", "", regex=True)
          .unique()
    )
    for tm in all_teams:
        supabase.table("team_stats").upsert(
            {
                "team": tm,
                "stanley_cup_wins":    0,
                "presidents_trophies": 0,
                "best_wins":           0,
                "best_pts":            0,
                "fewest_losses":       999
            },
            on_conflict="team"
        ).execute()

    # ─── 1) Per-user updates ─────────────────────────────────────────────────
    user_resp = supabase.table("users") \
        .select("*") \
        .eq("email", user_email) \
        .single() \
        .execute()
    user = user_resp.data or {}
    fav = user.get("favorite_team", "")

    cup_winner = bracket["final"][0]["winner"].split(" (")[0]
    top_team   = (
        standings_df.sort_values(["PTS","Win%"], ascending=[False,False])
                    .iloc[0]["RawTeam"]
                    .split(" (")[0]
    )

    updates = {}
    if fav == cup_winner:
        updates["championships_won"] = int(user.get("championships_won", 0)) + 1
    if fav == top_team:
        updates["presidents_trophies"] = int(user.get("presidents_trophies", 0)) + 1

    # personal bests for favorite team
    fav_row = standings_df[standings_df["RawTeam"].str.startswith(fav)]
    if not fav_row.empty:
        fr = fav_row.iloc[0]
        w, pts, l = int(fr["W"]), int(fr["PTS"]), int(fr["L"])
        updates["record_wins"]   = max(int(user.get("record_wins", 0)), w)
        updates["record_pts"]    = max(int(user.get("record_pts", 0)), pts)
        updates["record_losses"] = min(int(user.get("record_losses", 999)), l)

    if updates:
        supabase.table("users") \
            .update(updates) \
            .eq("email", user_email) \
            .execute()
        st.write("[DEBUG] Per-user stats updated:", updates)

    # ─── 2) Per-team stats ────────────────────────────────────────────────────

    def fetch_stat(team, col, default):
        resp = supabase.table("team_stats") \
            .select(col) \
            .eq("team", team) \
            .single() \
            .execute()
        return int((resp.data or {}).get(col, default))

    def upsert_stat(team, col, new_val):
        supabase.table("team_stats") \
            .upsert({"team": team, col: new_val}, on_conflict="team") \
            .execute()
        st.write(f"[DEBUG] team_stats: set {col} for {team} → {new_val}")

    # 2a) Cup winner increment
    old = fetch_stat(cup_winner, "stanley_cup_wins", 0)
    upsert_stat(cup_winner, "stanley_cup_wins", old + 1)

    # 2b) Presidents' Trophy increment
    old = fetch_stat(top_team, "presidents_trophies", 0)
    upsert_stat(top_team, "presidents_trophies", old + 1)

    # 2c) EVERY team: update best_wins, best_pts, fewest_losses
    for raw in standings_df["RawTeam"]:
        team = raw.split(" (")[0]
        row = standings_df[standings_df["RawTeam"] == raw].iloc[0]
        w, pts, l = int(row["W"]), int(row["PTS"]), int(row["L"])

        # best wins
        old_w = fetch_stat(team, "best_wins", 0)
        upsert_stat(team, "best_wins", max(old_w, w))

        # best pts
        old_p = fetch_stat(team, "best_pts", 0)
        upsert_stat(team, "best_pts", max(old_p, pts))

        # fewest losses
        old_l = fetch_stat(team, "fewest_losses", 999)
        upsert_stat(team, "fewest_losses", min(old_l, l))

    st.success("All per-team stats updated successfully!")
