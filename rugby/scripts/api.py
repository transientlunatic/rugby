import json
import glob
import re

import rugby.models

from flask import url_for
from flask_api import FlaskAPI
from flask_compress import Compress
from flask_cors import CORS

app = FlaskAPI(__name__)
Compress(app)
CORS(app)

@app.route("/")
def resources():
    resources = dict(seasons={"name": "seasons", "url": url_for("seasons", _external=True)})
    return resources

@app.route("/seasons/")
def seasons():
    seasons = rugby.models.Season.all()
    out = []

    for season in seasons:
        tournament = rugby.models.Tournament.get(season.tournament)
        out.append({"name": season.name,
                    "url": url_for("season", tournament=tournament.name, season=season.name,  _external=True),
                    "tournament": tournament.name})
    return out

@app.route("/seasons/<tournament>/<season>")
def season(tournament, season):
    tournament = rugby.models.Season.from_query(tournament=tournament, season=season)
    return tournament.to_json()

if __name__ == '__main__':
    
    app.run()
