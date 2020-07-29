=============
The Rugby API
=============

The rugby API exposes data for all of the matches, players, and match events in the rugby database. The API is RESTful, and uses HTTP requests and returns JSON data in responses.


Tournaments and Seasons
-----------------------

.. qrefflask:: rugby.scripts.api:app
  :undoc-static:
  :endpoints: tournaments, tournament_season_list

Endpoints
+++++++++

.. autoflask:: rugby.scripts.api:app
   :undoc-static:
   :include-empty-docstring:
   :endpoints: tournaments, tournament_season_list


Teams
-----

.. autoflask:: rugby.scripts.api:app
   :undoc-static:
   :include-empty-docstring:
   :endpoints: teams


Matches
-------

.. qrefflask:: rugby.scripts.api:app
  :undoc-static:
  :endpoints: match, lineup

.. autoflask:: rugby.scripts.api:app
   :undoc-static:
   :include-empty-docstring:
   :endpoints: match, lineup
