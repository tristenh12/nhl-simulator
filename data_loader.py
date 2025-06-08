import pandas as pd

def load_teams(season=None):
    path = r"C:\Users\Tristan\Documents\nhl_sim\data\teams_alignment_complete.csv"
    
    try:
        df = pd.read_csv(path)
    except FileNotFoundError:
        print(f"❌ Could not find file at: {path}")
        return {}, {}

    if season:
        df = df[df["Season"] == season]

    divisions = {}
    ratings = {}

    for _, row in df.iterrows():
        team = row["Team"]
        division = row["Division"]
        rating = row["Rating"]
        if division not in divisions:
            divisions[division] = []
        divisions[division].append(team)
        ratings[team] = rating

    return divisions, ratings
