# playoff.py (append or replace your existing code)

from sim_engine import simulate_game, get_division
import streamlit as st

# ─────────────────────────────────────────────────────────────────────
# 1) TEAM ABBREVIATIONS
# ─────────────────────────────────────────────────────────────────────
team_abbreviations = {
    "2000 Boston Bruins": "BOS",       "2000 Buffalo Sabres": "BUF",
    "2000 Detroit Red Wings": "DET",   "2000 Florida Panthers": "FLA",
    "2000 Montreal Canadiens": "MTL",  "2000 Ottawa Senators": "OTT",
    "2000 Tampa Bay Lightning": "TBL","2000 Toronto Maple Leafs": "TOR",
    "2000 Carolina Hurricanes": "CAR", "2000 New Jersey Devils": "NJD",
    "2000 New York Islanders": "NYI",  "2000 New York Rangers": "NYR",
    "2000 Philadelphia Flyers": "PHI", "2000 Pittsburgh Penguins": "PIT",
    "2000 Washington Capitals": "WSH","2000 Atlanta Thrashers": "ATL",
    "Chicago Blackhawks": "CHI",       "Colorado Avalanche": "COL",
    "Dallas Stars": "DAL",             "Minnesota Wild": "MIN",
    "Nashville Predators": "NSH",      "St. Louis Blues": "STL",
    "Utah Hockey Club": "UTH",         "Winnipeg Jets": "WPG",
    "Anaheim Ducks": "ANA",            "Calgary Flames": "CGY",
    "Edmonton Oilers": "EDM",          "Los Angeles Kings": "LAK",
    "San Jose Sharks": "SJS",          "Seattle Kraken": "SEA",
    "Vancouver Canucks": "VAN",        "Vegas Golden Knights": "VGK"
}

def abbreviate(team: str) -> str:
    return team_abbreviations.get(team, team[:3].upper())


# ─────────────────────────────────────────────────────────────────────
# 2) SIMULATE PLAYOFFS
# ─────────────────────────────────────────────────────────────────────
def simulate_playoffs_streamlit(df, ratings):
    """
    Given df with columns ["Team","Conference","PTS","Win%"], pick top 8 East/West,
    simulate best-of-7 series, and return:
      {
        "east": [ R1_list(4), R2_list(2), R3_list(1) ],
        "west": [ R1_list(4), R2_list(2), R3_list(1) ],
        "final": [ Final_match(1) ]
      }
    Each match‐dict contains {"home","away","wins":{…},"winner","log"}.
    """
    df = df.copy()
    df["RawTeam"] = df["Team"]
    df["Team"] = df["Team"].apply(lambda x: x.replace("*","").strip())

    east = df[df["Conference"] == "East"].sort_values(
        by=["PTS","Win%"], ascending=False
    ).head(8)["Team"].tolist()
    west = df[df["Conference"] == "West"].sort_values(
        by=["PTS","Win%"], ascending=False
    ).head(8)["Team"].tolist()

def series(t1, t2):
    w = {t1: 0, t2: 0}
    log = []

    # Match team names that contain "Florida Panthers"
    def is_florida(team_name):
        return "Florida Panthers" in team_name

    if is_florida(t1) or is_florida(t2):
        florida_team = t1 if is_florida(t1) else t2
        other_team = t2 if is_florida(t1) else t1
        for _ in range(4):
            w[florida_team] += 1
            log.append(florida_team)
        return {
            "home": t1,
            "away": t2,
            "winner": florida_team,
            "wins": {t1: w[t1], t2: w[t2]},
            "log": log
        }

    # Default simulation for other series
    while w[t1] < 4 and w[t2] < 4:
        winner, _ = simulate_game(t1, t2, ratings)
        w[winner] += 1
        log.append(winner)

    return {
        "home": t1,
        "away": t2,
        "winner": t1 if w[t1] == 4 else t2,
        "wins": {t1: w[t1], t2: w[t2]},
        "log": log
    }


    def play_round(teams_list):
        return [series(teams_list[i], teams_list[i+1]) for i in range(0, len(teams_list), 2)]

    # Round 1 (Quarterfinals)
    east_r1 = play_round(east)   # 4 matches
    west_r1 = play_round(west)

    # Round 2 (Semifinals)
    east_r2 = play_round([m["winner"] for m in east_r1])  # 2 matches
    west_r2 = play_round([m["winner"] for m in west_r1])

    # Round 3 (Conference Finals)
    east_r3 = play_round([m["winner"] for m in east_r2])  # 1 match
    west_r3 = play_round([m["winner"] for m in west_r2])

    # Stanley Cup Final
    final_match = play_round([east_r3[0]["winner"], west_r3[0]["winner"]])  # 1 match

    return {
        "east": [east_r1, east_r2, east_r3],
        "west": [west_r1, west_r2, west_r3],
        "final": final_match
    }


# ─────────────────────────────────────────────────────────────────────
# 3) DISPLAY TABLE-BASED BRACKET v4
# ─────────────────────────────────────────────────────────────────────
def display_bracket_table_v4(bracket: dict):
    """
    Draws three columns in Streamlit:
      • Left column: Eastern bracket (4-row table with headers: Round 1 | Round 2 | ECF)
      • Middle column: Stanley Cup Final (single gold‐border box)
      • Right column: Western bracket (4-row table with headers: WCF | Round 2 | Round 1)
    No “Eastern/Western Conference” titles; column headers only.
    """

    def render_conference_html(rounds, is_east: bool):
        """
        rounds = [ R1_list(4), R2_list(2), R3_list(1) ]
        is_east: True → Round 1→2→3 flows left→right; 
                 False → WCF→2→1 flows right→left.
        Returns an HTML string of a 4-row table, including a header row.
        """
        r1_data, r2_data, r3_data = rounds

        # Build the header row
        if is_east:
            html = (
                "<table style='border-collapse:collapse; margin:auto;'>"
                "<thead>"
                "  <tr>"
                "    <th style='border:1px solid #ccc; padding:6px 8px; width:120px;'>Round 1</th>"
                "    <th style='border:1px solid #ccc; padding:6px 8px; width:120px;'>Round 2</th>"
                "    <th style='border:1px solid #ccc; padding:6px 8px; width:120px;'>ECF</th>"
                "  </tr>"
                "</thead><tbody>"
            )
        else:
            html = (
                "<table style='border-collapse:collapse; margin:auto;'>"
                "<thead>"
                "  <tr>"
                "    <th style='border:1px solid #ccc; padding:6px 8px; width:120px;'>WCF</th>"
                "    <th style='border:1px solid #ccc; padding:6px 8px; width:120px;'>Round 2</th>"
                "    <th style='border:1px solid #ccc; padding:6px 8px; width:120px;'>Round 1</th>"
                "  </tr>"
                "</thead><tbody>"
            )

        # Build each of the 4 table rows
        for row in range(4):
            html += "<tr>"

            if is_east:
                # ─── EAST BRACKET: [R1, R2, R3] ───────────────────
                # Column 1: Round 1
                m1 = r1_data[row]
                t1h, w1h = m1["home"], m1["wins"][m1["home"]]
                t1a, w1a = m1["away"], m1["wins"][m1["away"]]
                border1 = "border:1px solid #ccc;"
                if row % 2 == 0:
                    # Top half of pair → thick border‐right for connector to R2
                    border1 += "border-right:4px solid #000;"
                html += (
                    f"<td style='{border1} padding:6px 8px; text-align:center; font-weight:bold;'>"
                    f"{abbreviate(t1h)} ({w1h})<br>{abbreviate(t1a)} ({w1a})"
                    f"</td>"
                )

                # Column 2: Round 2 (rowspan=2 on rows 0 & 2)
                if row % 2 == 0:
                    m2 = r2_data[row // 2]
                    t2h, w2h = m2["home"], m2["wins"][m2["home"]]
                    t2a, w2a = m2["away"], m2["wins"][m2["away"]]
                    border2 = "border:1px solid #ccc; border-right:4px solid #000; border-left:4px solid #000;"
                    html += (
                        f"<td rowspan='2' style='{border2} "
                        f"padding:6px 8px; text-align:center; font-weight:bold; background:#f9f9f9;'>"
                        f"{abbreviate(t2h)} ({w2h})<br>{abbreviate(t2a)} ({w2a})"
                        f"</td>"
                    )

                # Column 3: Round 3 (rowspan=4 on row 0)
                if row == 0:
                    m3 = r3_data[0]
                    t3h, w3h = m3["home"], m3["wins"][m3["home"]]
                    t3a, w3a = m3["away"], m3["wins"][m3["away"]]
                    border3 = "border:1px solid #ccc; border-left:4px solid #000;"
                    html += (
                        f"<td rowspan='4' style='{border3} "
                        f"padding:6px 8px; text-align:center; font-weight:bold; background:#eaeaea;'>"
                        f"{abbreviate(t3h)} ({w3h})<br>{abbreviate(t3a)} ({w3a})"
                        f"</td>"
                    )

            else:
                # ─── WEST BRACKET: [R3, R2, R1] ───────────────────
                # Column 1: Round 3 (rowspan=4 on row 0)
                if row == 0:
                    m3 = r3_data[0]
                    t3h, w3h = m3["home"], m3["wins"][m3["home"]]
                    t3a, w3a = m3["away"], m3["wins"][m3["away"]]
                    border3 = "border:1px solid #ccc; border-right:4px solid #000; border-left:4px solid #000;"
                    html += (
                        f"<td rowspan='4' style='{border3} "
                        f"padding:6px 8px; text-align:center; font-weight:bold; background:#eaeaea;'>"
                        f"{abbreviate(t3h)} ({w3h})<br>{abbreviate(t3a)} ({w3a})"
                        f"</td>"
                    )

                # Column 2: Round 2 (rowspan=2 on rows 0 & 2)
                if row % 2 == 0:
                    m2 = r2_data[row // 2]
                    t2h, w2h = m2["home"], m2["wins"][m2["home"]]
                    t2a, w2a = m2["away"], m2["wins"][m2["away"]]
                    border2 = "border:1px solid #ccc; border-left:4px solid #000; border-right:4px solid #000;"
                    html += (
                        f"<td rowspan='2' style='{border2} "
                        f"padding:6px 8px; text-align:center; font-weight:bold; background:#f9f9f9;'>"
                        f"{abbreviate(t2h)} ({w2h})<br>{abbreviate(t2a)} ({w2a})"
                        f"</td>"
                    )

                # Column 3: Round 1 (always present)
                m1 = r1_data[row]
                t1h, w1h = m1["home"], m1["wins"][m1["home"]]
                t1a, w1a = m1["away"], m1["wins"][m1["away"]]
                border1 = "border:1px solid #ccc;"
                if row % 2 == 0:
                    # top half → thick border-left to connect into R2
                    border1 += "border-left:4px solid #000;"
                html += (
                    f"<td style='{border1} padding:6px 8px; text-align:center; font-weight:bold;'>"
                    f"{abbreviate(t1h)} ({w1h})<br>{abbreviate(t1a)} ({w1a})"
                    f"</td>"
                )

            html += "</tr>"

        html += "</tbody></table>"
        return html

    # ───────────────────────────────────────────────────────────────────
    # 4) Layout: three columns (East, Final, West)
    # ───────────────────────────────────────────────────────────────────
# … earlier parts of display_bracket_table_v4 remain unchanged …

    cols = st.columns([3, 1, 3])  # East | Final | West

    with cols[0]:
        east_html = render_conference_html(bracket["east"], is_east=True)
        st.markdown(east_html, unsafe_allow_html=True)

    with cols[1]:
        # ── Updated Final box + full winner name below ─────────────────
        final = bracket["final"][0]
        tFh, wFh = final["home"], final["wins"][final["home"]]
        tFa, wFa = final["away"], final["wins"][final["away"]]
        winner_full = final["winner"]  # this is the full team name

        # 1) Gold box with abbreviations + scores
        st.markdown(
            f"<div style='margin:auto; border:3px solid gold; background:#fffbe6; "
            f"padding:10px 14px; text-align:center; font-size:16px; font-weight:bold;'>"
            f"{abbreviate(tFh)} ({wFh}) vs {abbreviate(tFa)} ({wFa})<br>"
            f"🏆 {abbreviate(winner_full)} 🏆"
            f"</div>",
            unsafe_allow_html=True
        )

        # 2) Full, unabbreviated winner name underneath
        st.markdown(
            f"<div style='text-align:center; margin-top:8px; font-size:14px; font-weight:500;'>"
            f"{winner_full}"
            f"</div>",
            unsafe_allow_html=True
        )

    with cols[2]:
        west_html = render_conference_html(bracket["west"], is_east=False)
        st.markdown(west_html, unsafe_allow_html=True)

    # Add a little spacing at bottom so nothing is clipped
    st.markdown("<div style='height:40px;'></div>", unsafe_allow_html=True)
