# stats_updater.py
import streamlit as st
import datetime

def update_user_stats(supabase, bracket, standings_df, user_email):
    # 0) Seed every team with default rows so none are ever missing
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

    # 1) Fetch current user row
    user_resp = (
        supabase
        .table("users")
        .select("*")
        .eq("email", user_email)
        .single()
        .execute()
    )
    user = user_resp.data or {}
    fav  = user.get("favorite_team", "")

    # 2) Compute overall and favorite-team simulation counters
    now_iso = datetime.datetime.utcnow().isoformat()
    per_user_updates = {
        "total_sims_run":         int(user.get("total_sims_run", 0)) + 1,
        "last_sim_date":          now_iso,
        "fav_team_sims_run":      int(user.get("fav_team_sims_run", 0)) + 1,
        "fav_team_last_sim_date": now_iso
    }

    # 3) Only bump trophies if favorite truly won
    cup_winner = bracket["final"][0]["winner"].split(" (")[0]
    top_team   = (
        standings_df
          .sort_values(["PTS","Win%"], ascending=[False,False])
          .iloc[0]["RawTeam"]
          .split(" (")[0]
    )
    if fav == cup_winner:
        per_user_updates["championships_won"] = int(user.get("championships_won", 0)) + 1
    if fav == top_team:
        per_user_updates["presidents_trophies"] = int(user.get("presidents_trophies", 0)) + 1

    # 4) Update favorite-team personal bests
    fav_rows = standings_df[standings_df["RawTeam"].str.startswith(fav)]
    if not fav_rows.empty:
        fr = fav_rows.iloc[0]
        w, pts, l = int(fr["W"]), int(fr["PTS"]), int(fr["L"])
        per_user_updates["record_wins"]   = max(int(user.get("record_wins", 0)), w)
        per_user_updates["record_pts"]    = max(int(user.get("record_pts", 0)), pts)
        per_user_updates["record_losses"] = min(int(user.get("record_losses", 999)), l)

    # 5) Push per-user updates
    supabase.table("users") \
        .update(per_user_updates) \
        .eq("email", user_email) \
        .execute()

    # 6) Helpers for per-team stats
    def fetch_stat(team, col, default):
        resp = (
            supabase
            .table("team_stats")
            .select(col)
            .eq("team", team)
            .single()
            .execute()
        )
        return int((resp.data or {}).get(col, default))

    def upsert_stat(team, col, new_val):
        supabase.table("team_stats") \
            .upsert({"team": team, col: new_val}, on_conflict="team") \
            .execute()

    # 7) Increment the Cup and Presidents' Trophy counters
    old = fetch_stat(cup_winner, "stanley_cup_wins", 0)
    upsert_stat(cup_winner, "stanley_cup_wins", old + 1)

    old = fetch_stat(top_team, "presidents_trophies", 0)
    upsert_stat(top_team, "presidents_trophies", old + 1)

    # 8) For every team in this season, update their bests if beaten
    for raw in standings_df["RawTeam"]:
        team = raw.split(" (")[0]
        row = standings_df[standings_df["RawTeam"] == raw].iloc[0]
        w, pts, l = int(row["W"]), int(row["PTS"]), int(row["L"])

        old_w = fetch_stat(team, "best_wins", 0)
        upsert_stat(team, "best_wins", max(old_w, w))

        old_p = fetch_stat(team, "best_pts", 0)
        upsert_stat(team, "best_pts", max(old_p, pts))

        old_l = fetch_stat(team, "fewest_losses", 999)
        upsert_stat(team, "fewest_losses", min(old_l, l))

    st.success("All user and league stats updated successfully!")
