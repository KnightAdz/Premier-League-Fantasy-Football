import pandas as pd
import matplotlib.pyplot as plt
from sklearn.preprocessing import OneHotEncoder


def data_prep(current_gameweek, hist_df, team_df, plyr_df, next_game_df=0):
    # Function to create input features and target labels for a given gameweek

    # Features should all come from before the gameweek we're predicting
    X = hist_df[hist_df['round'] == current_gameweek]

    # The target variable is the points scored in the gameweek, and we want to pull more features so lets grab that gameweek
    next_week_df = hist_df[hist_df['round'] == current_gameweek + 1]

    # Target variable
    next_week_points = next_week_df.loc[:, ('total_points', 'player_id')]
    X = X.merge(next_week_points, left_on='player_id', right_on='player_id', how='left', suffixes=['', '_next_week'])

    # Replace missing points values with zero
    X['total_points'].fillna(0)
    X['total_points_next_week'].fillna(0)


    ### PLAYERS INFO

    # Get information from the player dataset
    plyr_info = plyr_df[['first_name', 'id', 'news', 'news_added', 'second_name', 'squad_number', 'status', 'team']]
    # Don't include unavailable players (those out on loan etc.)
    X = X.merge(plyr_info, left_on='player_id', right_on='id', how='left')
    X = X[X['status'] != 'u']


    ### TEAMS INFO

    # Many of the team_df columns hold garbage, only take the useful ones
    team_cols = ['id', 'short_name', 'strength', 'strength_attack_away',
                 'strength_attack_home', 'strength_defence_away',
                 'strength_defence_home', 'strength_overall_away', 'strength_overall_home']

    # Join on the team info for the player's team
    X = X.merge(team_df[team_cols], left_on='team', right_on='id', how='left', suffixes=['','_own_team'])

    # Include the team to be played next gameweek, and their scores
    # For real predictions we will need to use next_game_df, but for history we can cheat
    if next_game_df == 0:
        # Get the opponent team id for each player in the next gameweek
        next_opponent = next_week_df.loc[:, ('player_id','opponent_team')]

        # Join on the team info for the next opponent
        next_opponent = next_opponent.merge(team_df[team_cols], left_on='opponent_team', right_on='id', how='left', suffixes=['','_opponent_team'])
    else:
        # Use the next gameweek info
        next_opponent = 0

    # Join the team info back into the main dataframe
    X = X.merge(next_opponent, left_on='player_id', right_on='player_id', how='left', suffixes=['', '_next_week'])




    # Should drop player id and some others as it doesn't mean anything
    # Also, create features from previous weeks too


    # For now, drop non-numeric columns
    X = X._get_numeric_data()

    return X


def merge_preds_and_players(X, y, plyr_df):
    # Combine predictions with player names to allow inspection of results
    ids = X['player_id']
    names = plyr_df[['id', 'web_name']]

    preds_df = pd.DataFrame(data={'player_id': ids, 'predicted_score': y})

    preds_df = preds_df.merge(names, left_on='player_id', right_on='id', how='left')
    preds_df = preds_df.drop('id', axis=1)

    return preds_df

def plot_feature_importance(X, model, threshold=0.01):
    # Plot a bar chart of the feature importances
    feature_importances = pd.DataFrame(data={'Feature':X.columns,'Importance':model.feature_importances_})
    feature_importances = feature_importances.sort_values(by='Importance')
    y = range(feature_importances[feature_importances['Importance']>threshold].shape[0])
    plt.barh(y,feature_importances[feature_importances['Importance']>threshold].Importance)
    plt.yticks(y,feature_importances['Feature'])
    plt.show()