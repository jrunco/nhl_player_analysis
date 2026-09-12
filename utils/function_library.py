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



def find_player_id(player_name, season):

    client = NHLClient(debug=False)

    # find player and get player_id
    get_player = player_name
    #position = "forwards" # dict_keys(['forwards', 'defensemen', 'goalies'])
    season = season

    # Get all current teams
    teams = client.teams.teams()
    for team in teams:

        roster = client.teams.team_roster(team_abbr=team["abbr"], season="20252026")
        for position in roster:
            for player in roster[position]:
                if player["firstName"]["default"] + " " + player["lastName"]["default"] == get_player:
                    player_id = player["id"]

    return player_id


def toi_string_to_float(df, str_param_name, float_param_name):

    # convert avgToi from a string to a float
    minutes = np.zeros(len(df))
    seconds = np.zeros(len(df))
    for i in range(len(df)):
        minutes[i], seconds[i] = map(int, df[str_param_name].values[i].split(":"))
    df[float_param_name] = minutes + (seconds / 60.)

    return df


def get_dates_and_weekdays(start_str, end_str, date_format="%Y-%m-%d"):
    # Convert string inputs to datetime objects
    start_date = datetime.strptime(start_str, date_format)
    end_date = datetime.strptime(end_str, date_format)

    date_strings = []
    days_of_week = []

    current_date = start_date
    # Loop inclusively from start_date to end_date
    while current_date <= end_date:
        # Append date formatted as a string
        date_strings.append(current_date.strftime(date_format))

        # Append the full name of the day of the week (e.g., 'Monday')
        # Use "%a" if you want short names instead (e.g., 'Mon')
        days_of_week.append(current_date.strftime("%A"))

        # Move to the next day
        current_date += timedelta(days=1)

    return date_strings, days_of_week


def format_table_stats(stat_arr, stat_name):

    idx_max = np.argmax(stat_arr)+1
    idx_min = np.argmin(stat_arr)+1

    stat_arr_obj = stat_arr.astype(object)
    #stat_arr_obj = np.array([f"{x:.2f}" for x in stat_arr_obj], dtype=object)
    stat_arr_obj = np.array([f"{x:g}" for x in stat_arr_obj], dtype=object)
    stat_arr_obj = np.insert(stat_arr_obj, 0, stat_name)
    '''
    # Find index of the largest value
    stat_arr = np.insert(stat_arr, 0, -9999.)
    idx_max = np.argmax(stat_arr)
    # Find index of the smallest value
    stat_arr[0] = np.inf
    idx_min = np.argmin(stat_arr)
    '''
    # Create row data, bolding the largest value
    '''
    row_data = [
        str(val) if i != idx_max else f"\033[1;92m{val}\033[0m"
        #str(val) if i != idx_max f"\033[1;31m{val}\033[0m" elif i != idx_min else f"\033[1;92m{val}\033[0m"
        for i, val in enumerate(stat_arr_obj)
    ]
    '''
    row_data = [""] * len(stat_arr_obj)
    for i, val in enumerate(stat_arr_obj):
        if i == idx_max:
            row_data[i] = f"\033[1;92m{val}\033[0m"
        elif i == idx_min:
            row_data[i] = f"\033[1;31m{val}\033[0m"
        else:
            row_data[i] = str(val)

    return row_data



def format_schedule_stats(stat_arr, stat_name):

    stat_arr_obj = stat_arr.astype(object)
    stat_arr_obj = np.array([f"{x:g}" for x in stat_arr_obj], dtype=object)
    stat_arr_obj = np.insert(stat_arr_obj, 0, stat_name)

    row_data = [""] * len(stat_arr_obj)
    for i, val in enumerate(stat_arr_obj):
        row_data[i] = str(val)

        '''
        # consider something like this if I want to bold rows
        if i == 0:
            continue
        elif i == 1:
            if val > 3:
                row_data[i] = f"\033[1;92m{val}\033[0m"
            elif val < 3:
                row_data[i] = f"\033[1;31m{val}\033[0m"
            else:
                row_data[i] = str(val)
        '''
    return row_data



def load_summary_statistics_for_skaters(season_start, season_end, limit: int = 100):
    #from nhlpy.api.query.builder import QueryBuilder, QueryContext
    #from nhlpy.api.query.filters.season import SeasonQuery
    #from nhlpy.api.query.filters.game_type import GameTypeQuery

    filters = [
    SeasonQuery(season_start=season_start, season_end=season_end),
    GameTypeQuery(game_type="2"),
    #OpponentQuery(opponent_franchise_id="2"),
    ]
    context: QueryContext = QueryBuilder().build(filters=filters)
    all_data = []
    start = 0

    client = NHLClient(debug=False)

    while True:
        response = client.stats.skater_stats_with_query_context(
            report_type='summary',
            query_context=context,
            aggregate=True,
            limit=limit,
            start=start
        )

        total = response['total']
        batch_data = response['data']
        all_data.extend(batch_data)

        if len(all_data) >= total:
            break

        start += limit

    return all_data


def load_realtime_statistics_for_skaters(season_start, season_end, limit: int = 100):

    filters = [
    SeasonQuery(season_start=season_start, season_end=season_end),
    GameTypeQuery(game_type="2"),
    #OpponentQuery(opponent_franchise_id="2"),
    ]
    context: QueryContext = QueryBuilder().build(filters=filters)
    all_data = []
    start = 0

    client = NHLClient(debug=False)

    while True:
        response = client.stats.skater_stats_with_query_context(
            report_type='realtime',
            query_context=context,
            aggregate=True,
            limit=limit,
            start=start
        )

        total = response['total']
        batch_data = response['data']
        all_data.extend(batch_data)

        if len(all_data) >= total:
            break

        start += limit

    return all_data


def load_faceoffwins_statistics_for_skaters(season_start, season_end, limit: int = 100):

    filters = [
    SeasonQuery(season_start=season_start, season_end=season_end),
    GameTypeQuery(game_type="2"),
    #OpponentQuery(opponent_franchise_id="2"),
    ]
    context: QueryContext = QueryBuilder().build(filters=filters)
    all_data = []
    start = 0

    client = NHLClient(debug=False)

    while True:
        response = client.stats.skater_stats_with_query_context(
            report_type='faceoffwins',
            query_context=context,
            aggregate=True,
            limit=limit,
            start=start
        )

        total = response['total']
        batch_data = response['data']
        all_data.extend(batch_data)

        if len(all_data) >= total:
            break

        start += limit

    return all_data


def skater_single_season_fantasy_points(skater_name,
    season,
    fantasy_points_goals,
    fantasy_points_assists,
    fantasy_points_plusminus,
    fantasy_points_pp_goals,
    fantasy_points_pp_assists,
    fantasy_points_sh_goals,
    fantasy_points_sh_assists,
    fantasy_points_game_winning_goals,
    fantasy_points_shots,
    fantasy_points_hits,
    fantasy_points_blocks,
    fantasy_points_fowins,
    fantasy_points_folosses,
    fantasy_points_pims,
    ):

    skater_to_grab = skater_name

    start_season = season
    end_season = season

    # do an initial query to see if player name exists

    skater_summary_query = load_summary_statistics_for_skaters(start_season, end_season)
    skater_realtime_query = load_realtime_statistics_for_skaters(start_season, end_season)
    skater_faceoffwins_query = load_faceoffwins_statistics_for_skaters(start_season, end_season)

    name_grabbed = "N/A"
    for i in range(len(skater_summary_query)):
        if skater_summary_query[i]["skaterFullName"] == skater_to_grab:
            name_grabbed = skater_summary_query[i]["skaterFullName"]
            season_gamesPlayed = skater_summary_query[i]["gamesPlayed"]
            season_goals = skater_summary_query[i]["goals"]
            season_assists = skater_summary_query[i]["assists"]
            season_plusMinus = skater_summary_query[i]["plusMinus"]
            season_ppGoals = skater_summary_query[i]["ppGoals"]
            season_ppAssists = skater_summary_query[i]["ppPoints"] - skater_summary_query[i]["ppGoals"]
            season_shGoals = skater_summary_query[i]["shGoals"]
            season_shAssists = skater_summary_query[i]["shPoints"] - skater_summary_query[i]["shGoals"]
            season_gameWinningGoals = skater_summary_query[i]["gameWinningGoals"]
            season_shots = skater_summary_query[i]["shots"]
            season_penaltyMinutes = skater_summary_query[i]["penaltyMinutes"]

    for i in range(len(skater_realtime_query)):
        if skater_realtime_query[i]["skaterFullName"] == skater_to_grab:
            #name_grabbed = skater_realtime_query[i]["skaterFullName"]
            season_blockedShots = skater_realtime_query[i]["blockedShots"]
            season_hits = skater_realtime_query[i]["hits"]

    for i in range(len(skater_faceoffwins_query)):
        if skater_faceoffwins_query[i]["skaterFullName"] == skater_to_grab:
            #name_grabbed = skater_faceoffwins_query[i]["skaterFullName"]
            season_totalFaceoffWins = skater_faceoffwins_query[i]["totalFaceoffWins"]
            season_totalFaceoffLosses = skater_faceoffwins_query[i]["totalFaceoffLosses"]

    if name_grabbed == "N/A":
        print("Skater not found: error in defining player name or season")
    else:
        tot_fantasy_points = (season_goals*fantasy_points_goals
            + season_assists*fantasy_points_assists
            + season_plusMinus*fantasy_points_plusminus
            + season_ppGoals*fantasy_points_pp_goals
            + season_ppAssists*fantasy_points_pp_assists
            + season_shGoals*fantasy_points_sh_goals
            + season_shAssists*fantasy_points_sh_assists
            + season_gameWinningGoals*fantasy_points_game_winning_goals
            + season_shots*fantasy_points_shots
            + season_hits*fantasy_points_hits
            + season_blockedShots*fantasy_points_blocks
            + season_totalFaceoffWins*fantasy_points_fowins
            + season_totalFaceoffLosses*fantasy_points_folosses
            + season_penaltyMinutes*fantasy_points_pims
            )
        print(f"\033[1m%s fantasy points = %s\033[0m" % (name_grabbed, tot_fantasy_points))
        print(" ")
        print("# of games played = %s" % (season_gamesPlayed))
        print("Fantasy points per game = %s" % (round((tot_fantasy_points/season_gamesPlayed), 2)))
        print(" ")
        print(" ")
        table = PrettyTable(['Stat Name', 'Total Stats', 'Fantasy Points', 'Stats / Game', 'Fantasy Points / Game'])
        table.title = "Fantasy Points Breakdown by Stat"
        table.add_row(['Goals', season_goals, round((season_goals*fantasy_points_goals), 2), round(season_goals/season_gamesPlayed, 2), round((season_goals*fantasy_points_goals)/season_gamesPlayed, 2)])
        table.add_row(['Assists', season_assists, round((season_assists*fantasy_points_assists), 2), round(season_assists/season_gamesPlayed, 2), round((season_assists*fantasy_points_assists)/season_gamesPlayed, 2)])
        table.add_row(['Plus/Minus', season_plusMinus, round((season_plusMinus*fantasy_points_plusminus), 2), round(season_plusMinus/season_gamesPlayed, 2), round((season_plusMinus*fantasy_points_plusminus)/season_gamesPlayed, 2)])
        table.add_row(['Bonus for PP Goals', season_ppGoals, round((season_ppGoals*fantasy_points_pp_goals), 2), round(season_ppGoals/season_gamesPlayed, 2), round((season_ppGoals*fantasy_points_pp_goals)/season_gamesPlayed, 2)])
        table.add_row(['Bonus for PP Assists', season_ppAssists, round((season_ppAssists*fantasy_points_pp_assists), 2), round(season_ppAssists/season_gamesPlayed, 2), round((season_ppAssists*fantasy_points_pp_assists)/season_gamesPlayed, 2)])
        table.add_row(['Bonus for SH Goals', season_shGoals, round((season_shGoals*fantasy_points_sh_goals), 2), round(season_shGoals/season_gamesPlayed, 2), round((season_shGoals*fantasy_points_sh_goals)/season_gamesPlayed, 2)])
        table.add_row(['Bonus for SH Assists', season_shAssists, round((season_shAssists*fantasy_points_sh_assists), 2), round(season_shAssists/season_gamesPlayed, 2), round((season_shAssists*fantasy_points_sh_assists)/season_gamesPlayed, 2)])
        table.add_row(['Bonus for Game Winning Goals', season_gameWinningGoals, round((season_gameWinningGoals*fantasy_points_game_winning_goals), 2), round(season_gameWinningGoals/season_gamesPlayed, 2), round((season_gameWinningGoals*fantasy_points_game_winning_goals)/season_gamesPlayed, 2)])
        table.add_row(['Shots', season_shots, round((season_shots*fantasy_points_shots), 2), round(season_shots/season_gamesPlayed, 2), round((season_shots*fantasy_points_shots)/season_gamesPlayed, 2)])
        table.add_row(['Hits', season_hits, round((season_hits*fantasy_points_hits), 2), round(season_hits/season_gamesPlayed, 2), round((season_hits*fantasy_points_hits)/season_gamesPlayed, 2)])
        table.add_row(['Blocks', season_blockedShots, round((season_blockedShots*fantasy_points_blocks), 2), round(season_blockedShots/season_gamesPlayed, 2), round((season_blockedShots*fantasy_points_blocks)/season_gamesPlayed, 2)])
        table.add_row(['Face-offs', (season_totalFaceoffWins-season_totalFaceoffLosses), round(((season_totalFaceoffWins*fantasy_points_fowins)+(season_totalFaceoffLosses*fantasy_points_folosses)), 2), round((season_totalFaceoffWins-season_totalFaceoffLosses)/season_gamesPlayed, 2), round(((season_totalFaceoffWins*fantasy_points_fowins)+(season_totalFaceoffLosses*fantasy_points_folosses))/season_gamesPlayed, 2)])
        table.add_row(['PIMs', season_penaltyMinutes, round((season_penaltyMinutes*fantasy_points_pims), 2), round(season_penaltyMinutes/season_gamesPlayed, 2), round((season_penaltyMinutes*fantasy_points_pims)/season_gamesPlayed, 2)])
        #table.add_divider()
        #table.set_style(DOUBLE_BORDER)
        print(table)

    return tot_fantasy_points


def comp_multi_skaters(skater_names,
    season,
    fantasy_points_goals,
    fantasy_points_assists,
    fantasy_points_plusminus,
    fantasy_points_pp_goals,
    fantasy_points_pp_assists,
    fantasy_points_sh_goals,
    fantasy_points_sh_assists,
    fantasy_points_game_winning_goals,
    fantasy_points_shots,
    fantasy_points_hits,
    fantasy_points_blocks,
    fantasy_points_fowins,
    fantasy_points_folosses,
    fantasy_points_pims,
    ):

    start_season = season
    end_season = season

    # do an initial query to see if player name exists

    skater_summary_query = load_summary_statistics_for_skaters(start_season, end_season)
    skater_realtime_query = load_realtime_statistics_for_skaters(start_season, end_season)
    skater_faceoffwins_query = load_faceoffwins_statistics_for_skaters(start_season, end_season)

    skater_names_grabbed = ["N/A"] * len(skater_names)
    skater_season_gamesPlayed = np.zeros(len(skater_names))
    skater_season_timeOnIcePerGame = np.zeros(len(skater_names))
    skater_season_timeOnIcePerGame_min = np.zeros(len(skater_names))
    skater_season_goals = np.zeros(len(skater_names))
    skater_season_assists = np.zeros(len(skater_names))
    skater_season_plusMinus = np.zeros(len(skater_names))
    skater_season_ppGoals = np.zeros(len(skater_names))
    skater_season_ppAssists = np.zeros(len(skater_names))
    skater_season_shGoals = np.zeros(len(skater_names))
    skater_season_shAssists = np.zeros(len(skater_names))
    skater_season_gameWinningGoals = np.zeros(len(skater_names))
    skater_season_shots = np.zeros(len(skater_names))
    skater_season_penaltyMinutes = np.zeros(len(skater_names))
    skater_season_blockedShots = np.zeros(len(skater_names))
    skater_season_hits = np.zeros(len(skater_names))
    skater_season_totalFaceoffWins = np.zeros(len(skater_names))
    skater_season_totalFaceoffLosses = np.zeros(len(skater_names))

    for name in range(len(skater_names)):
        for i in range(len(skater_summary_query)):
            if skater_summary_query[i]["skaterFullName"] == skater_names[name]:
                skater_names_grabbed[name] = skater_summary_query[i]["skaterFullName"]
                skater_season_timeOnIcePerGame[name] = skater_summary_query[i]["timeOnIcePerGame"]
                skater_season_timeOnIcePerGame_min[name] = round(skater_summary_query[i]["timeOnIcePerGame"]/60., 2)
                skater_season_gamesPlayed[name] = skater_summary_query[i]["gamesPlayed"]
                skater_season_goals[name] = skater_summary_query[i]["goals"]
                skater_season_assists[name] = skater_summary_query[i]["assists"]
                skater_season_plusMinus[name] = skater_summary_query[i]["plusMinus"]
                skater_season_ppGoals[name] = skater_summary_query[i]["ppGoals"]
                skater_season_ppAssists[name] = skater_summary_query[i]["ppPoints"] - skater_summary_query[i]["ppGoals"]
                skater_season_shGoals[name] = skater_summary_query[i]["shGoals"]
                skater_season_shAssists[name] = skater_summary_query[i]["shPoints"] - skater_summary_query[i]["shGoals"]
                skater_season_gameWinningGoals[name] = skater_summary_query[i]["gameWinningGoals"]
                skater_season_shots[name] = skater_summary_query[i]["shots"]
                skater_season_penaltyMinutes[name] = skater_summary_query[i]["penaltyMinutes"]

        for i in range(len(skater_realtime_query)):
            if skater_realtime_query[i]["skaterFullName"] == skater_names[name]:
                skater_season_blockedShots[name] = skater_realtime_query[i]["blockedShots"]
                skater_season_hits[name] = skater_realtime_query[i]["hits"]

        for i in range(len(skater_faceoffwins_query)):
            if skater_faceoffwins_query[i]["skaterFullName"] == skater_names[name]:
                skater_season_totalFaceoffWins[name] = skater_faceoffwins_query[i]["totalFaceoffWins"]
                skater_season_totalFaceoffLosses[name] = skater_faceoffwins_query[i]["totalFaceoffLosses"]

        # get the stat / game
        skater_season_goals_per_game = np.zeros(len(skater_names))
        skater_season_assists_per_game = np.zeros(len(skater_names))
        skater_season_plusMinus_per_game = np.zeros(len(skater_names))
        skater_season_ppGoals_per_game = np.zeros(len(skater_names))
        skater_season_ppAssists_per_game = np.zeros(len(skater_names))
        skater_season_shGoals_per_game = np.zeros(len(skater_names))
        skater_season_shAssists_per_game = np.zeros(len(skater_names))
        skater_season_gameWinningGoals_per_game = np.zeros(len(skater_names))
        skater_season_shots_per_game = np.zeros(len(skater_names))
        skater_season_penaltyMinutes_per_game = np.zeros(len(skater_names))
        skater_season_blockedShots_per_game = np.zeros(len(skater_names))
        skater_season_hits_per_game = np.zeros(len(skater_names))
        skater_season_totalFaceoffWins_per_game = np.zeros(len(skater_names))
        skater_season_totalFaceoffLosses_per_game = np.zeros(len(skater_names))
        skater_season_penaltyMinutes_per_game = np.zeros(len(skater_names))

        # get the stat / 60 minutes
        skater_season_goals_per_60min = np.zeros(len(skater_names))
        skater_season_assists_per_60min = np.zeros(len(skater_names))
        skater_season_plusMinus_per_60min = np.zeros(len(skater_names))
        skater_season_ppGoals_per_60min = np.zeros(len(skater_names))
        skater_season_ppAssists_per_60min = np.zeros(len(skater_names))
        skater_season_shGoals_per_60min = np.zeros(len(skater_names))
        skater_season_shAssists_per_60min = np.zeros(len(skater_names))
        skater_season_gameWinningGoals_per_60min = np.zeros(len(skater_names))
        skater_season_shots_per_60min = np.zeros(len(skater_names))
        skater_season_penaltyMinutes_per_60min = np.zeros(len(skater_names))
        skater_season_blockedShots_per_60min = np.zeros(len(skater_names))
        skater_season_hits_per_60min = np.zeros(len(skater_names))
        skater_season_totalFaceoffWins_per_60min = np.zeros(len(skater_names))
        skater_season_totalFaceoffLosses_per_60min = np.zeros(len(skater_names))
        skater_season_penaltyMinutes_per_60min = np.zeros(len(skater_names))

        skater_names_tot_fantasy_points = np.zeros(len(skater_names))
        skater_names_fantasy_points_per_game = np.zeros(len(skater_names))

    for name in range(len(skater_names)):
        if skater_names[name] == "N/A":
            print("Skater %s not found: error in defining player name or season" % (skater_names[name]))
        else:
            skater_names_tot_fantasy_points[name] = (skater_season_goals[name]*fantasy_points_goals
                + skater_season_assists[name]*fantasy_points_assists
                + skater_season_plusMinus[name]*fantasy_points_plusminus
                + skater_season_ppGoals[name]*fantasy_points_pp_goals
                + skater_season_ppAssists[name]*fantasy_points_pp_assists
                + skater_season_shGoals[name]*fantasy_points_sh_goals
                + skater_season_shAssists[name]*fantasy_points_sh_assists
                + skater_season_gameWinningGoals[name]*fantasy_points_game_winning_goals
                + skater_season_shots[name]*fantasy_points_shots
                + skater_season_hits[name]*fantasy_points_hits
                + skater_season_blockedShots[name]*fantasy_points_blocks
                + skater_season_totalFaceoffWins[name]*fantasy_points_fowins
                + skater_season_totalFaceoffLosses[name]*fantasy_points_folosses
                + skater_season_penaltyMinutes[name]*fantasy_points_pims
                )
            skater_names_fantasy_points_per_game[name] = round(skater_names_tot_fantasy_points[name]/skater_season_gamesPlayed[name], 2)

            # get stats per game
            skater_season_goals_per_game[name] = round(skater_season_goals[name]/skater_season_gamesPlayed[name], 2)
            skater_season_assists_per_game[name] = round(skater_season_assists[name]/skater_season_gamesPlayed[name], 2)
            skater_season_plusMinus_per_game[name] = round(skater_season_plusMinus[name]/skater_season_gamesPlayed[name], 2)
            skater_season_ppGoals_per_game[name] = round(skater_season_ppGoals[name]/skater_season_gamesPlayed[name], 2)
            skater_season_ppAssists_per_game[name] = round(skater_season_ppAssists[name]/skater_season_gamesPlayed[name], 2)
            skater_season_shGoals_per_game[name] = round(skater_season_shGoals[name]/skater_season_gamesPlayed[name], 2)
            skater_season_shAssists_per_game[name] = round(skater_season_shAssists[name]/skater_season_gamesPlayed[name], 2)
            skater_season_gameWinningGoals_per_game[name] = round(skater_season_gameWinningGoals[name]/skater_season_gamesPlayed[name], 2)
            skater_season_shots_per_game[name] = round(skater_season_shots[name]/skater_season_gamesPlayed[name], 2)
            skater_season_hits_per_game[name] = round(skater_season_hits[name]/skater_season_gamesPlayed[name], 2)
            skater_season_blockedShots_per_game[name] = round(skater_season_blockedShots[name]/skater_season_gamesPlayed[name], 2)
            skater_season_totalFaceoffWins_per_game[name] = round(skater_season_totalFaceoffWins[name]/skater_season_gamesPlayed[name], 2)
            skater_season_totalFaceoffLosses_per_game[name] = round(skater_season_totalFaceoffLosses[name]/skater_season_gamesPlayed[name], 2)
            skater_season_penaltyMinutes_per_game[name] = round(skater_season_penaltyMinutes[name]/skater_season_gamesPlayed[name], 2)

            # get stats per 60 minutes
            skater_season_goals_per_60min[name] = round(60.*skater_season_goals_per_game[name]/skater_season_timeOnIcePerGame_min[name], 2)
            skater_season_assists_per_60min[name] = round(60.*skater_season_assists_per_game[name]/skater_season_timeOnIcePerGame_min[name], 2)
            skater_season_plusMinus_per_60min[name] = round(60.*skater_season_plusMinus_per_game[name]/skater_season_timeOnIcePerGame_min[name], 2)
            skater_season_ppGoals_per_60min[name] = round(60.*skater_season_ppGoals_per_game[name]/skater_season_timeOnIcePerGame_min[name], 2)
            skater_season_ppAssists_per_60min[name] = round(60.*skater_season_ppAssists_per_game[name]/skater_season_timeOnIcePerGame_min[name], 2)
            skater_season_shGoals_per_60min[name] = round(60.*skater_season_shGoals_per_game[name]/skater_season_timeOnIcePerGame_min[name], 2)
            skater_season_shAssists_per_60min[name] = round(60.*skater_season_shAssists_per_game[name]/skater_season_timeOnIcePerGame_min[name], 2)
            skater_season_gameWinningGoals_per_60min[name] = round(60.*skater_season_gameWinningGoals_per_game[name]/skater_season_timeOnIcePerGame_min[name], 2)
            skater_season_shots_per_60min[name] = round(60.*skater_season_shots_per_game[name]/skater_season_timeOnIcePerGame_min[name], 2)
            skater_season_hits_per_60min[name] = round(60.*skater_season_hits_per_game[name]/skater_season_timeOnIcePerGame_min[name], 2)
            skater_season_blockedShots_per_60min[name] = round(60.*skater_season_blockedShots_per_game[name]/skater_season_timeOnIcePerGame_min[name], 2)
            skater_season_totalFaceoffWins_per_60min[name] = round(60.*skater_season_totalFaceoffWins_per_game[name]/skater_season_timeOnIcePerGame_min[name], 2)
            skater_season_totalFaceoffLosses_per_60min[name] = round(60.*skater_season_totalFaceoffLosses_per_game[name]/skater_season_timeOnIcePerGame_min[name], 2)
            skater_season_penaltyMinutes_per_60min[name] = round(60.*skater_season_penaltyMinutes_per_game[name]/skater_season_timeOnIcePerGame_min[name], 2)

    skater_names_grabbed.insert(0, "Stat")

    fp_table_headers = [
        f"\033[1m{skater_names_grabbed[i]}\033[0m" for i in range(len(skater_names_grabbed))
    ]

    # Initialize PrettyTable with the dynamic headers
    fp_table = PrettyTable(fp_table_headers)
    fp_table.title = "\033[1mPlayer Fantasy Comparison\033[0m"

    table_fantasy_points_total = format_table_stats(skater_names_tot_fantasy_points, "Total Fantasy Points")
    fp_table.add_row(table_fantasy_points_total)

    table_fantasy_points_total = format_table_stats(skater_names_fantasy_points_per_game, "# of Fantasy Points per Game")
    fp_table.add_row(table_fantasy_points_total)

    print(fp_table)


    stats_headers = [
    f"\033[1m{skater_names_grabbed[i]}\033[0m" for i in range(len(skater_names_grabbed))
]

    # Initialize PrettyTable with the dynamic headers
    stats_table = PrettyTable(stats_headers)
    stats_table.title = "\033[1mPlayer Stats Comparison\033[0m"

    # games played
    table_season_games_played_total = format_table_stats(skater_season_gamesPlayed, "Games Played")
    stats_table.add_row(table_season_games_played_total)
    # average TOI
    table_season_toi_per_game = format_table_stats(skater_season_timeOnIcePerGame_min, "Average TOI")
    stats_table.add_row(table_season_toi_per_game)
    # goals
    stats_table.add_divider()
    table_season_goals_total = format_table_stats(skater_season_goals, "Total Goals")
    stats_table.add_row(table_season_goals_total)
    table_season_goals_per_game = format_table_stats(skater_season_goals_per_game, "# of Goals per Game")
    stats_table.add_row(table_season_goals_per_game)
    table_season_goals_per_60min = format_table_stats(skater_season_goals_per_60min, "# of Goals per 60 minutes")
    stats_table.add_row(table_season_goals_per_60min)
    # assists
    stats_table.add_divider()
    table_season_assists_total = format_table_stats(skater_season_assists, "Total Assists")
    stats_table.add_row(table_season_assists_total)
    table_season_assists_per_game = format_table_stats(skater_season_assists_per_game, "# of Assists per Game")
    stats_table.add_row(table_season_assists_per_game)
    table_season_assists_per_60min = format_table_stats(skater_season_assists_per_60min, "# of Assists per 60 minutes")
    stats_table.add_row(table_season_assists_per_60min)
    # +/-
    stats_table.add_divider()
    table_season_plusMinus_total = format_table_stats(skater_season_plusMinus, "Season +/-")
    stats_table.add_row(table_season_plusMinus_total)
    table_season_plusMinus_per_game = format_table_stats(skater_season_plusMinus_per_game, "Average +/- per Game")
    stats_table.add_row(table_season_plusMinus_per_game)
    table_season_plusMinus_per_60min = format_table_stats(skater_season_plusMinus_per_60min, "Average +/- per 60 minutes")
    stats_table.add_row(table_season_plusMinus_per_60min)
    # PP Goals
    stats_table.add_divider()
    table_season_ppGoals_total = format_table_stats(skater_season_ppGoals, "Season PP Goals")
    stats_table.add_row(table_season_ppGoals_total)
    table_season_ppGoals_per_game = format_table_stats(skater_season_ppGoals_per_game, "Average PP Goals per Game")
    stats_table.add_row(table_season_ppGoals_per_game)
    table_season_ppGoals_per_60min = format_table_stats(skater_season_ppGoals_per_60min, "Average # of PP Goals per 60 minutes")
    stats_table.add_row(table_season_ppGoals_per_60min)
    # PP Assists
    stats_table.add_divider()
    table_season_ppAssists_total = format_table_stats(skater_season_ppAssists, "Season PP Assists")
    stats_table.add_row(table_season_ppAssists_total)
    table_season_ppAssists_per_game = format_table_stats(skater_season_ppAssists_per_game, "Average PP Assists per Game")
    stats_table.add_row(table_season_ppAssists_per_game)
    table_season_ppAssists_per_60min = format_table_stats(skater_season_ppAssists_per_60min, "Average # of PP Assists per 60 minutes")
    stats_table.add_row(table_season_ppAssists_per_60min)
    # SH Goals
    stats_table.add_divider()
    table_season_shGoals_total = format_table_stats(skater_season_shGoals, "Season SH Goals")
    stats_table.add_row(table_season_shGoals_total)
    table_season_shGoals_per_game = format_table_stats(skater_season_shGoals_per_game, "Average SH Goals per Game")
    stats_table.add_row(table_season_shGoals_per_game)
    table_season_shGoals_per_60min = format_table_stats(skater_season_shGoals_per_60min, "# of SH Goals per 60 minutes")
    stats_table.add_row(table_season_shGoals_per_60min)
    # SH Assists
    stats_table.add_divider()
    table_season_shAssists_total = format_table_stats(skater_season_shAssists, "Season SH Assists")
    stats_table.add_row(table_season_shAssists_total)
    table_season_shAssists_per_game = format_table_stats(skater_season_shAssists_per_game, "Average SH Assists per Game")
    stats_table.add_row(table_season_shAssists_per_game)
    table_season_shAssists_per_60min = format_table_stats(skater_season_shAssists_per_60min, "Average # of SH Assists per 60 minutes")
    stats_table.add_row(table_season_shAssists_per_60min)
    # Game Winning Goals
    stats_table.add_divider()
    table_season_gameWinningGoals_total = format_table_stats(skater_season_gameWinningGoals, "Season Game Winning Goals")
    stats_table.add_row(table_season_gameWinningGoals_total)
    table_season_gameWinningGoals_per_game = format_table_stats(skater_season_gameWinningGoals_per_game, "Average # of Game Winning Goals per Game")
    stats_table.add_row(table_season_gameWinningGoals_per_game)
    table_season_gameWinningGoals_per_60min = format_table_stats(skater_season_gameWinningGoals_per_60min, "Average # of Game Winning Goals per 60 minutes")
    stats_table.add_row(table_season_gameWinningGoals_per_60min)
    # Shots
    stats_table.add_divider()
    table_season_shots_total = format_table_stats(skater_season_shots, "Season Shots")
    stats_table.add_row(table_season_shots_total)
    table_season_shots_per_game = format_table_stats(skater_season_shots_per_game, "Average # of Shots per Game")
    stats_table.add_row(table_season_shots_per_game)
    table_season_shots_per_60min = format_table_stats(skater_season_shots_per_60min, "Average # of Shots per 60 minutes")
    stats_table.add_row(table_season_shots_per_60min)
    # Hits
    stats_table.add_divider()
    table_season_hits_total = format_table_stats(skater_season_hits, "Season Hits")
    stats_table.add_row(table_season_hits_total)
    table_season_hits_per_game = format_table_stats(skater_season_hits_per_game, "Average # of Hits per Game")
    stats_table.add_row(table_season_hits_per_game)
    table_season_hits_per_60min = format_table_stats(skater_season_hits_per_60min, "Average # of Hits per 60 minutes")
    stats_table.add_row(table_season_hits_per_60min)
    # Blocked Shots
    stats_table.add_divider()
    table_season_blockedShots_total = format_table_stats(skater_season_blockedShots, "Season Blocked Shots")
    stats_table.add_row(table_season_blockedShots_total)
    table_season_blockedShots_per_game = format_table_stats(skater_season_blockedShots_per_game, "Average # of Blocked Shots per Game")
    stats_table.add_row(table_season_blockedShots_per_game)
    table_season_blockedShots_per_60min = format_table_stats(skater_season_blockedShots_per_60min, "Average # of Blocked Shots per 60 minutes")
    stats_table.add_row(table_season_blockedShots_per_60min)
    # FO Wins
    stats_table.add_divider()
    table_season_totalFaceoffWins_total = format_table_stats(skater_season_totalFaceoffWins, "Season FO Wins")
    stats_table.add_row(table_season_totalFaceoffWins_total)
    table_season_totalFaceoffWins_per_game = format_table_stats(skater_season_totalFaceoffWins_per_game, "Average # of FO Wins per Game")
    stats_table.add_row(table_season_totalFaceoffWins_per_game)
    table_season_totalFaceoffWins_per_60min = format_table_stats(skater_season_totalFaceoffWins_per_60min, "Average # of FO Wins per 60 minutes")
    stats_table.add_row(table_season_totalFaceoffWins_per_60min)
    # FO Loses
    stats_table.add_divider()
    table_season_totalFaceoffLosses_total = format_table_stats(skater_season_totalFaceoffLosses, "Season FO Losses")
    stats_table.add_row(table_season_totalFaceoffLosses_total)
    table_season_totalFaceoffLosses_per_game = format_table_stats(skater_season_totalFaceoffLosses_per_game, "Average # of FO Losses per Game")
    stats_table.add_row(table_season_totalFaceoffLosses_per_game)
    table_season_totalFaceoffLosses_per_60min = format_table_stats(skater_season_totalFaceoffLosses_per_60min, "Average # of FO Losses per 60 minutes")
    stats_table.add_row(table_season_totalFaceoffLosses_per_60min)
    # PIMs
    stats_table.add_divider()
    table_season_penaltyMinutes_total = format_table_stats(skater_season_penaltyMinutes, "Season PIMs")
    stats_table.add_row(table_season_penaltyMinutes_total)
    table_season_penaltyMinutes_per_game = format_table_stats(skater_season_penaltyMinutes_per_game, "Average # of PIMs per Game")
    stats_table.add_row(table_season_penaltyMinutes_per_game)
    table_season_penaltyMinutes_per_60min = format_table_stats(skater_season_penaltyMinutes_per_60min, "Average # of PIMs per 60 minutes")
    stats_table.add_row(table_season_penaltyMinutes_per_60min)

    print(stats_table)


def get_stats_by_season(player_id, path_to_team_images):

    path_to_images = path_to_team_images

    images = {
        "Anaheim Ducks": path_to_images+"anaheim_ducks.png",
        "Boston Bruins": path_to_images+"boston_bruins.png",
        "Buffalo Sabres": path_to_images+"buffalo_sabres.png",
        "Calgary Flames": path_to_images+"calgary_flames.png",
        "Carolina Hurricanes": path_to_images+"carolina_hurricanes.png",
        "Chicago Blackhawks": path_to_images+"chicago_blackhawks.png",
        "Colorado Avalanche": path_to_images+"colorado_avalanche.png",
        "Columbus Blue Jackets": path_to_images+"columbus_blue_jackets.png",
        "Dallas Stars": path_to_images+"dallas_stars.png",
        "Detroit Red Wings": path_to_images+"detroit_red_wings.png",
        "Edmonton Oilers": path_to_images+"edmonton_oilers.png",
        "Florida Panthers": path_to_images+"florida_panthers.png",
        "Los Angeles Kings": path_to_images+"los_angeles_kings.png",
        "Minnesota Wild": path_to_images+"minnesota_wild.png",
        "Montréal Canadiens": path_to_images+"montreal_canadiens.png",
        "Nashville Predators": path_to_images+"nashville_predators.png",
        "New Jersey Devils": path_to_images+"new_jersey_devils.png",
        "New York Islanders": path_to_images+"new_york_islanders.png",
        "New York Rangers": path_to_images+"new_york_rangers.png",
        "Ottawa Senators": path_to_images+"ottawa_senators.png",
        "Philadelphia Flyers": path_to_images+"philadelphia_flyers.png",
        "Pittsburgh Penguins": path_to_images+"pittsburgh_penguins.png",
        "San Jose Sharks": path_to_images+"san_jose_sharks.png",
        "Seattle Kraken": path_to_images+"seattle_kraken.png",
        "St. Louis Blues": path_to_images+"st_louis_blues.png",
        "Tampa Bay Lightning": path_to_images+"tampa_bay_lightning.png",
        "Toronto Maple Leafs": path_to_images+"toronto_maple_leafs.png",
        "Utah Mammoth": path_to_images+"utah_mammoth.png",
        "Vancouver Canucks": path_to_images+"vancouver_canucks.png",
        "Vegas Golden Knights": path_to_images+"vegas_golden_knights.png",
        "Washington Capitals": path_to_images+"washington_capitals.png",
        "Winnipeg Jets": path_to_images+"winnipeg_jets.png"
    }

    client = NHLClient(debug=False)

    # define player
    career_stats = client.stats.player_career_stats(player_id=player_id)  # "8478402" = Connor McDavid

    # set up dataframe
    df_nhl_rs_career_stats = pd.DataFrame(career_stats["seasonTotals"])
    df_nhl_rs_career_stats = df_nhl_rs_career_stats[df_nhl_rs_career_stats["leagueAbbrev"] == "NHL"]
    df_nhl_rs_career_stats = df_nhl_rs_career_stats[df_nhl_rs_career_stats["gameTypeId"] == 2]
    df_nhl_rs_career_stats = df_nhl_rs_career_stats.reset_index(drop=True)

    # calculate pp_asists and sh_assists and add them to the stats/game below
    df_nhl_rs_career_stats["powerPlayAssists"] = df_nhl_rs_career_stats["powerPlayPoints"] - df_nhl_rs_career_stats["powerPlayGoals"]
    df_nhl_rs_career_stats["shorthandedAssists"] = df_nhl_rs_career_stats["shorthandedPoints"] - df_nhl_rs_career_stats["shorthandedGoals"]

    # calculate even strength stats
    df_nhl_rs_career_stats["even_strength_goals"] = df_nhl_rs_career_stats["goals"] - (df_nhl_rs_career_stats["powerPlayGoals"] + df_nhl_rs_career_stats["shorthandedGoals"])
    df_nhl_rs_career_stats["even_strength_assists"] = df_nhl_rs_career_stats["assists"] - (df_nhl_rs_career_stats["powerPlayAssists"] + df_nhl_rs_career_stats["shorthandedAssists"])
    df_nhl_rs_career_stats["even_strength_points"] = df_nhl_rs_career_stats["points"] - (df_nhl_rs_career_stats["powerPlayPoints"] + df_nhl_rs_career_stats["shorthandedPoints"])

    ## get stats/game
    df_nhl_rs_career_stats["assists_per_game"] = df_nhl_rs_career_stats["assists"]/df_nhl_rs_career_stats["gamesPlayed"]
    df_nhl_rs_career_stats["goals_per_game"] = df_nhl_rs_career_stats["goals"]/df_nhl_rs_career_stats["gamesPlayed"]
    df_nhl_rs_career_stats["points_per_game"] = df_nhl_rs_career_stats["points"]/df_nhl_rs_career_stats["gamesPlayed"]
    df_nhl_rs_career_stats["powerPlayGoals_per_game"] = df_nhl_rs_career_stats["powerPlayGoals"]/df_nhl_rs_career_stats["gamesPlayed"]
    df_nhl_rs_career_stats["powerPlayAssists_per_game"] = df_nhl_rs_career_stats["powerPlayAssists"]/df_nhl_rs_career_stats["gamesPlayed"]
    df_nhl_rs_career_stats["powerPlayPoints_per_game"] = df_nhl_rs_career_stats["powerPlayPoints"]/df_nhl_rs_career_stats["gamesPlayed"]
    df_nhl_rs_career_stats["shorthandedGoals_per_game"] = df_nhl_rs_career_stats["shorthandedGoals"]/df_nhl_rs_career_stats["gamesPlayed"]
    df_nhl_rs_career_stats["shorthandedAssists_per_game"] = df_nhl_rs_career_stats["shorthandedAssists"]/df_nhl_rs_career_stats["gamesPlayed"]
    df_nhl_rs_career_stats["shorthandedPoints_per_game"] = df_nhl_rs_career_stats["shorthandedPoints"]/df_nhl_rs_career_stats["gamesPlayed"]
    df_nhl_rs_career_stats["even_strength_goals_per_game"] = df_nhl_rs_career_stats["even_strength_goals"]/df_nhl_rs_career_stats["gamesPlayed"]
    df_nhl_rs_career_stats["even_strength_assists_per_game"] = df_nhl_rs_career_stats["even_strength_assists"]/df_nhl_rs_career_stats["gamesPlayed"]
    df_nhl_rs_career_stats["even_strength_points_per_game"] = df_nhl_rs_career_stats["even_strength_points"]/df_nhl_rs_career_stats["gamesPlayed"]
    df_nhl_rs_career_stats["shots_per_game"] = df_nhl_rs_career_stats["shots"]/df_nhl_rs_career_stats["gamesPlayed"]

    # define season start
    df_nhl_rs_career_stats["season_label"] = df_nhl_rs_career_stats['season']
    df_nhl_rs_career_stats['season_label'] = df_nhl_rs_career_stats['season_label'].astype('string')
    df_nhl_rs_career_stats["season_label"] = df_nhl_rs_career_stats['season_label'].str[:4]

    # get team name
    teams = pd.DataFrame(df_nhl_rs_career_stats["teamName"]) # df_nhl_rs_career_stats['teamCommonName'] gives just the team name (e.g., sharks)
    # might have to do for loop...
    team_names = []
    for i in range(len(teams)):
        team_names.append(teams["teamName"][i]["default"])
    team_names = np.array(team_names)
    df_nhl_rs_career_stats["team_names"] = team_names

    df_nhl_rs_career_stats = df_nhl_rs_career_stats.drop(columns=['teamName', 'teamCommonName', 'teamPlaceNameWithPreposition'])

    # convert avgToi from a string to a float
    minutes = np.zeros(len(df_nhl_rs_career_stats))
    seconds = np.zeros(len(df_nhl_rs_career_stats))
    for i in range(len(df_nhl_rs_career_stats)):
        minutes[i], seconds[i] = map(int, df_nhl_rs_career_stats["avgToi"].values[i].split(":"))
    df_nhl_rs_career_stats["avgToi_float"] = minutes + (seconds / 60.)

    # set up data to plot images
    df_nhl_rs_career_stats["team_img"] = df_nhl_rs_career_stats["team_names"].map(images)
    df_nhl_rs_career_stats["season_plot"] = df_nhl_rs_career_stats["season"].astype(str).str[:4].astype(int)

    return df_nhl_rs_career_stats


def plot_stat_per_game(ax, ax_str, df, include_avg, stat, title, ylabel):

    for x, y, path in zip(df["season_plot"], df[stat], df["team_img"]):
        try:
            # Load image array
            img_array = plt.imread(path)

            # Wrap image in OffsetImage. Use 'zoom' to scale its visual size.
            img_box = OffsetImage(img_array, zoom=0.05)

            # Position the box at the specific (x, y) data point
            ab = AnnotationBbox(img_box, (x, y), frameon=False, zorder=100)

            # Add the custom marker to your plot
            ax.add_artist(ab)
        except FileNotFoundError:
            print(f"Warning: {path} not found. Skipping point ({x}, {y}).")

    if include_avg:
        ax.axhline(y=np.mean(df[stat]), color='tab:green', linewidth=8, zorder=10)
        #plt.axhline(y=np.mean(df["goals"][1:]), color='tab:green', linewidth=2) # this would exclude their rookie season from the average

        ax.axhline(y=np.mean(df[stat])+np.std(df[stat]), color='tab:green', linestyle='--', linewidth=4, zorder=10)
        ax.axhline(y=np.mean(df[stat])-np.std(df[stat]), color='tab:green', linestyle='--', linewidth=4, zorder=10)
        ax.fill_between(df["season_plot"], np.mean(df[stat])+np.std(df[stat]),
            np.mean(df[stat])-np.std(df[stat]), color="gray", alpha=0.3, zorder=1)

    # set xlim and ylim
    xmin, xmax = min(df["season_plot"]), max(df["season_plot"])
    ymin, ymax = min(df[stat]), max(df[stat])
    x_pad = (xmax - xmin) * 0.1
    y_pad = (ymax - ymin) * 0.1
    ax.set_xlim(xmin - x_pad, xmax + x_pad)
    ax.set_ylim(ymin - y_pad, ymax + y_pad)

    ax.set_title(title)
    ax.set_xlabel("Season")
    ax.set_ylabel(ylabel)
    #ax.set_xticks(df["season"], df["season_label"])
    ax.tick_params(axis='x', labelrotation=45)
    ax.grid(True, alpha=0.3)


"""
def plot_stat_per_game_no_team_pics(ax, ax_str, df, include_avg, stat, title, ylabel):

    if ax_str == "ax1":
        sns.scatterplot(data=df, x="season", y=stat, s=200, hue="team_names", ax=ax, zorder=100)
    else:
        sns.scatterplot(data=df, x="season", y=stat, s=200, hue="team_names", ax=ax, legend=False, zorder=100)
    #sns._legend.set_title("Team Names")

    if include_avg:
        ax.axhline(y=np.mean(df[stat]), color='tab:green', linewidth=8, zorder=10)
        #plt.axhline(y=np.mean(df["goals"][1:]), color='tab:green', linewidth=2) # this would exclude their rookie season from the average

        ax.axhline(y=np.mean(df[stat])+np.std(df[stat]), color='tab:green', linestyle='--', linewidth=4, zorder=10)
        ax.axhline(y=np.mean(df[stat])-np.std(df[stat]), color='tab:green', linestyle='--', linewidth=4, zorder=10)
        ax.fill_between(df["season"], np.mean(df[stat])+np.std(df[stat]),
            np.mean(df[stat])-np.std(df[stat]), color="gray", alpha=0.3, zorder=1)

    ax.set_title(title)
    ax.set_xlabel("Season")
    ax.set_ylabel(ylabel)
    ax.set_xticks(df["season"], df["season_label"])
    ax.tick_params(axis='x', labelrotation=45)
    if ax_str == "ax1":
        # simple legend
        #ax.legend(frameon=False)

        # fancier legend. need plt.subplots adjust for this one
        #ax.legend(loc='upper center', frameon=False, bbox_to_anchor(0.5, 1.02), ncols=4)
        ax.legend(bbox_to_anchor=(0., 1.02, 1., .102), loc='lower left', ncols=2, mode="expand", borderaxespad=1.)
    #plt.subplots_adjust(top=0.90)
    #plt.show()
"""


def home_away_split(player_id, season_id):

    client = NHLClient(debug=False)

    season = season_id

    player_id = str(player_id)
    player_game_stats = client.stats.player_game_log(player_id=str(player_id), season_id=season, game_type="2")

    df_player_game_stats = pd.DataFrame(data=player_game_stats)
    df_player_game_stats["powerPlayAssists"] = df_player_game_stats["powerPlayPoints"] - df_player_game_stats["powerPlayGoals"]
    df_player_game_stats["shorthandedAssists"] = df_player_game_stats["shorthandedPoints"] - df_player_game_stats["shorthandedGoals"]

    df_player_game_stats = toi_string_to_float(df_player_game_stats, "toi", "toi_float")

    df_player_game_stats_home = df_player_game_stats[df_player_game_stats["homeRoadFlag"] == "H"]
    df_player_game_stats_road = df_player_game_stats[df_player_game_stats["homeRoadFlag"] == "R"]

    df_player_game_stats_points_per_game = round(sum(df_player_game_stats["points"])/len(df_player_game_stats), 2)
    df_player_game_stats_points_per_60min = round((sum(df_player_game_stats["points"])/len(df_player_game_stats))/np.mean(df_player_game_stats["toi_float"]) * 60., 2)
    df_player_game_stats_goals_per_game = round(sum(df_player_game_stats["goals"])/len(df_player_game_stats), 2)
    df_player_game_stats_goals_per_60min = round((sum(df_player_game_stats["goals"])/len(df_player_game_stats))/np.mean(df_player_game_stats["toi_float"]) * 60., 2)
    df_player_game_stats_assists_per_game = round(sum(df_player_game_stats["assists"])/len(df_player_game_stats), 2)
    df_player_game_stats_assists_per_60min = round((sum(df_player_game_stats["assists"])/len(df_player_game_stats))/np.mean(df_player_game_stats["toi_float"]) * 60., 2)
    df_player_game_stats_shots_per_game = round(sum(df_player_game_stats["shots"])/len(df_player_game_stats), 2)
    df_player_game_stats_shots_per_60min = round((sum(df_player_game_stats["shots"])/len(df_player_game_stats))/np.mean(df_player_game_stats["toi_float"]) * 60., 2)
    df_player_game_stats_pm_per_game = round(sum(df_player_game_stats["plusMinus"])/len(df_player_game_stats), 2)
    df_player_game_stats_pm_per_60min = round((sum(df_player_game_stats["plusMinus"])/len(df_player_game_stats))/np.mean(df_player_game_stats["toi_float"]) * 60., 2)
    df_player_game_stats_pp_points_per_game = round(sum(df_player_game_stats["powerPlayPoints"])/len(df_player_game_stats), 2)
    df_player_game_stats_pp_points_per_60min = round((sum(df_player_game_stats["powerPlayPoints"])/len(df_player_game_stats))/np.mean(df_player_game_stats["toi_float"]) * 60., 2)
    df_player_game_stats_pp_goals_per_game = round(sum(df_player_game_stats["powerPlayGoals"])/len(df_player_game_stats), 2)
    df_player_game_stats_pp_goals_per_60min = round((sum(df_player_game_stats["powerPlayGoals"])/len(df_player_game_stats))/np.mean(df_player_game_stats["toi_float"]) * 60., 2)
    df_player_game_stats_pp_assists_per_game = round(sum(df_player_game_stats["powerPlayAssists"])/len(df_player_game_stats), 2)
    df_player_game_stats_pp_assists_per_60min = round((sum(df_player_game_stats["powerPlayAssists"])/len(df_player_game_stats))/np.mean(df_player_game_stats["toi_float"]) * 60., 2)
    df_player_game_stats_shooting_percentage = round(sum(df_player_game_stats["goals"])/sum(df_player_game_stats["shots"])*100., 2)

    # make home game stat per game and per 60
    df_player_game_stats_home_points_per_game = round(sum(df_player_game_stats_home["points"])/len(df_player_game_stats_home), 2)
    df_player_game_stats_home_points_per_60min = round((sum(df_player_game_stats_home["points"])/len(df_player_game_stats_home))/np.mean(df_player_game_stats_home["toi_float"]) * 60., 2)
    df_player_game_stats_home_goals_per_game = round(sum(df_player_game_stats_home["goals"])/len(df_player_game_stats_home), 2)
    df_player_game_stats_home_goals_per_60min = round((sum(df_player_game_stats_home["goals"])/len(df_player_game_stats_home))/np.mean(df_player_game_stats_home["toi_float"]) * 60., 2)
    df_player_game_stats_home_assists_per_game = round(sum(df_player_game_stats_home["assists"])/len(df_player_game_stats_home), 2)
    df_player_game_stats_home_assists_per_60min = round((sum(df_player_game_stats_home["assists"])/len(df_player_game_stats_home))/np.mean(df_player_game_stats_home["toi_float"]) * 60., 2)
    df_player_game_stats_home_shots_per_game = round(sum(df_player_game_stats_home["shots"])/len(df_player_game_stats_home), 2)
    df_player_game_stats_home_shots_per_60min = round((sum(df_player_game_stats_home["shots"])/len(df_player_game_stats_home))/np.mean(df_player_game_stats_home["toi_float"]) * 60., 2)
    df_player_game_stats_home_pm_per_game = round(sum(df_player_game_stats_home["plusMinus"])/len(df_player_game_stats_home), 2)
    df_player_game_stats_home_pm_per_60min = round((sum(df_player_game_stats_home["plusMinus"])/len(df_player_game_stats_home))/np.mean(df_player_game_stats_home["toi_float"]) * 60., 2)
    df_player_game_stats_home_pp_points_per_game = round(sum(df_player_game_stats_home["powerPlayPoints"])/len(df_player_game_stats_home), 2)
    df_player_game_stats_home_pp_points_per_60min = round((sum(df_player_game_stats_home["powerPlayPoints"])/len(df_player_game_stats_home))/np.mean(df_player_game_stats_home["toi_float"]) * 60., 2)
    df_player_game_stats_home_pp_goals_per_game = round(sum(df_player_game_stats_home["powerPlayGoals"])/len(df_player_game_stats_home), 2)
    df_player_game_stats_home_pp_goals_per_60min = round((sum(df_player_game_stats_home["powerPlayGoals"])/len(df_player_game_stats_home))/np.mean(df_player_game_stats_home["toi_float"]) * 60., 2)
    df_player_game_stats_home_pp_assists_per_game = round(sum(df_player_game_stats_home["powerPlayAssists"])/len(df_player_game_stats_home), 2)
    df_player_game_stats_home_pp_assists_per_60min = round((sum(df_player_game_stats_home["powerPlayAssists"])/len(df_player_game_stats_home))/np.mean(df_player_game_stats_home["toi_float"]) * 60., 2)
    df_player_game_stats_home_shooting_percentage = round(sum(df_player_game_stats_home["goals"])/sum(df_player_game_stats_home["shots"])*100., 2)

    # make road game stat per game and per 60
    df_player_game_stats_road_points_per_game = round(sum(df_player_game_stats_road["points"])/len(df_player_game_stats_road), 2)
    df_player_game_stats_road_points_per_60min = round((sum(df_player_game_stats_road["points"])/len(df_player_game_stats_road))/np.mean(df_player_game_stats_road["toi_float"]) * 60., 2)
    df_player_game_stats_road_goals_per_game = round(sum(df_player_game_stats_road["goals"])/len(df_player_game_stats_road), 2)
    df_player_game_stats_road_goals_per_60min = round((sum(df_player_game_stats_road["goals"])/len(df_player_game_stats_road))/np.mean(df_player_game_stats_road["toi_float"]) * 60., 2)
    df_player_game_stats_road_assists_per_game = round(sum(df_player_game_stats_road["assists"])/len(df_player_game_stats_road), 2)
    df_player_game_stats_road_assists_per_60min = round((sum(df_player_game_stats_road["assists"])/len(df_player_game_stats_road))/np.mean(df_player_game_stats_road["toi_float"]) * 60., 2)
    df_player_game_stats_road_shots_per_game = round(sum(df_player_game_stats_road["shots"])/len(df_player_game_stats_road), 2)
    df_player_game_stats_road_shots_per_60min = round((sum(df_player_game_stats_road["shots"])/len(df_player_game_stats_road))/np.mean(df_player_game_stats_road["toi_float"]) * 60., 2)
    df_player_game_stats_road_pm_per_game = round(sum(df_player_game_stats_road["plusMinus"])/len(df_player_game_stats_road), 2)
    df_player_game_stats_road_pm_per_60min = round((sum(df_player_game_stats_road["plusMinus"])/len(df_player_game_stats_road))/np.mean(df_player_game_stats_road["toi_float"]) * 60., 2)
    df_player_game_stats_road_pp_points_per_game = round(sum(df_player_game_stats_road["powerPlayPoints"])/len(df_player_game_stats_road), 2)
    df_player_game_stats_road_pp_points_per_60min = round((sum(df_player_game_stats_road["powerPlayPoints"])/len(df_player_game_stats_road))/np.mean(df_player_game_stats_road["toi_float"]) * 60., 2)
    df_player_game_stats_road_pp_goals_per_game = round(sum(df_player_game_stats_road["powerPlayGoals"])/len(df_player_game_stats_road), 2)
    df_player_game_stats_road_pp_goals_per_60min = round((sum(df_player_game_stats_road["powerPlayGoals"])/len(df_player_game_stats_road))/np.mean(df_player_game_stats_road["toi_float"]) * 60., 2)
    df_player_game_stats_road_pp_assists_per_game = round(sum(df_player_game_stats_road["powerPlayAssists"])/len(df_player_game_stats_road), 2)
    df_player_game_stats_road_pp_assists_per_60min = round((sum(df_player_game_stats_road["powerPlayAssists"])/len(df_player_game_stats_road))/np.mean(df_player_game_stats_road["toi_float"]) * 60., 2)
    df_player_game_stats_road_shooting_percentage = round(sum(df_player_game_stats_road["goals"])/sum(df_player_game_stats_road["shots"])*100., 2)


    table = PrettyTable(['Stat', 'All Games', "Home Games", "Away Games"])
    table.title = "Home vs. Road Stat Split"
    table.add_row(['# of games', len(df_player_game_stats), len(df_player_game_stats_home), len(df_player_game_stats_road)])
    table.add_row(['Average TOI [minutes]', round(np.mean(df_player_game_stats["toi_float"]), 2), round(np.mean(df_player_game_stats_home["toi_float"]), 2), round(np.mean(df_player_game_stats_road["toi_float"]), 2)])
    table.add_row(['Average # of Shifts', round(np.mean(df_player_game_stats["shifts"]), 2), round(np.mean(df_player_game_stats_home["shifts"]), 2), round(np.mean(df_player_game_stats_road["shifts"]), 2)])
    table.add_divider()
    table.add_row(['Total Points', sum(df_player_game_stats["points"]), sum(df_player_game_stats_home["points"]), sum(df_player_game_stats_road["points"])])
    table.add_row(['Total Points per Game', df_player_game_stats_points_per_game, df_player_game_stats_home_points_per_game, df_player_game_stats_road_points_per_game])
    table.add_row(['Total Points per 60 minutes', df_player_game_stats_points_per_60min, df_player_game_stats_home_points_per_60min, df_player_game_stats_road_points_per_60min])
    table.add_divider()
    table.add_row(['Total Goals', sum(df_player_game_stats["goals"]), sum(df_player_game_stats_home["goals"]), sum(df_player_game_stats_road["goals"])])
    table.add_row(['Total Goals per Game', df_player_game_stats_goals_per_game, df_player_game_stats_home_goals_per_game, df_player_game_stats_road_goals_per_game])
    table.add_row(['Total Goals per 60 minutes', df_player_game_stats_goals_per_60min, df_player_game_stats_home_goals_per_60min, df_player_game_stats_road_goals_per_60min])
    table.add_divider()
    table.add_row(['Total Assists', sum(df_player_game_stats["assists"]), sum(df_player_game_stats_home["assists"]), sum(df_player_game_stats_road["assists"])])
    table.add_row(['Total Assists per Game', df_player_game_stats_assists_per_game, df_player_game_stats_home_assists_per_game, df_player_game_stats_road_assists_per_game])
    table.add_row(['Total Assists per 60 minutes', df_player_game_stats_assists_per_60min, df_player_game_stats_home_assists_per_60min, df_player_game_stats_road_assists_per_60min])
    table.add_divider()
    table.add_row(['Total PP Points', sum(df_player_game_stats["powerPlayPoints"]), sum(df_player_game_stats_home["powerPlayPoints"]), sum(df_player_game_stats_road["powerPlayPoints"])])
    table.add_row(['Total PP Points per Game', df_player_game_stats_pp_points_per_game, df_player_game_stats_home_pp_points_per_game, df_player_game_stats_road_pp_points_per_game])
    table.add_row(['Total PP Points per 60 minutes', df_player_game_stats_pp_points_per_60min, df_player_game_stats_home_pp_points_per_60min, df_player_game_stats_road_pp_points_per_60min])
    table.add_divider()
    table.add_row(['Total PP Goals', sum(df_player_game_stats["powerPlayGoals"]), sum(df_player_game_stats_home["powerPlayGoals"]), sum(df_player_game_stats_road["powerPlayGoals"])])
    table.add_row(['Total PP Goals per Game', df_player_game_stats_pp_goals_per_game, df_player_game_stats_home_pp_goals_per_game, df_player_game_stats_road_pp_goals_per_game])
    table.add_row(['Total PP Goals per 60 minutes', df_player_game_stats_pp_goals_per_60min, df_player_game_stats_home_pp_goals_per_60min, df_player_game_stats_road_pp_goals_per_60min])
    table.add_divider()
    table.add_row(['Total PP Assists', sum(df_player_game_stats["powerPlayAssists"]), sum(df_player_game_stats_home["powerPlayAssists"]), sum(df_player_game_stats_road["powerPlayAssists"])])
    table.add_row(['Total PP Assists per Game', df_player_game_stats_pp_assists_per_game, df_player_game_stats_home_pp_assists_per_game, df_player_game_stats_road_pp_assists_per_game])
    table.add_row(['Total PP Assists per 60 minutes', df_player_game_stats_pp_assists_per_60min, df_player_game_stats_home_pp_assists_per_60min, df_player_game_stats_road_pp_assists_per_60min])
    table.add_divider()
    table.add_row(['Total Shots', sum(df_player_game_stats["shots"]), sum(df_player_game_stats_home["shots"]), sum(df_player_game_stats_road["shots"])])
    table.add_row(['Total Shots per Game', df_player_game_stats_shots_per_game, df_player_game_stats_home_shots_per_game, df_player_game_stats_road_shots_per_game])
    table.add_row(['Total Shots per 60 minutes', df_player_game_stats_shots_per_60min, df_player_game_stats_home_shots_per_60min, df_player_game_stats_road_shots_per_60min])
    table.add_row(['Total Shooting %', df_player_game_stats_shooting_percentage, df_player_game_stats_home_shooting_percentage, df_player_game_stats_road_shooting_percentage])
    #table.set_style(DOUBLE_BORDER)
    print(table)



def game_schedule(start_date, end_date):

    client = NHLClient()

    dates, weekdays = get_dates_and_weekdays(start_date, end_date)

    #print("Dates:", dates)
    #print("Days of Week:", weekdays)

    df_schedule = pd.DataFrame({
        "date": dates,
        "day_of_week": weekdays,
    })
    df_schedule = df_schedule.set_index('date')


    # get the number of games each day
    num_games = np.zeros(len(df_schedule))
    game_ids = []
    all_home_teams = []
    all_away_teams = []
    for i in range(len(df_schedule)):

        # define game info to get
        ids = []
        home_teams = []
        away_teams = []

        # Get games for a specific date
        games = client.schedule.daily_schedule(date=df_schedule.index[i])
        df_games = pd.DataFrame(games['games'])

        # check if df_games is empty
        if df_games.empty:
            print("No Games on %s" % (df_schedule.index[i]))
        else:
            # makes sure games are regular season games
            df_games = df_games[df_games["gameType"] == 2]
            num_games[i] = len(df_games)

            # grab the game ids, home team, and away team
            for j in range(len(df_games)):
                ids.append(df_games["id"].values[j])
                home_teams.append(df_games["homeTeam"].values[j]["abbrev"])
                away_teams.append(df_games["awayTeam"].values[j]["abbrev"])

        game_ids.append(ids)
        all_home_teams.append(home_teams)
        all_away_teams.append(away_teams)


    # add columns that I want to track
    df_schedule["num_games"] = num_games
    df_schedule["num_games"] = df_schedule["num_games"].astype(int)

    df_schedule["game_ids"] = game_ids
    df_schedule["home_teams"] = all_home_teams
    df_schedule["away_teams"] = all_away_teams


    df_schedule = df_schedule[df_schedule["num_games"] != 0]

    ### identify the "busy days"
    df_schedule["num_games_tracker"] = ""
    for i in range(len(df_schedule)):
        if df_schedule["num_games"].values[i] == 0:
            df_schedule["num_games_tracker"].values[i] = "No Games"
        elif df_schedule["num_games"].values[i] <= 6:
            df_schedule["num_games_tracker"].values[i] = "Light Day"
        elif 6 < df_schedule["num_games"].values[i] <= 9:
            df_schedule["num_games_tracker"].values[i] = "Medium Day"
            #print("%s is a moderately busy fantasy day: %s games" % (df_schedule.index[i], df_schedule["num_games"].values[i]))
            ## make above text yellow!
        elif df_schedule["num_games"].values[i] > 9:
            df_schedule["num_games_tracker"].values[i] = "Busy Day"
            #print("%s is a very busy fantasy day: %s games" % (df_schedule.index[i], df_schedule["num_games"].values[i]))
            ## make above text red!

    ## eventually automate this and query the current team list
    full_team_abbr_list = [
        "ANA",
        "BOS",
        "BUF",
        "CAR",
        "CBJ",
        "CGY",
        "CHI",
        "COL",
        "DAL",
        "DET",
        "EDM",
        "FLA",
        "LAK",
        "MIN",
        "MTL",
        "NJD",
        "NSH",
        "NYI",
        "NYR",
        "OTT",
        "PHI",
        "PIT",
        "SEA",
        "SJS",
        "STL",
        "TBL",
        "TOR",
        "UTA",
        "VGK",
        "WSH",
        "VAN",
        "WPG",
    ]


    team_name_dict = {
        "ANA": "Anaheim Ducks",
        "BOS": "Boston Bruins",
        "BUF": "Buffalo Sabres",
        "CAR": "Carolina Hurricanes",
        "CBJ": "Columbus Blue Jackets",
        "CGY": "Calgary Flames",
        "CHI": "Chicago Blackhawks",
        "COL": "Colorado Avalanche",
        "DAL": "Dallas Stars",
        "DET": "Detroit Red Wings",
        "EDM": "Edmonton Oilers",
        "FLA": "Florida Panthers",
        "LAK": "Los Angeles Kings",
        "MIN": "Minnesota Wild",
        "MTL": "Montréal Canadiens",
        "NJD": "New Jersey Devils",
        "NSH": "Nashville Predators",
        "NYI": "New York Islanders",
        "NYR": "New York Rangers",
        "OTT": "Ottawa Senators",
        "PHI": "Philadelphia Flyers",
        "PIT": "Pittsburgh Penguins",
        "SEA": "Seattle Kraken",
        "SJS": "San Jose Sharks",
        "STL": "St. Louis Blues",
        "TBL": "Tampa Bay Lightning",
        "TOR": "Toronto Maple Leafs",
        "UTA": "Utah Mammoth",
        "VGK": "Vegas Golden Knights",
        "WSH": "Washington Capitals",
        "VAN": "Vancouver Canucks",
        "WPG": "Winnipeg Jets",
    }


    cols_for_table = ["Game Category", "Total # of Games", "# of Light Days", "# of Medium Days", "# of Heavy Days"]

    schedule_headers = [
    f"\033[1m{cols_for_table[i]}\033[0m" for i in range(len(cols_for_table))
    ]
    schedule_table = PrettyTable(schedule_headers)
    schedule_table.title = "\033[1mGame Breakdown in Date Window %s - %s\033[0m" % (start_date, end_date)

    # loop through all of the teams
    for i in range(len(full_team_abbr_list)):

        team_full_schedule = client.schedule.team_season_schedule(team_abbr=full_team_abbr_list[i], season="20262027")
        df_team_full_schedule = pd.DataFrame(team_full_schedule["games"])
        df_team_full_schedule = df_team_full_schedule.set_index('gameDate')

        df_team_schedule_in_range = pd.merge(df_schedule, df_team_full_schedule, left_index=True, right_index=True, how='inner')

        # count the total number of games, and how many of them are busy days
        total_games = len(df_team_schedule_in_range)
        light_days_counter = 0
        medium_days_counter = 0
        busy_days_counter = 0
        for j in range(len(df_team_schedule_in_range)):
            if df_team_schedule_in_range["num_games_tracker"].values[j] == "Light Day":
                light_days_counter+=1
            elif df_team_schedule_in_range["num_games_tracker"].values[j] == "Medium Day":
                medium_days_counter+=1
            elif df_team_schedule_in_range["num_games_tracker"].values[j] == "Busy Day":
                busy_days_counter+=1

        team_games = np.array([total_games, light_days_counter, medium_days_counter, busy_days_counter])

        team_row = format_schedule_stats(team_games, team_name_dict[full_team_abbr_list[i]])
        schedule_table.add_row(team_row)
        schedule_table.add_divider()

    print(schedule_table)











## end
