import random
import pandas as pd
from collections import defaultdict
from itertools import combinations

def get_division(team, divisions, include_original=False, original_divisions=None):
    """
    Return the “modern” division (key of the `divisions` dict) in which `team` sits.
    If include_original=True and original_divisions is provided, append the original historical division.
    """
    for div, teams in divisions.items():
        if team in teams:
            if include_original and original_divisions:
                original_division = original_divisions.get(team)
                if original_division and original_division != div:
                    return f"{div} ({original_division})"
            return div
    return "Unknown"


def get_conference(team, divisions, season_df=None):
    """
    First, try to infer conference from the “modern” divisions dict.
    If `team` is in any of divisions[div_name], return “East” or “West” based on div_name keywords.
    Otherwise, fall back to reading the team’s historical “Conference” column from season_df.
    """
    # 1) Check “modern” divisions
    for div_name, team_list in divisions.items():
        if team in team_list:
            # Any key containing “Atlantic” or “Metropolitan” is East, etc.
            if any(k in div_name for k in ["Atlantic", "Metropolitan", "East", "Wales", "Adams", "Canadian", "Patrick", "Southeast", "Northeast"]):
                return "East"
            elif any(k in div_name for k in ["Central", "Pacific", "West", "Campbell", "Norris", "Smythe", "Northwest"]):
                return "West"

    # 2) Fallback: look up from season_df if provided
    if season_df is not None:
        conf_series = season_df[season_df["Team"] == team]["Conference"]
        if not conf_series.empty:
            return conf_series.values[0]

    return "Unknown"


def generate_balanced_schedule(ratings):
    """
    Try to generate an 82-game schedule for every team in `ratings`.
    If impossible (e.g. too few teams), fall back to a single round-robin (each pair meets once).
    Returns a list of (team1, team2) match tuples.
    """
    teams = list(ratings.keys())
    num_teams = len(teams)
    target_games = 82

    games_per_team = {team: 0 for team in teams}
    matchup_counts = defaultdict(int)
    matchups = []

    # Calculate a reasonable “max times any pair can meet” 
    estimated_games_needed = (target_games * num_teams) / 2
    total_possible_pairs = num_teams * (num_teams - 1) / 2
    max_vs_same_team = int((estimated_games_needed / total_possible_pairs) * 2.2)
    max_vs_same_team = max(1, min(max_vs_same_team, 10))

    possible_pairs = list(combinations(teams, 2))

    try:
        # Attempt to fill 82 games per team
        while any(g < target_games for g in games_per_team.values()):
            scheduled = False
            for t1, t2 in possible_pairs:
                if (
                    games_per_team[t1] < target_games
                    and games_per_team[t2] < target_games
                    and matchup_counts[(t1, t2)] < max_vs_same_team
                ):
                    matchups.append((t1, t2))
                    games_per_team[t1] += 1
                    games_per_team[t2] += 1
                    matchup_counts[(t1, t2)] += 1
                    matchup_counts[(t2, t1)] += 1
                    scheduled = True
            if not scheduled:
                # Cannot place any more games under these constraints → fallback
                raise ValueError("Cannot complete 82-game schedule.")
        return matchups

    except ValueError:
        # FALLBACK: single round-robin
        return possible_pairs


def simulate_game(team1, team2, ratings):
    """
    Simulate one game between team1 and team2 based on their ratings.
    Returns (winner, ot_flag).
    """
    team1_clean = team1.split(" (")[0]
    team2_clean = team2.split(" (")[0]
    diff = ratings.get(team1_clean, 75.0) - ratings.get(team2_clean, 75.0)
    base = 50 + diff * 0.7
    chance = max(10, min(90, base))
    winner = team1 if random.random() * 100 < chance else team2
    ot = random.random() < 0.25
    return winner, ot


def simulate_season(divisions, ratings):
    """
    Given:
      divisions: dict mapping division_name → list of team_names (raw names)
      ratings: dict mapping raw team_name → rating
    Create a balanced schedule (or fallback), then simulate each matchup.
    Returns a stats dict: stats[team] = {"GP", "W", "L", "OTL"}.
    """
    stats = {team: {"GP": 0, "W": 0, "L": 0, "OTL": 0} for team in ratings}
    matchups = generate_balanced_schedule(ratings)
    for t1, t2 in matchups:
        winner, ot = simulate_game(t1, t2, ratings)
        stats[t1]["GP"] += 1
        stats[t2]["GP"] += 1
        if winner == t1:
            stats[t1]["W"] += 1
            if ot:
                stats[t2]["OTL"] += 1
            else:
                stats[t2]["L"] += 1
        else:
            stats[t2]["W"] += 1
            if ot:
                stats[t1]["OTL"] += 1
            else:
                stats[t1]["L"] += 1
    return stats


def build_dataframe(stats, divisions, season_df, team_to_season_map=None):
    """
    Construct a pandas DataFrame of standings from `stats` and `divisions`.
    Each row corresponds to one raw team_name.
    We use `team_to_season_map` to pick the exact historical season of each team
    (so that the “Team Display” includes the correct year suffix).
    Returns: (df, auto_assigned_flag)
      - df has columns: [Team, RawTeam, Division, Conference, GP, W, L, OTL, PTS, Win%, Rating]
      - auto_assigned_flag = True if any Conference was “Unknown” and then fixed.
    """
    real_div_lookup = dict(zip(season_df["Team"], season_df["Division"]))
    real_rating_lookup = dict(zip(season_df["Team"], season_df["Rating"]))

    temp_rows = []
    east_count = 0
    west_count = 0
    unknown_teams = []

    for team, s in stats.items():
        # 1) Determine simulated division
        sim_division = get_division(team, divisions)

        # 2) Find the exact Historical row that matches (team, chosen_season)
        if team_to_season_map and team in team_to_season_map:
            chosen_season = team_to_season_map[team]
            season_row = season_df[
                (season_df["Team"] == team) & (season_df["Season"] == chosen_season)
            ]
        else:
            # Fallback if no specific season-map provided
            season_row = season_df[season_df["Team"] == team]

        if not season_row.empty:
            season_str = str(season_row.iloc[0]["Season"])
            suffix = season_str[-2:]
            team_display = f"{team} {suffix}"
        else:
            team_display = team

        # 3) Compute PTS and Win%
        pts_val = s["W"] * 2 + s["OTL"]
        wp_val = round(s["W"] / s["GP"], 3) if s["GP"] > 0 else 0

        # 4) Determine conference: first try modern divisions, else fallback to CSV
        conference = get_conference(team, divisions, season_df)
        if conference == "East":
            east_count += 1
        elif conference == "West":
            west_count += 1
        else:
            unknown_teams.append(team)

        temp_rows.append({
            "Team":       team_display,
            "RawTeam":    team,
            "Division":   sim_division,
            "Conference": conference,
            "GP":         s["GP"],
            "W":          s["W"],
            "L":          s["L"],
            "OTL":        s["OTL"],
            "PTS":        pts_val,
            "Win%":       wp_val,
            "Rating":     real_rating_lookup.get(team, 75.0)
        })

    # 5) If any Conference is still Unknown, auto-assign evenly
    auto_assigned = False
    for row in temp_rows:
        if row["Conference"] == "Unknown":
            if east_count <= west_count:
                row["Conference"] = "East"
                east_count += 1
            else:
                row["Conference"] = "West"
                west_count += 1
            auto_assigned = True

    return pd.DataFrame(temp_rows), auto_assigned
