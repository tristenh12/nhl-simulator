# stats_updater.py
import streamlit as st

def update_user_stats(supabase, bracket, standings_df, user_email):
    """
    Updates Supabase "users" table based on simulation results:
    - championships_won
    - presidents_trophies
    - cups_won
    - record_wins, record_pts, record_losses
    """
    st.write("[DEBUG] Starting user stats update for", user_email)
    # Fetch current user data
    user_resp = supabase.table("users").select("*").eq("email", user_email).single().execute()
    user_data = user_resp.data
    st.write("[DEBUG] Fetch user response data:", user_data)
    if not user_data:
        st.error("Failed to fetch user stats for update.")
        return

    # Determine winners
    cup_winner = bracket["final"][0]["winner"].split(" (")[0]
    # Presidents' Trophy winner (top regular-season team)
    top_team = standings_df.sort_values(["PTS", "Win%"], ascending=[False, False]).iloc[0]["Team"]
    st.write(f"[DEBUG] Cup winner: {cup_winner}, Top team: {top_team}")

    # Prepare updates
    updates = {}
    # Increment championships_won if user's favorite won the Cup
    if user_data.get("favorite_team") == cup_winner:
        updates["championships_won"] = int(user_data.get("championships_won", 0)) + 1
        st.write("[DEBUG] Increment championships_won to", updates["championships_won"])
    # Increment presidents_trophies if user's favorite won Presidents' Trophy
    if user_data.get("favorite_team") == top_team:
        updates["presidents_trophies"] = int(user_data.get("presidents_trophies", 0)) + 1
        st.write("[DEBUG] Increment presidents_trophies to", updates["presidents_trophies"])
    # Always increment cups_won
    updates["cups_won"] = int(user_data.get("cups_won", 0)) + 1
    st.write("[DEBUG] Increment cups_won to", updates["cups_won"])

    # Update record stats: wins, pts, losses
    # Match champion in standings by 'Team' column
    match_df = standings_df[standings_df["Team"] == cup_winner]
    if match_df.empty:
        st.error(f"Could not find champion {cup_winner} in standings ('Team') to update record stats. Available teams: {standings_df['Team'].tolist()}")
        return
    champ_record = match_df.iloc[0]
    # Cast to Python int
    new_wins = int(champ_record["W"])
    new_pts = int(champ_record["PTS"])
    new_losses = int(champ_record["L"])
    # Take max of existing vs new
    updates["record_wins"] = max(int(user_data.get("record_wins", 0)), new_wins)
    updates["record_pts"] = max(int(user_data.get("record_pts", 0)), new_pts)
    updates["record_losses"] = max(int(user_data.get("record_losses", 0)), new_losses)
    st.write("[DEBUG] New record stats:", {"wins": updates["record_wins"], "pts": updates["record_pts"], "losses": updates["record_losses"]})

    # Push updates to Supabase
    res = supabase.table("users").update(updates).eq("email", user_email).execute()
    res_data = getattr(res, 'data', None)
    st.write("[DEBUG] Update response data:", res_data)
    if res_data:
        st.success("User stats updated successfully!")
    else:
        st.error("No rows were updated. Check permissions or email match.")
