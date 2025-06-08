# free_sim.py
import random
import re
import pandas as pd

def get_team_rating(team_name, season):
    df = pd.read_csv("data/teams_alignment_complete.csv")
    row = df[(df["Team"] == team_name) & (df["Season"] == season)]
    if not row.empty:
        return float(row.iloc[0]["Rating"])
    return 80.0  # Default if not found

def simulate_one_game(team1_name, season1, team2_name, season2):
    """
    Returns:
      commentary:   list[str] of event lines
      stats:        dict mapping "Team (Season)" → summary stat dict
      full_box_df:  pandas.DataFrame of detailed play-by-play
    """
    team1 = f"{team1_name} ({season1})"
    team2 = f"{team2_name} ({season2})"

    rating1 = get_team_rating(team1_name, season1)
    rating2 = get_team_rating(team2_name, season2)
    bias1 = rating1 / (rating1 + rating2)
    bias2 = 1 - bias1

    periods = ["1st Period", "2nd Period", "3rd Period"]
    stats = {
        team1: {"Goals": 0, "Shots": 0, "Hits": 0, "PIM": 0, "PPG": 0, "PP": 0, "Possession": 0},
        team2: {"Goals": 0, "Shots": 0, "Hits": 0, "PIM": 0, "PPG": 0, "PP": 0, "Possession": 0}
    }
    commentary = []

    for period in periods:
        commentary.append(f"=== {period} ===")
        for _ in range(40):
            t = random.choices([team1, team2], weights=[bias1, bias2])[0]
            opp = team2 if t == team1 else team1

            event = random.choices(
                ["Shot on Goal", "Hit", "Penalty", "Faceoff Win"],
                weights=[65, 20, 7, 8],
                k=1
            )[0]
            minute = random.randint(0, 19)
            second = random.randint(0, 59)
            time_str = f"{minute:02d}:{second:02d}"
            line = f"{time_str} – {t}: {event}"
            commentary.append(line)

            # update stats and inject GOAL events
            if event == "Shot on Goal":
                stats[t]["Shots"] += 1
                goal_chance = 0.10 * (rating1/100 if t == team1 else rating2/100)
                if random.random() < goal_chance:
                    stats[t]["Goals"] += 1
                    commentary.append(f"{time_str} – {t}: GOAL")
            elif event == "Hit":
                stats[t]["Hits"] += 1
            elif event == "Penalty":
                stats[t]["PIM"] += 2
                stats[opp]["PP"] += 1
                pp_chance = 0.18 * (rating1/100 if opp == team1 else rating2/100)
                if random.random() < pp_chance:
                    stats[opp]["PPG"] += 1
                    stats[opp]["Goals"] += 1
                    commentary.append(f"{time_str} – {opp}: GOAL (PP)")

            stats[t]["Possession"] += random.randint(10, 20)

    # format possession
    for team in (team1, team2):
        sec = stats[team]["Possession"]
        m, s = divmod(sec, 60)
        stats[team]["Possession"] = f"{m:02d}:{s:02d}"

    # build full_box_df
    rows = []
    pattern = re.compile(r"(\d{2}:\d{2}) – ([^:]+): (.+)")
    for ln in commentary:
        if ln.startswith("==="):
            rows.append({"Time": ln, "Team": "", "Event": ""})
        else:
            m = pattern.match(ln)
            if m:
                ts, team_part, ev_part = m.groups()
                rows.append({"Time": ts, "Team": team_part, "Event": ev_part})
            else:
                rows.append({"Time": "", "Team": "", "Event": ln})

    full_box_df = pd.DataFrame(rows)
    return commentary, stats, full_box_df

def simulate_best_of_7(team1_name, season1, team2_name, season2):
    """
    Returns:
      wins: dict of wins per team
      logs: list of per-game summary
    """
    team1 = f"{team1_name} ({season1})"
    team2 = f"{team2_name} ({season2})"
    rating1 = get_team_rating(team1_name, season1)
    rating2 = get_team_rating(team2_name, season2)

    wins = {team1: 0, team2: 0}
    logs = []
    while wins[team1] < 4 and wins[team2] < 4:
        commentary, stats, _ = simulate_one_game(team1_name, season1, team2_name, season2)
        s1 = stats[team1]["Goals"]
        s2 = stats[team2]["Goals"]
        if s1 > s2:
            winner = team1
        elif s2 > s1:
            winner = team2
        else:
            winner = random.choices([team1, team2], weights=[rating1, rating2])[0]
            commentary.append(f"OT: {winner} wins")
        wins[winner] += 1
        logs.append(f"Game {len(logs)+1}: {winner} ({s1}-{s2})")
    return wins, logs
