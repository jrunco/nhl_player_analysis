import numpy as np
import pandas as pd

from pathlib import Path
import sys

import seaborn as sns
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.offsetbox import OffsetImage, AnnotationBbox
import matplotlib.colors as mcolors
from matplotlib import rc
plt.rcParams.update({'font.size':22})

from tabulate import tabulate
from prettytable import PrettyTable, TableStyle
from IPython.display import display, HTML
from datetime import date, datetime, timedelta

from sklearn.cluster import KMeans

from nhlpy.nhl_client import NHLClient

from nhlpy.api.query.builder import QueryBuilder, QueryContext
from nhlpy.api.query.filters.draft import DraftQuery
from nhlpy.api.query.filters.season import SeasonQuery
from nhlpy.api.query.filters.game_type import GameTypeQuery
from nhlpy.api.query.filters.position import PositionQuery, PositionTypes
from nhlpy.api.query.filters.franchise import FranchiseQuery
from nhlpy.api.query.filters.shoot_catch import ShootCatchesQuery
from nhlpy.api.query.filters.status import StatusQuery
from nhlpy.api.query.filters.opponent import OpponentQuery
from nhlpy.api.query.filters.home_road import HomeRoadQuery
from nhlpy.api.query.filters.experience import ExperienceQuery
from nhlpy.api.query.filters.decision import DecisionQuery



from utils.function_library import find_player_id
from utils.function_library import toi_string_to_float
from utils.function_library import load_summary_statistics_for_skaters
from utils.function_library import load_realtime_statistics_for_skaters
from utils.function_library import load_faceoffwins_statistics_for_skaters


client = NHLClient(debug=False)



fp_goals = 6.0
fp_assists = 4.0
fp_plusminus = 1.5
fp_pp_goals = 2.0
fp_pp_assists = 2.0
fp_sh_goals = 4.0
fp_sh_assists = 1.0
fp_game_winning_goals = 1.0
fp_shots = 0.75
fp_hits = 0.40
fp_blocks = 1.25
fp_fowins = 0.15
fp_folosses = -0.15
fp_pims = 0.0

season = "20252026"

stat = 'fantasy_points_per_game'

positions = ["C", "L", "R", "D"]


def skater_single_season_tiers(season,
    fp_goals,
    fp_assists,
    fp_plusminus,
    fp_pp_goals,
    fp_pp_assists,
    fp_sh_goals,
    fp_sh_assists,
    fp_game_winning_goals,
    fp_shots,
    fp_hits,
    fp_blocks,
    fp_fowins,
    fp_folosses,
    fp_pims,
    stat,
    positions,
    ):

    skater_summary_query = load_summary_statistics_for_skaters(season, season)
    df_skater_summary_query = pd.DataFrame(skater_summary_query)
    df_skater_summary_query = df_skater_summary_query.sort_values(by='playerId')

    skater_realtime_query = load_realtime_statistics_for_skaters(season, season)
    df_skater_realtime_query = pd.DataFrame(skater_realtime_query)
    df_skater_realtime_query = df_skater_realtime_query.sort_values(by='playerId')

    skater_faceoffwins_query = load_faceoffwins_statistics_for_skaters(season, season)
    df_skater_faceoffwins_query = pd.DataFrame(skater_faceoffwins_query)
    df_skater_faceoffwins_query = df_skater_faceoffwins_query.sort_values(by='playerId')

    # merge the dataframes
    df_merge1 = pd.merge(df_skater_summary_query, df_skater_realtime_query, on='playerId', suffixes=('', '_drop'))
    df_merge1 = df_merge1.drop(columns=[col for col in df_merge1.columns if col.endswith('_drop')])

    # more merges if needed

    # final merge
    df_skater_stats = pd.merge(df_merge1, df_skater_faceoffwins_query, on='playerId', suffixes=('', '_drop'))
    df_skater_stats = df_skater_stats.drop(columns=[col for col in df_skater_stats.columns if col.endswith('_drop')])

    # grab only the positions wanted
    df_skater_stats = df_skater_stats[df_skater_stats["positionCode"].isin(positions)]

    # calculate total fantasy points
    tot_fantasy_points = (df_skater_stats["goals"]*fp_goals
        + df_skater_stats["assists"]*fp_assists
        + df_skater_stats["plusMinus"]*fp_plusminus
        + df_skater_stats["ppGoals"]*fp_pp_goals
        + (df_skater_stats["ppPoints"]-df_skater_stats["ppGoals"])*fp_pp_assists
        + df_skater_stats["shGoals"]*fp_sh_goals
        + (df_skater_stats["shPoints"]-df_skater_stats["shGoals"])*fp_sh_assists
        + df_skater_stats["gameWinningGoals"]*fp_game_winning_goals
        + df_skater_stats["shots"]*fp_shots
        + df_skater_stats["hits"]*fp_hits
        + df_skater_stats["blockedShots"]*fp_blocks
        + df_skater_stats["totalFaceoffWins"]*fp_fowins
        + df_skater_stats["totalFaceoffLosses"]*fp_folosses
        + df_skater_stats["penaltyMinutes"]*fp_pims
    )

    df_skater_stats["fantasy_points"] = tot_fantasy_points
    df_skater_stats["fantasy_points_per_game"] = df_skater_stats["fantasy_points"]/df_skater_stats["gamesPlayed"]

    # remove players that barely got any fantasy points
    df_skater_stats = df_skater_stats[df_skater_stats["fantasy_points"] >= 100.0]

    X_data = df_skater_stats[[stat]]
    kmeans = KMeans(n_clusters=10, random_state=71)
    df_skater_stats['cluster_seed'] = kmeans.fit_predict(X_data)

    # Sort cluster centers and get the index mapping
    # We use .mean(axis=1) to get a sorting scalar if data is multi-dimensional
    idx = np.argsort(kmeans.cluster_centers_.sum(axis=1))

    # Create a lookup array to remap the old labels to the sorted order
    lut = np.zeros_like(idx)
    lut[idx] = np.arange(len(idx))

    # Apply the mapping to the original labels
    ordered_labels = lut[kmeans.labels_]

    df_skater_stats['cluster_num'] = 10 - ordered_labels

    df_skater_stats_fp_sort = df_skater_stats.sort_values(by='fantasy_points_per_game', ascending=False)

    #cmap_colors = ['maroon', 'tab:red', 'orange', 'blueviolet', 'magenta', 'black', 'grey', 'cyan', 'blue', 'tab:green']
    cmap_colors = ['tab:green', 'blue', 'cyan', 'grey', 'black', 'magenta', 'blueviolet', 'orange', 'tab:red', 'maroon']
    cmap = mcolors.ListedColormap(cmap_colors)


    scatter = plt.scatter(df_skater_stats_fp_sort['skaterFullName'], df_skater_stats_fp_sort[stat], c=df_skater_stats_fp_sort['cluster_num'], cmap=cmap)
    #plt.xticks(rotation=45, ha='right')
    plt.xticks([])
    plt.title(stat)

    handles, labels = scatter.legend_elements(prop="colors")
    custom_labels = np.unique(df_skater_stats_fp_sort['cluster_num'].values)
    plt.legend(handles, custom_labels, title="Tiers", frameon=False, bbox_to_anchor=(1.05, 1.0), loc='upper left')

    plt.show()

    # print tables of player names
    for i in range(len(np.unique(df_skater_stats_fp_sort['cluster_num'].values))):

        tier_table_headers = ["Player Name", stat]
        tier_table = PrettyTable(tier_table_headers)
        tier_table.title = "\033[1m Tier %s \033[0m" % (np.unique(df_skater_stats_fp_sort['cluster_num'].values)[i])

        df_skater_tier = df_skater_stats_fp_sort[df_skater_stats_fp_sort["cluster_num"] == np.unique(df_skater_stats_fp_sort['cluster_num'].values)[i]]
        for j in range(len(df_skater_tier)):
            tier_table.add_row([df_skater_tier["skaterFullName"].values[j], np.round(df_skater_tier[stat].values[j], 2)])

        print(tier_table)

    return df_skater_stats_fp_sort





test = skater_single_season_tiers(season,
    fp_goals,
    fp_assists,
    fp_plusminus,
    fp_pp_goals,
    fp_pp_assists,
    fp_sh_goals,
    fp_sh_assists,
    fp_game_winning_goals,
    fp_shots,
    fp_hits,
    fp_blocks,
    fp_fowins,
    fp_folosses,
    fp_pims,
    stat,
    positions,
    )









"""
skater_summary_query = load_summary_statistics_for_skaters(season, season)
df_skater_summary_query = pd.DataFrame(skater_summary_query)
df_skater_summary_query = df_skater_summary_query.sort_values(by='playerId')

skater_realtime_query = load_realtime_statistics_for_skaters(season, season)
df_skater_realtime_query = pd.DataFrame(skater_realtime_query)
df_skater_realtime_query = df_skater_realtime_query.sort_values(by='playerId')

skater_faceoffwins_query = load_faceoffwins_statistics_for_skaters(season, season)
df_skater_faceoffwins_query = pd.DataFrame(skater_faceoffwins_query)
df_skater_faceoffwins_query = df_skater_faceoffwins_query.sort_values(by='playerId')


# merge the dataframes
df_merge1 = pd.merge(df_skater_summary_query, df_skater_realtime_query, on='playerId', suffixes=('', '_drop'))
df_merge1 = df_merge1.drop(columns=[col for col in df_merge1.columns if col.endswith('_drop')])

# more merges if needed

# final merge
df_skater_stats = pd.merge(df_merge1, df_skater_faceoffwins_query, on='playerId', suffixes=('', '_drop'))
df_skater_stats = df_skater_stats.drop(columns=[col for col in df_skater_stats.columns if col.endswith('_drop')])


# calculate total fantasy points
tot_fantasy_points = (df_skater_stats["goals"]*fp_goals
    + df_skater_stats["assists"]*fp_assists
    + df_skater_stats["plusMinus"]*fp_plusminus
    + df_skater_stats["ppGoals"]*fp_pp_goals
    + (df_skater_stats["ppPoints"]-df_skater_stats["ppGoals"])*fp_pp_assists
    + df_skater_stats["shGoals"]*fp_sh_goals
    + (df_skater_stats["shPoints"]-df_skater_stats["shGoals"])*fp_sh_assists
    + df_skater_stats["gameWinningGoals"]*fp_game_winning_goals
    + df_skater_stats["shots"]*fp_shots
    + df_skater_stats["hits"]*fp_hits
    + df_skater_stats["blockedShots"]*fp_blocks
    + df_skater_stats["totalFaceoffWins"]*fp_fowins
    + df_skater_stats["totalFaceoffLosses"]*fp_folosses
    + df_skater_stats["penaltyMinutes"]*fp_pims
)

df_skater_stats["fantasy_points"] = tot_fantasy_points
df_skater_stats["fantasy_points_per_game"] = df_skater_stats["fantasy_points"]/df_skater_stats["gamesPlayed"]

df_skater_stats = df_skater_stats[df_skater_stats["fantasy_points"] >= 100.0]

#kmeans = KMeans(n_clusters=10, random_state=0, n_init="auto").fit(df_skater_stats["fantasy_points"])

stat = 'fantasy_points'
X_data = df_skater_stats[[stat]]
kmeans = KMeans(n_clusters=10, random_state=71)
df_skater_stats['cluster_seed'] = kmeans.fit_predict(X_data)

# 3. Sort cluster centers and get the index mapping
# We use .mean(axis=1) to get a sorting scalar if data is multi-dimensional
idx = np.argsort(kmeans.cluster_centers_.sum(axis=1))

# 4. Create a lookup array to remap the old labels to the sorted order
lut = np.zeros_like(idx)
lut[idx] = np.arange(len(idx))

# 5. Apply the mapping to the original labels
ordered_labels = lut[kmeans.labels_]

df_skater_stats['cluster_num'] = ordered_labels

print(df_skater_stats[['skaterFullName', 'cluster_num', stat, 'cluster_seed']])

df_skater_stats_fp_sort = df_skater_stats.sort_values(by='fantasy_points', ascending=False)
for i in range(len(df_skater_stats_fp_sort)):
    print(df_skater_stats_fp_sort[['skaterFullName', 'cluster_num', stat]].values[i])

#for i in range(len(df_skater_stats_fp_sort)):
#    print(df_skater_stats_fp_sort[['skaterFullName', 'cluster_num', stat, 'cluster_seed']].values[i])


stat = 'fantasy_points_per_game'
X_data = df_skater_stats[[stat]]
kmeans = KMeans(n_clusters=10, random_state=71)
df_skater_stats['cluster_seed'] = kmeans.fit_predict(X_data)

# 3. Sort cluster centers and get the index mapping
# We use .mean(axis=1) to get a sorting scalar if data is multi-dimensional
idx = np.argsort(kmeans.cluster_centers_.sum(axis=1))

# 4. Create a lookup array to remap the old labels to the sorted order
lut = np.zeros_like(idx)
lut[idx] = np.arange(len(idx))

# 5. Apply the mapping to the original labels
ordered_labels = lut[kmeans.labels_]

df_skater_stats['cluster_num'] = 10 - ordered_labels

print(df_skater_stats[['skaterFullName', 'cluster_num', stat, 'cluster_seed']])

df_skater_stats_fp_sort = df_skater_stats.sort_values(by='fantasy_points_per_game', ascending=False)
#for i in range(len(df_skater_stats_fp_sort)):
#    print(df_skater_stats_fp_sort[['skaterFullName', 'cluster_num', stat]].values[i])


#cmap_colors = ['maroon', 'tab:red', 'orange', 'blueviolet', 'magenta', 'black', 'grey', 'cyan', 'blue', 'tab:green']
cmap_colors = ['tab:green', 'blue', 'cyan', 'grey', 'black', 'magenta', 'blueviolet', 'orange', 'tab:red', 'maroon']
cmap = mcolors.ListedColormap(cmap_colors)


scatter = plt.scatter(df_skater_stats_fp_sort['skaterFullName'], df_skater_stats_fp_sort[stat], c=df_skater_stats_fp_sort['cluster_num'], cmap=cmap)
#plt.xticks(rotation=45, ha='right')
plt.xticks([])
plt.title(stat)

handles, labels = scatter.legend_elements(prop="colors")
custom_labels = np.unique(df_skater_stats_fp_sort['cluster_num'].values)
plt.legend(handles, custom_labels, title="Tiers")

plt.show()

# print tables
for i in range(len(np.unique(df_skater_stats_fp_sort['cluster_num'].values))):

    tier_table_headers = ["Player Name", stat]
    tier_table = PrettyTable(tier_table_headers)
    tier_table.title = "\033[1m Tier %s \033[0m" % (np.unique(df_skater_stats_fp_sort['cluster_num'].values)[i])

    df_skater_tier = df_skater_stats_fp_sort[df_skater_stats_fp_sort["cluster_num"] == np.unique(df_skater_stats_fp_sort['cluster_num'].values)[i]]
    for j in range(len(df_skater_tier)):
        tier_table.add_row([df_skater_tier["skaterFullName"].values[j], np.round(df_skater_tier[stat].values[j], 2)])

    print(tier_table)

"""








"""
example
# 1. Sample DataFrame
df = pd.DataFrame({
    'X': [1.2, 1.5, 10.1, 10.5, 3.0, 12.0],
    'Y': ['Apple', 'Banana', 'Carrot', 'Dill', 'Eggplant', 'Fig']
})

# 2. Extract column X and reshape it to 2D array (required by scikit-learn)
X_data = df[['X']]

# 3. Initialize and fit the KMeans model
kmeans = KMeans(n_clusters=2, random_state=42)
df['Cluster'] = kmeans.fit_predict(X_data)

# 4. See what cluster column Y was grouped into
print(df[['Y', 'Cluster', 'X']])

"""




###
