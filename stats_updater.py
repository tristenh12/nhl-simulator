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
    st.write("[DEBUG] Fetch user response data:", user_resp.data)
    if not user_resp.data:
        st.error("Failed to fetch user stats for update.")
        return
    user = user_resp.data
    st.write("[DEBUG] Current user data:", user)

    # Determine winners
    cup_winner = bracket["final"][0]["winner"].split(" (")[0]
    top_team = standings_df.sort_values(["PTS","Win%"], ascending=[False,False]).iloc[0]["RawTeam"]
    st.write(f"[DEBUG] Cup winner: {cup_winner}, Top team: {top_team}")

    updates = {}
    # Favorite team trophies
    if user.get("favorite_team") == cup_winner:
        updates["championships_won"] = int(user.get("championships_won", 0)) + 1
        st.write("[DEBUG] Increment championships_won to", updates["championships_won"]) 
    if user.get("favorite_team") == top_team:
        updates["presidents_trophies"] = int(user.get("presidents_trophies", 0)) + 1
        st.write("[DEBUG] Increment presidents_trophies to", updates["presidents_trophies"]) 
    # Always count cup
    updates["cups_won"] = int(user.get("cups_won", 0)) + 1
    st.write("[DEBUG] Increment cups_won to", updates["cups_won"]) 

    # Update record stats
    champ_record = standings_df[standings_df["RawTeam"] == cup_winner].iloc[0]
    # cast numpy ints to Python ints
    new_wins = int(champ_record["W"])
    new_pts = int(champ_record["PTS"])
    new_losses = int(champ_record["L"])
    updates["record_wins"] = max(int(user.get("record_wins", 0)), new_wins)
    updates["record_pts"] = max(int(user.get("record_pts", 0)), new_pts)
    updates["record_losses"] = max(int(user.get("record_losses", 0)), new_losses)
    st.write("[DEBUG] New record stats:", {"wins": updates["record_wins"], "pts": updates["record_pts"], "losses": updates["record_losses"]})

    # Push updates
    res = supabase.table("users").update(updates).eq("email", user_email).execute()
    # Detailed response logging
    st.write("[DEBUG] Update response data:", getattr(res, 'data', None))
    if getattr(res, 'data', None):
        st.success("User stats updated successfully!")
    else:
        st.error("No rows were updated. Check permissions or email match.")
