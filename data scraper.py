import urllib.request


import requests
import json
import csv
import argparse
import pandas as pd
import random

FPL_URL = "https://fantasy.premierleague.com/drf/"
USER_SUMMARY_SUBURL = "element-summary/"
LEAGUE_CLASSIC_STANDING_SUBURL = "leagues-classic-standings/"
LEAGUE_H2H_STANDING_SUBURL = "leagues-h2h-standings/"
TEAM_ENTRY_SUBURL = "entry/"
PLAYERS_INFO_SUBURL = "bootstrap-static"
PLAYERS_INFO_FILENAME = "allPlayersInfo.json"

USER_SUMMARY_URL = FPL_URL + USER_SUMMARY_SUBURL
PLAYERS_INFO_URL = FPL_URL + PLAYERS_INFO_SUBURL
START_PAGE = 1


# Player positions and counts
positions = ['GKP','DEF','MID','FWD']
max_pos = [2,5,5,3]
legit_formations = [    [1,5,4,1],
                        [1,4,4,2],
                        [1,3,5,2],
                        [1,4,3,3],
                        [1,3,4,3],
                        [1,4,5,1]   ]

# Download all player data: https://fantasy.premierleague.com/drf/bootstrap-static
def get_players_info():
    r = requests.get(PLAYERS_INFO_URL)
    jsonResponse = r.json()
    with open(PLAYERS_INFO_FILENAME, 'w') as outfile:
        json.dump(jsonResponse, outfile)


def player_name(plyr_info, i):
    return plyr_info['elements'][i]['first_name'] + " " + plyr_info['elements'][i]['second_name']


def position(plyr_info, i):
    return plyr_info['elements'][i]['singular_name_short']


def total_points(plyr_info, i):
    if 'total_points' not in plyr_info['elements'][i]:
        return 0
    else:
        return plyr_info['elements'][i]['total_points']


def cost(plyr_info, i):
    if 'now_cost' not in plyr_info['elements'][i]:
        return 0
    else:
        return plyr_info['elements'][i]['now_cost']/10


def points_per_pound(plyr_info, i):
    return int(total_points(plyr_info,i))/float(cost(plyr_info,i))


def team(plyr_info, i):
    team_code = plyr_info['elements'][i]['team_code']
    for t in plyr_info['teams']:
        if t['code'] == team_code:
            return t['short_name']

def position(plyr_info, i):
    pos_code = plyr_info['elements'][i]['element_type']
    for p in plyr_info['element_types']:
        if p['id'] == pos_code:
            return p['singular_name_short']

def Score(squad):
    max_score = -9999

    # Take each legitimate formation
    for f in legit_formations:
        scoring_players = pd.DataFrame()
        # Take each position
        for pos in range(0,4):
            # Take the highest scoring players that fit in the formation
            pos_players = squad[squad['Position'] == positions[pos]]
            pos_players = pos_players.sort_values('Points', axis=0, ascending=False)
            high_score_players = pos_players.head(f[pos])
            scoring_players = scoring_players.append(high_score_players, ignore_index=True)
        if scoring_players['Points'].sum() > max_score:
            max_score = scoring_players['Points'].sum()
            best_players = scoring_players

    return max_score, best_players

def TooManyPlayerTeams(squad):
    error_teams = []
    # Take each legitimate formation
    for p in squad:
        count = 1
        t = p["Team"]
        if t not in error_teams:
            for p2 in squad:
                if p2["Team"] == t:
                    count += 1
            if count > 3:
                error_teams.append(t)

    return error_teams

def optimal_team(df, squad_size=15, budget=100):
    # Define variables
    max_per_team = 3

    # Strip out below average players
    df = df[df["PtsPerCost"] > df["PtsPerCost"].mean()]
    # Sort by pts per cost
    df = df.sort_values('PtsPerCost', axis=0, ascending=False)

    # Create new DataFrame to store the squad
    squad = pd.DataFrame()
    spent = 0
    #while spent > budget:
    #    df = df.sample(frac=1)
    # First, fill squad to maximise points per cost, then sort out other rules
    mp = 0
    for pos in positions:
        # Create a slice of players in that position
        pos_df = df[df['Position'] == pos]
        for pos2 in range(0,max_pos[mp]):
            # And narrow it to what we can afford
            funds = budget - spent
            pos_df = pos_df[pos_df['Cost'] <= funds]
            new_players = pos_df.head(1)
            squad = squad.append(new_players, ignore_index=True)
            spent += new_players["Cost"].sum()
            # Delete this player so we don't select a player we already have
            pos_df.drop(pos_df.index[:1], inplace=True)

        mp += 1

    spent = squad["Cost"].head(squad_size).sum()

    print(squad.head(squad_size))

    score, players = Score(squad)


    print("Squad points: ", score)
    print(players)
    print("Total cost: ", spent)


def main():
    #dest_folder = "D:\\Coding\\Fantasy Football photos\\Photos\\"

    # Team data?
    #urllib.request.urlretrieve("https://fantasy.premierleague.com/drf/element-summary/271")

    # Player data
    #get_players_info()
    with open(PLAYERS_INFO_FILENAME) as json_data:
        plyr_info = json.load(json_data)
        print(plyr_info)

    print(plyr_info['elements'][31])

    player_df = pd.DataFrame()
    for i in range(0, len(plyr_info['elements'])):
        df = pd.DataFrame(data={"Player": player_name(plyr_info,i),
                                "Points": total_points(plyr_info, i),
                                "Cost": cost(plyr_info, i),
                                "PtsPerCost": points_per_pound(plyr_info,i),
                                "Team": team(plyr_info,i),
                                "Position": position(plyr_info, i)},
                          index={i})
        player_df = player_df.append(df)

    player_df = player_df.sort("PtsPerCost")
    print(player_df.to_string())

    optimal_team(player_df)


if __name__ == "__main__":
    main()