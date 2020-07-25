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

    info = dict(title = "Rugby Data API",
                description = "A simple machine-readable interface for rugby match and player information.",
                version = "0.0.1")
    
    resources = {
        url_for("tournaments"): {"get": {"description": "Returns a list of all seasons for a tournament."}},
        url_for("seasons"): {"get": {"description": "Returns a list of all seasons in the database."}},
        url_for("all_matches"): {"get": {"description": "Returns a list of all matches in the database."}},
        url_for("teams"): {"get": {"description": "Returns a list of all teams in the database."}}
                 }
    return dict(info=info, paths=resources, externalDocs="https://code.daniel-williams.co.uk/rugby")

@app.route("/tournaments/")
def tournaments():
    out = []
    tournaments = rugby.models.Tournament.all()
    for tournament in tournaments:
        out.append({"name": tournament.name,
                    "url": url_for("tournament_season_list", tournament=tournament.name.replace(" ", "_"),  _external=False),})
    return out

@app.route("/tournament/<tournament>")
def tournament_season_list(tournament):
    tournament = " ".join(tournament.split("_"))
    tournament_s = rugby.models.Season.from_query(tournament=tournament);
    out = []
    for season in tournament_s:
        out.append({"name": season.season, "url": url_for("season", tournament=tournament.replace(" ", "_"), season=season.season)})
    return out

@app.route("/seasons/")
def seasons():
    seasons = rugby.models.Season.all()
    out = []

    for season in seasons:
        tournament = rugby.models.Tournament.get(season.tournament)
        out.append({"name": season.name,
                    "url": url_for("season", tournament=tournament.name.replace(" ", "_"), season=season.name,  _external=False),
                    "tournament": tournament.name})
    return out


    
@app.route("/seasons/<tournament>/<season>")
def season(tournament, season):
    tournament = " ".join(tournament.split("_"))
    tournament = rugby.models.Season.from_query(tournament=tournament, season=season)
    matches = []
    for match in tournament.matches:
        matches.append({"home": match.teams['home'].short_name,
                        "away": match.teams['away'].short_name,
                        "date": match.date.isoformat(),
                        "score": match.score,
                        "url": url_for("match", home=match.teams['home'].short_name, away=match.teams['away'].short_name, date=f"{match.date:%Y-%m-%d}",  _external=False)})
    for match in tournament.future:
        matches.append({"home": match.teams['home'].short_name,
                        "away": match.teams['away'].short_name,
                        "date": match.date.isoformat(),
                        "url": url_for("match", home=match.teams['home'].short_name, away=match.teams['away'].short_name, date=f"{match.date:%Y-%m-%d}",  _external=False)})
    return {"matches": matches,
            "tournament": tournament.name,
            "season": tournament.season,
            "table": url_for("league_table", tournament=tournament.name.replace(" ", "_"), season=tournament.season),
            "teams": [{"name": team.short_name,
                        "url": url_for("team", shortname=team.short_name.replace(" ", "_"), _external=False)} for team in tournament.teams()]}
    #return tournament.to_json()

@app.route("/seasons/<tournament>/<season>/table")
def league_table(tournament, season):
    """The league table for a given tournament."""
    tournament = " ".join(tournament.split("_"))
    tournament = rugby.models.Season.from_query(tournament=tournament, season=season)

    table = tournament.league_table()

    out = []
    for i, row in table.iterrows():
        
        out.append({
            "position": i+1,
            "played": row.played,
            "points": row.points,
            "won": row.won,
            "lost": row.lost,
            "drawn": row.drawn,
            "for": row['for'],
            "bonus": row.bonus,
            "against": row['against'],
            "team": {"name": row.team.short_name,
                             "url": url_for("team", shortname=row.team.short_name.replace(" ", "_"), _external=False)}
        })
    return out
        
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
            "country": team.country,
            "colors": {"primary": f"#{team.color_primary}"},
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
