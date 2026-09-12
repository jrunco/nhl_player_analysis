
This NHL analytics and fantasy hockey tool. Use it to:
- calculate player fantasy stats in a single season
- deep dive into single season performance
- visualize player stats across their career to identify trends

To use this tool do the following:
1. clone this repo
2. in a terminal window use the environment.yml file to set up the conda environment

  `conda env create -f environment.yml`

3. Open a jupyter notebook to run any of the available tools. Type `jupyter notebook` in a terminal window (same directory where the .ipynb files are). This will open a jupyter notebook session in a web browser. There are three available tools at this time.

    a) analyze_single_skater.ipynb -- This tool provides an in-depth analysis on a single skater (no goalies). Specifically, it provides a breakdown on their stats over the course of a single season. Stats on a per game and per 60 minutes are calculated. Home vs. away splits are also calculated. It also plots the player's statistical totals each year over the course of their career and calculates their career averages per season. To run change the default fantasy scoring system to your league system in cell 3, and in cell 4) define the skater name and regular season to what you want to analyze.

    b) compare_multiple_skaters.ipynb -- This tool provides a stats comparison for 2 or more skaters.

    c) create_schedule_calendar.py -- This tool shows the number of busy and light number of games for all 32 teams over a user specified time range

To run any of these scripts, click "kernel" then "restart and run all" to run the kernel.


Note: do not change the folder structure and what files are stored where. This is needed to accurately grab pngs of NHL logos to plot.

Note: this tool is not complete. The following work in is progress:
  1. I'm adding new capabilities for more in-depth player analysis.
  2. Moving this tool to a GUI window environment in progress. gui_driver.py does not have all of the functionality of the jupyter notebook (yet).

Also, ignore the sandbox. It is where I test new ideas for the project. Or don't ignore it and look at messy code.
