# stats_updater.py
import streamlit as st

def update_user_stats(supabase, bracket, standings_df, user_email):
    st.write("[DEBUG] Starting stats update for", user_email)

    # 1) Fetch & update per-user stats
    user_resp = supabase.table("users") \
        .select("*") \
        .eq("email", user_email) \
        .single() \
        .execute()
    user = user_resp.data or {}
    fav = user.get("favorite_team")

    # Determine who won this sim
    cup_winner = bracket["final"][0]["winner"].split(" (")[0]
    top_team   = standings_df.sort_values(["PTS","Win%"], ascending=[False,False]) \
                    .iloc[0]["RawTeam"].split(" (")[0]

    updates = {}

    # +1 Stanley Cups (championships_won) only if fav won
    if fav == cup_winner:
        updates["championships_won"] = int(user.get("championships_won", 0)) + 1
        st.write("[DEBUG] +1 Stanley Cups →", updates["championships_won"])

    # +1 Presidents' Trophies only if fav finished first
    if fav == top_team:
        updates["presidents_trophies"] = int(user.get("presidents_trophies", 0)) + 1
        st.write("[DEBUG] +1 Presidents' Trophies →", updates["presidents_trophies"])

    # Always update fav team's record stats if beaten
    fav_row = standings_df[standings_df["RawTeam"].str.startswith(fav)]
    if not fav_row.empty:
        r = fav_row.iloc[0]
        w, pts, l = int(r["W"]), int(r["PTS"]), int(r["L"])
        updates["record_wins"]   = max(int(user.get("record_wins", 0)), w)
        updates["record_pts"]    = max(int(user.get("record_pts", 0)), pts)
        updates["record_losses"] = min(int(user.get("record_losses", 999)), l)
        st.write(f"[DEBUG] Fav record → W:{updates['record_wins']} PTS:{updates['record_pts']} L:{updates['record_losses']}")

    if updates:
        supabase.table("users") \
            .update(updates) \
            .eq("email", user_email) \
            .execute()
        st.write("[DEBUG] Per-user stats updated.")

    # 2) Upsert into team_stats by fetching & computing in Python

    def fetch_stat(team, col):
        r = supabase.table("team_stats").select(col).eq("team", team).single().execute().data
        return int(r.get(col, 0)) if r else 0

    def upsert_stat(team, col, new_val):
        supabase.table("team_stats") \
            .upsert({"team": team, col: new_val}, on_conflict="team") \
            .execute()
        st.write(f"[DEBUG] team_stats: set {col} for {team} → {new_val}")

    # a) Stanley Cup wins
    old = fetch_stat(cup_winner, "stanley_cup_wins")
    upsert_stat(cup_winner, "stanley_cup_wins", old + 1)

    # b) Presidents' trophies
    old = fetch_stat(top_team, "presidents_trophies")
    upsert_stat(top_team, "presidents_trophies", old + 1)

    # c) Global league records
    #    wins
    best_wins = int(standings_df["W"].max())
    best_tm   = standings_df.loc[standings_df["W"].idxmax(), "RawTeam"].split(" (")[0]
    old       = fetch_stat(best_tm, "best_wins")
    upsert_stat(best_tm, "best_wins", max(old, best_wins))

    #    pts
    best_pts  = int(standings_df["PTS"].max())
    bestp_tm  = standings_df.loc[standings_df["PTS"].idxmax(), "RawTeam"].split(" (")[0]
    old       = fetch_stat(bestp_tm, "best_pts")
    upsert_stat(bestp_tm, "best_pts", max(old, best_pts))

    #    fewest losses
    few_l     = int(standings_df["L"].min())
    few_tm    = standings_df.loc[standings_df["L"].idxmin(), "RawTeam"].split(" (")[0]
    old       = fetch_stat(few_tm, "fewest_losses")
    upsert_stat(few_tm, "fewest_losses", min(old, few_l))

    st.success("Per-team stats updated successfully!")
