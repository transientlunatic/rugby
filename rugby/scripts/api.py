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

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

engine = create_engine(f'sqlite:///{rugby.__path__[0]}/rugby.db')
session_factory = sessionmaker(bind=engine)

from flask_sqlalchemy_session import flask_scoped_session
session = flask_scoped_session(session_factory, app)

@app.route("/")
def resources():
    resources = dict(seasons={"name": "seasons", "url": url_for("seasons", _external=True)},
                     matches={"name": "matches",
                              "url": url_for("all_matches", _external=True)},
                     teams={"name": "teams", "url": url_for("teams", _external=True)}
    )
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
    matches = []
    for match in tournament.matches:
        matches.append({"home": match.teams['home'].short_name,
                        "away": match.teams['away'].short_name,
                        "date": match.date,
                        "score": match.score,
                        "url": url_for("match", home=match.teams['home'].short_name, away=match.teams['away'].short_name, date=f"{match.date:%Y-%m-%d}",  _external=True)})
    return {"matches": matches, "tournament": tournament.name, "season": tournament.season}
    #return tournament.to_json()

@app.route("/teams/")
def teams():
    teams = rugby.models.Team.all()
    teams_r = []
    for team in teams:
        teams_r.append({"name": team.name,
                        "url": url_for("team", shortname=team.shortname, _external=True)})
    return teams_r
    
@app.route("/teams/<shortname>")
def team(shortname):
    team = rugby.models.Team.from_query(shortname)
    return {"name": team.name,
            "short name": team.shortname}

@app.route("/matches/")
def all_matches():
    return rugby.models.Match.all()

@app.route("/matches/<home>/<away>/")
def derbies(home, away):
    return rugby.models.Match.from_query(home=home, away=away)
    
@app.route("/matches/<home>/<away>/<date>")
def match(home, away, date):
    match = rugby.models.Match.from_query(home=home, away=away, date=date)
    return match.to_rest()

if __name__ == '__main__':
    
    app.run()
