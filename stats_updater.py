# stats_updater.py
import streamlit as st


def update_user_stats(supabase, bracket, standings_df, user_email):
    """
    - Updates per-user stats in `users` table
    - Maintains league-wide distribution in `league_aggregates` via a PostgreSQL RPC
    """
    st.write("[DEBUG] Starting stats update for", user_email)
    # 1) Update per-user stats
    user_resp = supabase.table("users").select("*").eq("email", user_email).single().execute()
    user = user_resp.data
    if not user:
        st.error("Failed to fetch user data.")
        return

    cup_winner = bracket["final"][0]["winner"].split(" (")[0]
    top_team = standings_df.sort_values(["PTS","Win%"], ascending=[False,False]).iloc[0]["RawTeam"]

    updates = {}
    if user.get("favorite_team") == cup_winner:
        updates["championships_won"] = int(user.get("championships_won", 0)) + 1
    if user.get("favorite_team") == top_team:
        updates["presidents_trophies"] = int(user.get("presidents_trophies", 0)) + 1
    updates["cups_won"] = int(user.get("cups_won", 0)) + 1

    # Champion record
    match_df = standings_df[standings_df["RawTeam"].str.startswith(cup_winner)]
    if not match_df.empty:
        champ = match_df.iloc[0]
        updates["record_wins"]   = max(int(user.get("record_wins",0)), int(champ["W"]))
        updates["record_pts"]    = max(int(user.get("record_pts",0)), int(champ["PTS"]))
        updates["record_losses"] = min(int(user.get("record_losses",999)), int(champ["L"]))

    supabase.table("users").update(updates).eq("email", user_email).execute()
    st.write("[DEBUG] User stats updated.")

    # 2) Update league-wide aggregates via RPC
    champ_wins = int(standings_df["W"].max())
    champ_wins_team = standings_df.loc[standings_df["W"].idxmax(), "RawTeam"]
    champ_pts = int(standings_df["PTS"].max())
    champ_pts_team = standings_df.loc[standings_df["PTS"].idxmax(), "RawTeam"]
    few_losses = int(standings_df["L"].min())
    few_losses_team = standings_df.loc[standings_df["L"].idxmin(), "RawTeam"]

    payloads = [
        {"_team": cup_winner,      "inc_cups": 1},
        {"_team": top_team,        "inc_presidents": 1},
        {"_team": champ_wins_team, "best_wins": champ_wins},
        {"_team": champ_pts_team,  "best_pts": champ_pts},
        {"_team": few_losses_team, "few_losses": few_losses},
    ]

    for p in payloads:
        res = supabase.rpc("increment_league_aggregate", p).execute()
        if res.error:
            st.error(f"RPC error for {p.get('_team')}: {res.error.message}")
        else:
            st.write(f"[DEBUG] RPC updated {p.get('_team')}: {res.data}")

    st.success("League aggregates updated.")
