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
PLAYERS_INFO_FILENAME = "allPlayersInfo Wk"

USER_SUMMARY_URL = FPL_URL + USER_SUMMARY_SUBURL
PLAYERS_INFO_URL = FPL_URL + PLAYERS_INFO_SUBURL
START_PAGE = 1

def gen_filename(week_number=1):
    return PLAYERS_INFO_FILENAME + str(week_number) + ".json"


def download_main_file():
    # Download all player data, save as a json and return a dataframe
    r = requests.get(PLAYERS_INFO_URL)
    jsonResponse = r.json()

    next_game_df = pd.DataFrame(data=jsonResponse['next_event_fixtures'])
    current_week = get_current_week(next_game_df)

    filename = gen_filename(current_week)

    with open(filename, 'w') as outfile:
        json.dump(jsonResponse, outfile)

    return current_week

def get_current_week(next_event_df):
    return next_event_df['event'].head(1)[0]

def load_main_data(week_number):
    filename = gen_filename(week_number)

    with open(filename) as json_data:
        jsonResponse = json.load(json_data)

    plyr_df = pd.DataFrame(data=jsonResponse['elements'])
    team_df = pd.DataFrame(data=jsonResponse['teams'])
    next_game_df = pd.DataFrame(data=jsonResponse['next_event_fixtures'])

    return plyr_df, team_df, next_game_df

def load_player_histories():
    return pd.DataFrame.from_csv('allhist.csv', index_col=None)

def download_player_histories(player_ids):
    # Given a list of player ids, download the player history for this year into its own file
    for p in player_ids:
        url = USER_SUMMARY_URL + "/" + str(p)
        r = requests.get(url)
        jsonResponse = r.json()
        #with open(str(p)+'.json', 'w') as outfile:
        #    json.dump(jsonResponse, outfile)

        history_df = pd.DataFrame(data=jsonResponse['history'])
        #history_df.to_csv(str(p)+".csv", index=False)

        history_df['player_id'] = p

        with open('allhist.csv', 'a') as f:
            header = f.tell() == 0
            history_df.to_csv(f, header=header, index=False)


def get_FPL_data():
    # Download all data from the FPL website and return DataFrames with the data in

    # Download the main data and get the current week number
    week_number = download_main_file()

    # Load the json into DataFrames
    plyr_df, team_df, next_game_df = load_main_data(week_number)

    plyr_ids = plyr_df['id']

    # Get the historic gameweek data for each player, save as csvs
    download_player_histories(plyr_ids)

    # Load player ids
    history_df = load_player_histories()

    return week_number, plyr_df, team_df, next_game_df, history_df

def load_FPL_data(week_number):
    # Load data from disk as DataFrames

    # Load the json into DataFrames
    plyr_df, team_df, next_game_df = load_main_data(week_number)

    # Load player ids
    history_df = load_player_histories()

    return week_number, plyr_df, team_df, next_game_df, history_df