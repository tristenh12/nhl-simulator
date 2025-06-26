# stats_updater.py
import streamlit as st

def update_user_stats(supabase, bracket, standings_df, user_email):
    st.write("[DEBUG] Starting stats update for", user_email)

    # ─── 1) Per-user updates ────────────────────────────────────────────────────
    user_resp = supabase.table("users") \
        .select("*") \
        .eq("email", user_email) \
        .single() \
        .execute()
    user = user_resp.data or {}
    fav = user.get("favorite_team")

    cup_winner = bracket["final"][0]["winner"].split(" (")[0]
    top_team   = standings_df.sort_values(
                    ["PTS","Win%"], ascending=[False,False]
                 ).iloc[0]["RawTeam"].split(" (")[0]

    updates = {}
    if fav == cup_winner:
        updates["championships_won"] = int(user.get("championships_won", 0)) + 1
    if fav == top_team:
        updates["presidents_trophies"] = int(user.get("presidents_trophies", 0)) + 1

    # Always update fav-team record if beaten
    fav_row = standings_df[standings_df["RawTeam"].str.startswith(fav)]
    if not fav_row.empty:
        fr = fav_row.iloc[0]
        w, pts, l = int(fr["W"]), int(fr["PTS"]), int(fr["L"])
        updates["record_wins"]   = max(int(user.get("record_wins", 0)), w)
        updates["record_pts"]    = max(int(user.get("record_pts", 0)), pts)
        updates["record_losses"] = min(int(user.get("record_losses", 999)), l)

    if updates:
        supabase.table("users").update(updates).eq("email", user_email).execute()
        st.write("[DEBUG] Per-user stats updated:", updates)

    # ─── Helper to fetch a single column (or return default 0 / large value) ──
    def fetch_stat(team, col, default=0):
        resp = supabase.table("team_stats").select(f"team,{col}") \
            .eq("team", team).execute()
        rows = resp.data or []
        if len(rows) == 1 and col in rows[0]:
            return int(rows[0][col])
        return default

    def upsert_stat(team, col, new_val):
        supabase.table("team_stats") \
            .upsert({ "team": team, col: new_val }, on_conflict="team") \
            .execute()
        st.write(f"[DEBUG] team_stats: set {col} for {team} → {new_val}")

    # ─── 2a) Cup wins ────────────────────────────────────────────────────────────
    old = fetch_stat(cup_winner, "stanley_cup_wins", default=0)
    upsert_stat(cup_winner, "stanley_cup_wins", old + 1)

    # ─── 2b) Presidents' trophies ────────────────────────────────────────────────
    old = fetch_stat(top_team, "presidents_trophies", default=0)
    upsert_stat(top_team, "presidents_trophies", old + 1)

    # ─── 2c) League global records ──────────────────────────────────────────────
    # Best wins
    bw = int(standings_df["W"].max())
    bwt = standings_df.loc[standings_df["W"].idxmax(), "RawTeam"].split(" (")[0]
    old = fetch_stat(bwt, "best_wins", default=0)
    upsert_stat(bwt, "best_wins", max(old, bw))

    # Best pts
    bp = int(standings_df["PTS"].max())
    bpt = standings_df.loc[standings_df["PTS"].idxmax(), "RawTeam"].split(" (")[0]
    old = fetch_stat(bpt, "best_pts", default=0)
    upsert_stat(bpt, "best_pts", max(old, bp))

    # Fewest losses
    fl = int(standings_df["L"].min())
    flt = standings_df.loc[standings_df["L"].idxmin(), "RawTeam"].split(" (")[0]
    old = fetch_stat(flt, "fewest_losses", default=999)
    upsert_stat(flt, "fewest_losses", min(old, fl))

    st.success("Per-team stats updated successfully!")
