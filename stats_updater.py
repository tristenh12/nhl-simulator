# stats_updater.py
import streamlit as st

def update_user_stats(supabase, bracket, standings_df, user_email):
    """
    1) Update per-user stats in `users` table:
       - Stanley Cups (championships_won): only if favorite team wins the Cup
       - Presidents' Trophies: only if favorite team finishes first
       - record_wins, record_pts, record_losses: always updated if favorite team beats its prior best/worst
    2) Upsert per-team stats in `team_stats` table:
       - stanley_cup_wins
       - presidents_trophies
       - best_wins, best_pts, fewest_losses (global league records each sim)
    """
    st.write("[DEBUG] Starting stats update for", user_email)

    # ─── 1) Per-user updates ────────────────────────────────────────────────────
    resp = supabase.table("users") \
        .select("*") \
        .eq("email", user_email) \
        .single() \
        .execute()
    user = resp.data
    if not user:
        st.error("Failed to fetch user data.")
        return

    fav = user.get("favorite_team")
    cup_winner = bracket["final"][0]["winner"].split(" (")[0]
    top_team   = standings_df.sort_values(
                    ["PTS","Win%"], ascending=[False,False]
                 ).iloc[0]["RawTeam"].split(" (")[0]

    updates = {}
    if fav == cup_winner:
        updates["championships_won"] = int(user.get("championships_won", 0)) + 1
        st.write("[DEBUG] +1 Stanley Cups →", updates["championships_won"])
    if fav == top_team:
        updates["presidents_trophies"] = int(user.get("presidents_trophies", 0)) + 1
        st.write("[DEBUG] +1 Presidents’ Trophies →", updates["presidents_trophies"])

    # Always bump fav team’s record stats if beaten
    fav_row = standings_df[standings_df["RawTeam"].str.startswith(fav)]
    if not fav_row.empty:
        fr = fav_row.iloc[0]
        w, pts, l = int(fr["W"]), int(fr["PTS"]), int(fr["L"])
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

    # ─── 2) Per-team upserts ───────────────────────────────────────────────────
    # Compute global league records this sim
    league_best_wins      = int(standings_df["W"].max())
    league_best_wins_tm   = standings_df.loc[standings_df["W"].idxmax(), "RawTeam"].split(" (")[0]
    league_best_pts       = int(standings_df["PTS"].max())
    league_best_pts_tm    = standings_df.loc[standings_df["PTS"].idxmax(), "RawTeam"].split(" (")[0]
    league_fewest_losses  = int(standings_df["L"].min())
    league_fewest_losses_tm = standings_df.loc[standings_df["L"].idxmin(), "RawTeam"].split(" (")[0]

    # 2a) Cup wins
    supabase.table("team_stats").upsert(
        {"team": cup_winner, "stanley_cup_wins": 1},
        on_conflict="team",
        update={"stanley_cup_wins": "team_stats.stanley_cup_wins + EXCLUDED.stanley_cup_wins"}
    ).execute()
    st.write(f"[DEBUG] team_stats: +1 cup for {cup_winner}")

    # 2b) Presidents' trophies
    supabase.table("team_stats").upsert(
        {"team": top_team, "presidents_trophies": 1},
        on_conflict="team",
        update={"presidents_trophies": "team_stats.presidents_trophies + EXCLUDED.presidents_trophies"}
    ).execute()
    st.write(f"[DEBUG] team_stats: +1 presidents for {top_team}")

    # 2c) Global best/worst records
    supabase.table("team_stats").upsert(
        {
          "team": league_best_wins_tm,
          "best_wins": league_best_wins,
          "best_pts": league_best_pts,
          "fewest_losses": league_fewest_losses
        },
        on_conflict="team",
        update={
          "best_wins":     "GREATEST(team_stats.best_wins, EXCLUDED.best_wins)",
          "best_pts":      "GREATEST(team_stats.best_pts, EXCLUDED.best_pts)",
          "fewest_losses": "LEAST(team_stats.fewest_losses, EXCLUDED.fewest_losses)"
        }
    ).execute()
    st.write(f"[DEBUG] team_stats: updated league records for {league_best_wins_tm}")

    st.success("Per-team stats updated successfully!")
