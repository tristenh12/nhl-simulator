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
    # Fetch current user data
    user_resp = supabase.table("users").select("*").eq("email", user_email).single().execute()
    if user_resp.error or not user_resp.data:
        st.error("Failed to fetch user stats for update.")
        return
    user = user_resp.data

    # Determine winners
    cup_winner = bracket["final"][0]["winner"].split(" (")[0]
    top_team = standings_df.sort_values(["PTS","Win%"], ascending=[False,False]).iloc[0]["RawTeam"]

    updates = {}
    # Favorite team trophies
    if user.get("favorite_team") == cup_winner:
        updates["championships_won"] = user.get("championships_won", 0) + 1
    if user.get("favorite_team") == top_team:
        updates["presidents_trophies"] = user.get("presidents_trophies", 0) + 1
    # Always count cup
    updates["cups_won"] = user.get("cups_won", 0) + 1

    # Update record stats
    champ_record = standings_df[standings_df["RawTeam"] == cup_winner].iloc[0]
    updates["record_wins"] = max(user.get("record_wins", 0), champ_record["W"])
    updates["record_pts"] = max(user.get("record_pts", 0), champ_record["PTS"])
    updates["record_losses"] = max(user.get("record_losses", 0), champ_record["L"])

    # Push updates
    res = supabase.table("users").update(updates).eq("email", user_email).execute()
    if res.error:
        st.error(f"Error updating user stats: {res.error.message}")
    else:
        st.success("User stats updated successfully!")
