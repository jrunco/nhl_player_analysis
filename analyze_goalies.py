
import numpy as np
import pandas as pd

from pathlib import Path
import sys

import seaborn as sns
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.offsetbox import OffsetImage, AnnotationBbox
from matplotlib import rc
plt.rcParams.update({'font.size':22})

from tabulate import tabulate
from prettytable import PrettyTable, TableStyle
from IPython.display import display, HTML
from datetime import date, datetime, timedelta

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


fp_games_started = 0.0
fp_wins = 5.0
fp_losses = 0.0
fp_goals_against = -3.0
fp_shots_against = 0.0
fp_saves = 0.5
fp_shutouts = 5.0


client = NHLClient()

# Get basic goalie stats
basic_goalie_stats = client.stats.goalie_stats_summary(
    start_season="20252026",
    end_season="20252026",
    limit=-1
)
df_basic_goalie_stats = pd.DataFrame(basic_goalie_stats)
df_basic_goalie_stats_sorted = df_basic_goalie_stats.sort_values(by='playerId')


# Get advanced goalie stats
adv_goalie_stats = client.stats.goalie_stats_summary(
    start_season="20252026",
    end_season="20252026",
    stats_type="advanced",
    limit=-1
)
df_adv_goalie_stats = pd.DataFrame(adv_goalie_stats)
df_adv_goalie_stats_sorted = df_adv_goalie_stats.sort_values(by='playerId')


df_all_goalie_stats = pd.merge(df_basic_goalie_stats, df_adv_goalie_stats, on="playerId", how='inner')

'''
# find common columns
common_cols = list(set(df_basic_goalie_stats_sorted.columns) & set(df_adv_goalie_stats_sorted.columns))
df_all_goalie_stats = pd.merge(df_basic_goalie_stats_sorted, df_adv_goalie_stats_sorted, on=common_cols, how='inner')
'''


# i can get game log for goalies
goalie_game_log = client.stats.player_game_log(
    player_id="8482137", # Yaroslav Askarov
    season_id="20252026",
    game_type=2  # Regular season
)
df_goalie_game_log = pd.DataFrame(goalie_game_log)

team_full_schedule = client.schedule.team_season_schedule(team_abbr="SJS", season="20252026")
df_team_full_schedule = pd.DataFrame(team_full_schedule)


'''
idea hub
- with both basic and advnaced season dfs i can get fantasy points and other useful metrics for 2+ players
    - this is good for 1 goalie analysis and 2+ goalie analysis
- with game log and schedule i can see how patterns on when 1 goalie starts and recent trends
    - this is good for just one goalie analysis
'''













"""
all_data = []
start = 0
limit = 10

while True:
    response = client.stats.goalie_stats_summary(
        start_season="20252026",
        end_season="20252026",
        limit=limit,
        start=start
    )

    total = response['total']
    batch_data = response['data']
    all_data.extend(batch_data)

    if len(all_data) >= total:
        break

    start += limit
"""

















###
