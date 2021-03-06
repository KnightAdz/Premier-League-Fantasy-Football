import pandas as pd
import matplotlib.pyplot as plt
from sklearn.preprocessing import OneHotEncoder


def data_prep(current_gameweek, hist_df, team_df, plyr_df, next_game_df=0):
    # Function to create input features and target labels for a given gameweek

    # Features should all come from before the gameweek we're predicting for
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
    # element_type is the position e.g. goalkeeper, defender, midfielder, attacker
    plyr_info = plyr_df[['first_name', 'id', 'news', 'news_added', 'second_name', 'squad_number', 'status', 'team', 'element_type']]

    ### TEAMS INFO
    X = X.merge(plyr_info, left_on='player_id', right_on='id', how='left')

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

    # Team should be one-hot encoded for best results
    # TODO: Will this break in gameweeks where some teams don't play?
    #X = pd.concat([X,pd.get_dummies(next_opponent['opponent_team_next_week'])])

    ### FEATURE ENGINEERING


    # Average of past scores
#    points = hist_df[hist_df['round'] <= current_gameweek][['player_id', 'round', 'total_points']].set_index(['player_id', 'round'])
#    points = points.unstack()
#    points.columns = points.columns.get_level_values(1).fillna(0)
#    points.columns = ['wk' + str(x) for x in points.columns]

#    X['avg_pts_last_3wks'] = get_past_wks(points, 3).mean(axis=1).values
#    X['avg_pts_last_5wks'] = get_past_wks(points, 5).mean(axis=1).values
#    X['avg_pts_last_10wks'] = get_past_wks(points, 10).mean(axis=1).values
#    X['avg_pts_last_allwks'] = get_past_wks(points, 40).mean(axis=1).values

#    X['max_pts_last_3wks'] = get_past_wks(points, 3).max(axis=1).values
#    X['max_pts_last_5wks'] = get_past_wks(points, 5).max(axis=1).values
#    X['max_pts_last_10wks'] = get_past_wks(points, 10).max(axis=1).values
#    X['max_pts_allwks'] = get_past_wks(points, 40).max(axis=1).values

 #   X['min_pts_last_3wks'] = get_past_wks(points, 3).min(axis=1).values
 #   X['min_pts_last_5wks'] = get_past_wks(points, 5).min(axis=1).values
 #   X['min_pts_last_10wks'] = get_past_wks(points, 10).min(axis=1).values
  #  X['min_pts_allwks'] = get_past_wks(points, 40).min(axis=1).values

    X = historical_features(X, hist_df, current_gameweek, 'total_points')
    X = historical_features(X, hist_df, current_gameweek, 'selected')
    X = historical_features(X, hist_df, current_gameweek, 'minutes')
    X = historical_features(X, hist_df, current_gameweek, 'completed_passes')
    X = historical_features(X, hist_df, current_gameweek, 'transfers_in')

    # Should drop player id and some others as it doesn't mean anything
    # Also, create features from previous weeks too


    # Don't include unavailable players (those out on loan etc.)

    # Remove unfit players
    X = X[X['status'] != 'u']

    # For now, drop non-numeric columns
    X = X._get_numeric_data()

    return X

def historical_features(X_df,h_df,current_gameweek,target_col, wks_back=[3,5,10,40]):
    # Average of past selection scores
    selects = h_df[h_df['round'] <= current_gameweek][['player_id', 'round', target_col]].set_index(['player_id', 'round'])
    selects = selects.unstack()
    selects.columns = selects.columns.get_level_values(1).fillna(0)
    selects.columns = ['wk' + str(x) for x in selects.columns]

    for i in wks_back:
        X_df['avg_'+target_col+'_last_'+str(i)+'wks'] = get_past_wks(selects, i).mean(axis=1).values

    return X_df



def get_past_wks(df, wks_back):
    # Given a dataframe with columns named 'wk1','wk2' etc, return the last number of
    n_cols = df.columns.shape[0]
    start = n_cols-wks_back
    if start < 1:
        start = 1
    colnames = ['wk'+str(i) for i in range(start, n_cols+1)]
    return df[colnames]


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
    feature_importances = feature_importances.sort_values(by='Importance', ascending=False)
    y = range(feature_importances[feature_importances['Importance']>threshold].shape[0])
    plt.barh(y,feature_importances[feature_importances['Importance']>threshold].Importance)
    plt.yticks(y,feature_importances['Feature'])
    plt.show()