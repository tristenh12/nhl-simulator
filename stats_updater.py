# stats_updater.py
import streamlit as st

def update_user_stats(supabase, bracket, standings_df, user_email):
    """
    - Updates user-specific stats in `users` table
    - Maintains league-wide distribution in `league_aggregates` table:
      cups_won (count), presidents_trophies (count), best_wins, best_pts, least_losses per team
    """
    st.write("[DEBUG] Starting stats update for", user_email)
    # Fetch user data
    user_resp = supabase.table("users").select("*").eq("email", user_email).single().execute()
    user = user_resp.data
    if not user:
        st.error("Failed to fetch user data.")
        return

    # Determine winners
    cup_winner = bracket["final"][0]["winner"].split(" (")[0]
    top_team = standings_df.sort_values(["PTS","Win%"], ascending=[False,False]).iloc[0]["RawTeam"]

    # 1) Update user stats as before
    updates = {}
    if user.get("favorite_team") == cup_winner:
        updates["championships_won"] = int(user.get("championships_won",0)) + 1
    if user.get("favorite_team") == top_team:
        updates["presidents_trophies"] = int(user.get("presidents_trophies",0)) + 1
    updates["cups_won"] = int(user.get("cups_won",0)) + 1
    # champion record
    match_df = standings_df[standings_df["RawTeam"].str.startswith(cup_winner)]
    if not match_df.empty:
        champ = match_df.iloc[0]
        updates["record_wins"]   = max(int(user.get("record_wins",0)), int(champ["W"]))
        updates["record_pts"]    = max(int(user.get("record_pts",0)), int(champ["PTS"]))
        updates["record_losses"] = min(int(user.get("record_losses",999)), int(champ["L"]))
    supabase.table("users").update(updates).eq("email", user_email).execute()
    st.write("[DEBUG] User stats updated.")

    # 2) Update league distribution in league_aggregates table
    # Compute counts and records for this simulation
    # Cups and trophies: just 1 per winning team
    league_updates = []
    # Cup win
    league_updates.append({
        "team": cup_winner,
        "delta_cups": 1
    })
    # Presidents' Trophy
    league_updates.append({
        "team": top_team,
        "delta_trophies": 1
    })
    # Best wins
    best_wins = int(standings_df["W"].max())
    best_wins_team = standings_df.loc[standings_df["W"].idxmax(), "RawTeam"]
    league_updates.append({
        "team": best_wins_team,
        "best_wins": best_wins
    })
    # Best points
    best_pts = int(standings_df["PTS"].max())
    best_pts_team = standings_df.loc[standings_df["PTS"].idxmax(), "RawTeam"]
    league_updates.append({
        "team": best_pts_team,
        "best_pts": best_pts
    })
    # Fewest losses
    few_losses = int(standings_df["L"].min())
    few_losses_team = standings_df.loc[standings_df["L"].idxmin(), "RawTeam"]
    league_updates.append({
        "team": few_losses_team,
        "few_losses": few_losses
    })

    # Upsert each record into league_aggregates
    for entry in league_updates:
        # Build upsert payload
        payload = {"team": entry["team"]}
        if entry.get("delta_cups"):
            payload["cups_won"] = f"cups_won + {entry['delta_cups']}"
        if entry.get("delta_trophies"):
            payload["presidents_trophies"] = f"presidents_trophies + {entry['delta_trophies']}"
        if entry.get("best_wins") is not None:
            payload["best_wins"] = entry["best_wins"]
        if entry.get("best_pts") is not None:
            payload["best_pts"] = entry["best_pts"]
        if entry.get("few_losses") is not None:
            payload["few_losses"] = entry["few_losses"]
        # Perform upsert with SQL raw expressions for increments
        supabase.postgrest.rpc(
            "increment_league_aggregate",
            {"team": entry["team"], "updates": payload}
        ).execute()
    st.write("[DEBUG] League aggregates updated.")
