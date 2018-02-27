import pandas as pd
import matplotlib.pyplot as plt
from sklearn.preprocessing import OneHotEncoder

def data_prep(current_gameweek, hist_df):
    # Function to create input features and target labels for a given gameweek

    # Features should all come from before the gameweek we're predicting
    X = hist_df[hist_df['round'] == current_gameweek]


    # The target variable is the points scored in the gameweek
    next_week_points = hist_df[hist_df['round'] == current_gameweek + 1]
    next_week_points = next_week_points.loc[:, ('total_points', 'player_id')]
    X = X.merge(next_week_points, left_on='player_id', right_on='player_id', how='left', suffixes=['', '_next_week'])

    # Replace missing points values with zero
    X['total_points'].fillna(0)
    X['total_points_next_week'].fillna(0)

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