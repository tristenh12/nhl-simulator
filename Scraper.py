import os
import pandas as pd
from bs4 import BeautifulSoup

# === Paths ===
input_folder = "C:/Users/Tristan/Documents/nhl_sim/seasons"
output_csv = "teams.csv"

# === Rating Calculator ===
def pts_pct_to_rating(pts_pct):
    try:
        return round(60 + float(pts_pct) * 40, 1)
    except:
        return None

# === Known Divisions and Conferences ===
known_divisions = [
    "Adams", "Patrick", "Norris", "Smythe",
    "Atlantic", "Central", "Metropolitan", "Northeast", "Southeast",
    "Canadian", "Pacific", "North", "West", "East", "Midwest", "South"
]

known_conferences = [
    "Wales", "Campbell", "Eastern", "Western"
]

# === Abbreviation Map ===
abbreviation_map = {
    "Anaheim Ducks": "ANA", "Arizona Coyotes": "ARI", "Atlanta Flames": "ATL", "Atlanta Thrashers": "ATL",
    "Boston Bruins": "BOS", "Brooklyn Americans": "BRK", "Buffalo Sabres": "BUF", "Calgary Flames": "CGY",
    "California Golden Seals": "CGS", "Carolina Hurricanes": "CAR", "Chicago Blackhawks": "CHI",
    "Cleveland Barons": "CLE", "Colorado Avalanche": "COL", "Colorado Rockies": "CLR",
    "Columbus Blue Jackets": "CBJ", "Dallas Stars": "DAL", "Detroit Red Wings": "DET",
    "Edmonton Oilers": "EDM", "Florida Panthers": "FLA", "Hamilton Tigers": "HAM", "Hartford Whalers": "HFD",
    "Kansas City Scouts": "KCS", "Los Angeles Kings": "LAK", "Minnesota North Stars": "MNS",
    "Minnesota Wild": "MIN", "Montreal Canadiens": "MTL", "Montréal Canadiens": "MTL",
    "Montreal Maroons": "MMR", "Montreal Wanderers": "MWN", "Nashville Predators": "NSH",
    "New Jersey Devils": "NJD", "New York Americans": "NYA", "New York Islanders": "NYI",
    "New York Rangers": "NYR", "Oakland Seals": "OAK", "Ottawa Senators": "OTT", "Philadelphia Flyers": "PHI",
    "Phoenix Coyotes": "PHX", "Pittsburgh Penguins": "PIT", "Quebec Nordiques": "QUE", "San Jose Sharks": "SJS",
    "Seattle Kraken": "SEA", "St. Louis Blues": "STL", "Tampa Bay Lightning": "TBL",
    "Toronto Maple Leafs": "TOR", "Toronto Arenas": "TAN", "Toronto St. Patricks": "TSP",
    "Utah Hockey Club": "UTH", "Utah HC": "UTH",
    "Vancouver Canucks": "VAN", "Vegas Golden Knights": "VGK",
    "Washington Capitals": "WSH", "Winnipeg Jets": "WPG", "Winnipeg Jets (1979)": "WPG",
    "Winnipeg Jets (2011)": "WPG"
}

# === New: Independent Inference of Division and Conference ===
def infer_division_and_conference(text, table_id=None):
    division = "Unknown"
    conference = "Unknown"

    # Use table ID as primary signal
    if table_id:
        if "EAS" in table_id and "MET" not in table_id:
            division = "Atlantic"
            conference = "Eastern"
        elif "MET" in table_id:
            division = "Metropolitan"
            conference = "Eastern"
        elif "CEN" in table_id:
            division = "Central"
            conference = "Western"
        elif "PAC" in table_id:
            division = "Pacific"
            conference = "Western"
        elif "WES" in table_id:
            conference = "Western"
        elif "standings_EAS" in table_id:
            conference = "Eastern"

    # Add backup inference from heading text
    if text:
        lower_text = text.lower()
        for div in known_divisions:
            if div.lower() in lower_text:
                division = div
        for conf in known_conferences:
            if conf.lower() in lower_text:
                conference = conf

    return division, conference

# === Main Loop ===
all_data = []

for filename in os.listdir(input_folder):
    if filename.endswith(".html"):
        season = filename.split(" ")[0]  # e.g., "2014-15"
        with open(os.path.join(input_folder, filename), "r", encoding="utf-8") as f:
            soup = BeautifulSoup(f.read(), "html.parser")

        for table in soup.find_all("table"):
            if "standings" not in table.get("id", ""):
                continue

            table_id = table.get("id", "")
            heading = table.find_previous(["h2", "strong"])
            heading_text = heading.get_text(strip=True) if heading else ""

            division, conference = infer_division_and_conference(heading_text, table_id)

            for row in table.tbody.find_all("tr"):
                if row.get("class") and "thead" in row.get("class"):
                    continue

                try:
                    team_name = row.find("a").text.strip()
                    if team_name == "Utah HC":
                        team_name = "Utah Hockey Club"

                    win_pct = float(row.find_all("td")[-1].text.strip())
                except:
                    continue

                abbreviation = abbreviation_map.get(team_name, team_name[:3].upper())

                all_data.append({
                    "Season": season,
                    "Team": team_name,
                    "Abbreviation": abbreviation,
                    "Win%": win_pct,
                    "Rating": pts_pct_to_rating(win_pct),
                    "Division": division,
                    "Conference": conference
                })

# === Export to CSV ===
df = pd.DataFrame(all_data)
df.to_csv(output_csv, index=False)
print(f"✅ Saved {len(df)} rows to {output_csv}")
