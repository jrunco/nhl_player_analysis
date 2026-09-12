
import numpy as np
import pandas as pd
from pathlib import Path
import sys

import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import seaborn as sns

from tabulate import tabulate
from prettytable import PrettyTable, TableStyle

from datetime import date, datetime, timedelta

from nhlpy.nhl_client import NHLClient

from utils.function_library import get_dates_and_weekdays
from utils.function_library import format_schedule_stats

client = NHLClient()





start_date = "2026-09-25"
end_date = "2027-04-15"

def game_schedule(start_date, end_date):

    dates, weekdays = get_dates_and_weekdays(start_date, end_date)

    print("Dates:", dates)
    print("Days of Week:", weekdays)

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

        #print(df_schedule.index[i])
        # Get games for a specific date
        games = client.schedule.daily_schedule(date=df_schedule.index[i])
        df_games = pd.DataFrame(games['games'])
        #print(df_games)

        # check if df_games is empty
        if df_games.empty:
            print("no games on %s" % (df_schedule.index[i]))
        else:
            # makes sure games are regular season games
            #print(len(df_games))
            df_games = df_games[df_games["gameType"] == 2]
            #print(len(df_games))
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
    #print(df_schedule)

    ### identify the "busy days"
    df_schedule["num_games_tracker"] = ""
    for i in range(len(df_schedule)):
        if df_schedule["num_games"].values[i] == 0:
            df_schedule["num_games_tracker"].values[i] = "No Games"
        elif df_schedule["num_games"].values[i] <= 6:
            df_schedule["num_games_tracker"].values[i] = "Light Day"
        elif 6 < df_schedule["num_games"].values[i] <= 9:
            df_schedule["num_games_tracker"].values[i] = "Medium Day"
            print("%s is a moderately busy fantasy day: %s games" % (df_schedule.index[i], df_schedule["num_games"].values[i]))
            ## make above text yellow!
        elif df_schedule["num_games"].values[i] > 9:
            df_schedule["num_games_tracker"].values[i] = "Busy Day"
            print("%s is a very busy fantasy day: %s games" % (df_schedule.index[i], df_schedule["num_games"].values[i]))
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
        #print(team_full_schedule.keys())
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
        #print("# of Total Games = %s" % (total_games))
        #print("# of Games on Light Days = %s" % (light_days_counter))
        #print("# of Games on Semi-busy Days = %s" % (medium_days_counter))
        #print("# of Games on Busy Days = %s" % (busy_days_counter))

        team_games = np.array([total_games, light_days_counter, medium_days_counter, busy_days_counter])

        team_row = format_schedule_stats(team_games, team_name_dict[full_team_abbr_list[i]])
        #team_row = format_schedule_stats(team_games, full_team_abbr_list[i])
        schedule_table.add_row(team_row)
        schedule_table.add_divider()

    print(schedule_table)


print("pre function test")

game_schedule("2026-09-01", "2027-04-30")

print("post function test")




































################################################ below is the example
# --- Example Usage ---
start = "2026-09-25"
end = "2027-04-15"

dates, weekdays = get_dates_and_weekdays(start, end)

print("Dates:", dates)
print("Days of Week:", weekdays)

df_schedule = pd.DataFrame({
    "date": dates,
    "day_of_week": weekdays,
})
df_schedule = df_schedule.set_index('date')

# add columns that I want to track
#df_schedule["num_games"] = 0
#df_schedule["game_ids"] = None


"""
ideas:
1) use client.schedule.daily_schedule() to get number of games in each date specified in function get_dates_and_weekdays()
    - add to df_schedule
2) loop through teams, see how many times they play in window, showing the days they play
"""


num_games = np.zeros(len(df_schedule))
game_ids = []
all_home_teams = []
all_away_teams = []
for i in range(len(df_schedule)):

    # define game info to get
    ids = []
    home_teams = []
    away_teams = []

    #print(df_schedule.index[i])
    # Get games for a specific date
    games = client.schedule.daily_schedule(date=df_schedule.index[i])
    df_games = pd.DataFrame(games['games'])
    #print(df_games)

    # check if df_games is empty
    if df_games.empty:
        print("no games on %s" % (df_schedule.index[i]))
    else:
        # makes sure games are regular season games
        #print(len(df_games))
        df_games = df_games[df_games["gameType"] == 2]
        #print(len(df_games))
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
#print(df_schedule)

### identify the "busy days"
df_schedule["num_games_tracker"] = ""
for i in range(len(df_schedule)):
    if df_schedule["num_games"].values[i] == 0:
        df_schedule["num_games_tracker"].values[i] = "No Games"
    elif df_schedule["num_games"].values[i] <= 6:
        df_schedule["num_games_tracker"].values[i] = "Light Day"
    elif 6 < df_schedule["num_games"].values[i] <= 9:
        df_schedule["num_games_tracker"].values[i] = "Medium Day"
        print("%s is a moderately busy fantasy day: %s games" % (df_schedule.index[i], df_schedule["num_games"].values[i]))
        ## make above text yellow!
    elif df_schedule["num_games"].values[i] > 9:
        df_schedule["num_games_tracker"].values[i] = "Busy Day"
        print("%s is a very busy fantasy day: %s games" % (df_schedule.index[i], df_schedule["num_games"].values[i]))
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
schedule_table.title = "\033[1mGame Breakdown in Date Window %s - %s\033[0m" % (start, end)

# loop through all of the teams
for i in range(len(full_team_abbr_list)):

    team_full_schedule = client.schedule.team_season_schedule(team_abbr=full_team_abbr_list[i], season="20262027")
    #print(team_full_schedule.keys())
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
    #print("# of Total Games = %s" % (total_games))
    #print("# of Games on Light Days = %s" % (light_days_counter))
    #print("# of Games on Semi-busy Days = %s" % (medium_days_counter))
    #print("# of Games on Busy Days = %s" % (busy_days_counter))

    team_games = np.array([total_games, light_days_counter, medium_days_counter, busy_days_counter])

    team_row = format_schedule_stats(team_games, team_name_dict[full_team_abbr_list[i]])
    #team_row = format_schedule_stats(team_games, full_team_abbr_list[i])
    schedule_table.add_row(team_row)
    schedule_table.add_divider()

print(schedule_table)














######## make a table for one team

# count the number of times a team plays in that window
# Get team's games for a specific season
team_full_schedule = client.schedule.team_season_schedule(team_abbr="SJS", season="20262027")
print(team_full_schedule.keys())
df_team_full_schedule = pd.DataFrame(team_full_schedule["games"])
df_team_full_schedule = df_team_full_schedule.set_index('gameDate')


df_team_schedule_in_range = pd.merge(df_schedule, df_team_full_schedule, left_index=True, right_index=True, how='inner')

# count the total number of games, and how many of them are busy days
total_games = len(df_team_schedule_in_range)
light_days_counter = 0
medium_days_counter = 0
busy_days_counter = 0
for i in range(len(df_team_schedule_in_range)):
    if df_team_schedule_in_range["num_games_tracker"].values[i] == "Light Day":
        light_days_counter+=1
    elif df_team_schedule_in_range["num_games_tracker"].values[i] == "Medium Day":
        medium_days_counter+=1
    elif df_team_schedule_in_range["num_games_tracker"].values[i] == "Busy Day":
        busy_days_counter+=1
print("# of Total Games = %s" % (total_games))
print("# of Games on Light Days = %s" % (light_days_counter))
print("# of Games on Semi-busy Days = %s" % (medium_days_counter))
print("# of Games on Busy Days = %s" % (busy_days_counter))

team_games = np.array([total_games, light_days_counter, medium_days_counter, busy_days_counter])

### make a prettyTable where each team is a column and each of the 4 game counts is a row


## 1. make the teams the rows
cols_for_table = ["Game Category", "Total # of Games", "# of Light Days", "# of Medium Days", "# of Heavy Days"]

schedule_headers = [
f"\033[1m{cols_for_table[i]}\033[0m" for i in range(len(cols_for_table))
]
schedule_table = PrettyTable(schedule_headers)
schedule_table.title = "\033[1mGame Breakdown in Date Window %s - %s\033[0m" % (start, end)

team_row = format_schedule_stats(team_games, "SJS")
schedule_table.add_row(team_row)

print(schedule_table)




## 2. make the teams the columns
teams_for_table2 = ["Game Category", "SJS"]

schedule_headers2 = [
f"\033[1m{teams_for_table2[i]}\033[0m" for i in range(len(teams_for_table2))
]


schedule_table2 = PrettyTable(schedule_headers2)
schedule_table2.title = "\033[1mGame Breakdown in Date Window %s - %s\033[0m" % (start, end)

print(schedule_table2)







# Get games for a specific date
games = client.schedule.daily_schedule(date="2026-08-01")
print(games.keys())
# dict_keys(['nextStartDate', 'previousStartDate', 'date', 'oddsPartners', 'games', 'numberOfGames'])
# games["numberOfGames"] = 5
# games["date"] = '2026-11-01'
df_games = pd.DataFrame(games['games'])


# Get games for a specific week
week_games = client.schedule.weekly_schedule(date="2026-11-01")
print(week_games.keys())

# Get team's games for a specific week
weekly_schedule = client.schedule.team_weekly_schedule(team_abbr="SJS", date="2026-11-01")
#print(weekly_schedule.keys()) # no keys

# Get team's games for a specific month
team_schedule = client.schedule.team_monthly_schedule(team_abbr="SJS", month="2026-11")
#print(team_schedule.keys()) # no keys

# Get team's games for a specific season
full_schedule = client.schedule.team_season_schedule(team_abbr="SJS", season="20262027")
print(full_schedule.keys())
# dict_keys(['previousSeason', 'currentSeason', 'clubTimezone', 'clubUTCOffset', 'games'])


# get a calendar schedule?
cal = client.schedule.calendar_schedule(date="2026-11-01")
print(cal.keys())










"""
# 1. Define start and end date strings
start_str = "2026-09-01"
end_str = "2026-10-05"

# 2. Convert strings to datetime objects
start_date = datetime.strptime(start_str, "%Y-%m-%d")
end_date = datetime.strptime(end_str, "%Y-%m-%d")

# 3. Generate all dates in between and format them back to strings
# Note: Use `(end_date - start_date).days + 1` to include the end date (inclusive)
date_strings = [
    (start_date + timedelta(days=x)).strftime("%Y-%m-%d")
    for x in range((end_date - start_date).days + 1)
]

print(date_strings)
# Output: ['2026-09-01', '2026-09-02', '2026-09-03', '2026-09-04', '2026-09-05']

"""

###
