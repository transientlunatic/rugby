Data Visualisation
==================

The ``rugby`` package contains a number of functions designed to make visualising data from its database easier.


Time matrix plots
-----------------

Time-matrix plots can be produced for any tournament, showing the time each player in a team's squad has spent on the pitch across all their games in that season.

.. autofunction:: rugby.plotting.player_time_matrix_plot

.. plot::

   import rugby
   from rugby.tournament import Tournament
   import rugby.plotting
   import pandas as pd

   import matplotlib
   import matplotlib.pyplot as plt
   plt.style.use(rugby.plotting.style)

   tournament = Tournament.from_json(f"{rugby.__path__[0]}/json_data/super-rugby-aotearoa-2020.json")
   
   team = "Highlanders"
   f, ax = plt.subplots(1,1, sharey=True, figsize=(1.5,6), dpi=300)
   rugby.plotting.player_time_matrix_plot(tournament, team, ax, labelfont={"fontsize":5})
   f.text(0.08, 0.99, "Minutes played", fontdict={"fontsize":5}, ha="left")
   f.tight_layout()
