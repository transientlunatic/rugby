import os
import json
import glob
import re

import rugby.models

from rugby import utils

from flask import url_for, request
from flask_api import FlaskAPI, status
from flask_compress import Compress
from flask_cors import CORS

from flask_jwt_extended import (
    JWTManager, jwt_required,
    jwt_refresh_token_required,
    get_jwt_identity,
    create_access_token,
    create_refresh_token
)

from sqlalchemy.orm.exc import NoResultFound

app = FlaskAPI(__name__)
Compress(app)
CORS(app)
if 'RUGBYDB' in os.environ:
    db = os.environ['RUGBYDB']
    app.config['JWT_SECRET_KEY'] = os.environ['RUGBY_SECRET']
else:
    db = f"{rugby.__path__[0]}/rugby.db"
    app.config['JWT_SECRET_KEY'] = 'test'
jwt = JWTManager(app)

print(db);

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


engine = create_engine(f'sqlite:///{db}')
session_factory = sessionmaker(bind=engine)

from flask_sqlalchemy_session import flask_scoped_session
session = flask_scoped_session(session_factory, app)

try:
    rugby.models.User.__table__.drop(engine)
except:
    pass

rugby.models.User.__table__.create(engine)
rugby.models.User.create_user("Daniel Williams", "daniel", "daniel", session=session)


@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate, public, max-age=0"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


@app.route("/")
def resources():

    info = dict(title = "Rugby Data API",
                description = "A simple machine-readable interface for rugby match and player information.",
                version = "0.0.1")
    
    resources = {
        url_for("authenticate"): {"post": {"description": "Authenticates user, returns JWT."}},
        "tournaments": {"get": {"description": "Returns a list of all seasons for a tournament.",},
                        "url": url_for("tournaments")
        },
        "seasons": {"get": {"description": "Returns a list of all seasons in the database."},
                    "url": url_for("seasons")
        },
        url_for("all_players"): {"get": {"description": "Returns a list of all players."}},
        url_for("all_matches"): {"get": {"description": "Returns a list of all matches in the database."}},
        url_for("teams"): {"get": {"description": "Returns a list of all teams in the database."}}
                 }
    return dict(info=info, paths=resources, externalDocs="https://code.daniel-williams.co.uk/rugby")

    
@app.route("/authenticate", methods=['POST'])
def authenticate():
    """
    Authenticate the user and issue a JWT.
    """
    data = request.data
    if set(data.keys()) < {"username", "password"}:
        return {}, status.HTTP_400_BAD_REQUEST

    username = data.get("username")
    password = data.get("password")
    user = rugby.models.User.login(username, password)
    if user:
        access_token = create_access_token(identity=user['id'], fresh=True)
        refresh_token = create_refresh_token(user['id'])
        return {
            'access_token': access_token,
            'refresh_token': refresh_token
        }
    else:
        return {}, status.HTTP_401_UNAUTHORIZED

@app.route("/authenticate/refresh", methods=['POST'])
@jwt_refresh_token_required
def refresh():
    # retrive the user's identity from the refresh token using a Flask-JWT-Extended built-in method
    current_user = get_jwt_identity()
    # return a non-fresh token for the user
    new_token = create_access_token(identity=current_user, fresh=False)
    return {'access_token': new_token}, 200

@app.route("/secret")
@jwt_required
def secret():
    """A secret."""
    return "Keep it secret. Keep it safe."
    
@app.route("/tournaments/", methods=["GET", "POST"])
def tournaments():
    """
    .. :quickref: Tournaments; Get a list of all tournaments in the database.
    """
    if request.method == "GET":
        out = []
        tournaments = rugby.models.Tournament.all()
        for tournament in tournaments:
            out.append({"name": tournament.name,
                        "url": url_for("tournament_season_list", tournament=tournament.name.replace(" ", "_"),  _external=False),})
        return out
    elif request.method == "POST":
        out = rugby.models.Tournament.add(request.data)
        return out.to_dict()

@app.route("/tournament/<tournament>", methods=["GET", "PUT", "DELETE"])
def tournament_details(tournament):
    tournament = " ".join(tournament.split("_"))
    if request.method=="GET":
        tournament = rugby.models.Tournament.from_query(name=tournament)
    elif request.method=="PUT":
        tournament = rugby.models.Tournament.update(name=tournament, data=request.data)
    elif request.method=="DELETE":
        return rugby.models.Tournament.remove(name=tournament)
    return {"name": tournament.name,
            "url": url_for("tournament_details",
                           tournament=tournament.name.replace(" ", "_")),
            "seasons":  url_for("tournament_season_list",
                                tournament=tournament.name.replace(" ", "_"))}

@app.route("/tournament/<tournament>/seasons")
def tournament_season_list(tournament):
    tournament = " ".join(tournament.split("_"))
    tournament_s = rugby.models.Season.from_query(tournament=tournament);
    out = []
    for season in tournament_s:
        out.append({"name": season.season, "url": url_for("season", tournament=tournament.replace(" ", "_"), season=season.season)})
    return out

@app.route("/seasons/", methods=["GET", "POST"])
def seasons():
    if request.method=="GET":
        seasons = rugby.models.Season.all()
        out = []

        for season in seasons:
            tournament = rugby.models.Tournament.get(season.tournament)
            out.append({"name": season.name,
                        "url": url_for("season", tournament=tournament.name.replace(" ", "_"), season=season.name,  _external=False),
                        "tournament": tournament.name})
        return out
    elif request.method=="POST":
        print(request.data)
        season = rugby.models.Season.add(request.data)
        return season.to_dict()


    
@app.route("/seasons/<tournament>/<season>")
def season(tournament, season):
    tournament = " ".join(tournament.split("_"))
    season = " ".join(season.split("_"))
    tournament = rugby.models.Season.from_query(tournament=tournament, season=season)
    matches = []
    for match in tournament.matches:
        matches.append({"home": match.teams['home'].short_name,
                        "away": match.teams['away'].short_name,
                        "date": match.date.isoformat(),
                        "score": match.score,
                        "url": url_for("match",
                                       home=match.teams['home'].short_name.replace(" ", "_").replace("/", "~"),
                                       away=match.teams['away'].short_name.replace(" ", "_").replace("/", "~"),
                                       date=f"{match.date:%Y-%m-%d}",  _external=False)})
    for match in tournament.future:
        matches.append({"home": match.teams['home'].short_name,
                        "away": match.teams['away'].short_name,
                        "date": match.date.isoformat(),
                        "url": url_for("match",
                                       home=match.teams['home'].short_name.replace(" ", "_").replace("/", "~"),
                                       away=match.teams['away'].short_name.replace(" ", "_").replace("/", "~"), date=f"{match.date:%Y-%m-%d}",  _external=False)})

        
    return {"matches": matches,
            "tournament": tournament.name,
            "season": tournament.season,
            "table": url_for("league_table", tournament=tournament.name.replace(" ", "_"), season=tournament.season),
            "teams": [{"name": team.short_name,
                       "url": url_for("team", shortname=team.short_name.replace(" ", "_").replace("/", "~"), _external=False)} for team in tournament.teams()]
            }
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

@app.route("/matches/<team1>/<team2>/")
def derbies(team1, team2):
    if "limit" in request.args:
        limit=request.args['limit']
    else:
        limit = 5
        
    team2 = " ".join(team2.split("_"))
    team1 = " ".join(team1.split("_"))
    matches_q = rugby.models.Match.from_query(home=team1, away=team2, limit=limit)
    #matches_q += rugby.models.Match.from_query(home=team2, away=team1)
    matches = []
    for match in matches_q:
        print(match)
        matches.append({"home": match['home']['name'],
                        "away": match['away']['name'],
                        "tournament": match['tournament'],
                        "season": match['season'],
                        "date": match['date'].isoformat(),
                        "score": match['score'],
                        "url": url_for("match", home=match['home']['name'],
                                       away=match['away']['name'], date=f"{match['date']:%Y-%m-%d}",  _external=False)})    
    return matches


@app.route("/seasons/<tournament>/<season>/matches/<team1>/<team2>/")
def season_derbies(tournament, season, team1, team2):
    tournament = " ".join(tournament.split("_"))
    season = " ".join(season.split("_"))
    team2 = " ".join(team2.split("_"))
    team1 = " ".join(team1.split("_"))
    tournament = rugby.models.Season.from_query(tournament=tournament, season=season)
    matches = []
    for match in tournament.matches:
        if {match.teams['home'].short_name, match.teams['away'].short_name} == {team1, team2}:
            matches.append({"home": match.teams['home'].short_name,
                            "away": match.teams['away'].short_name,
                            "date": match.date.isoformat(),
                            "score": match.score,
                            "url": url_for("match", home=match.teams['home'].short_name, away=match.teams['away'].short_name, date=f"{match.date:%Y-%m-%d}",  _external=False)})
    
    return matches

        
@app.route("/teams/", methods=["GET", "POST"])
def teams():
    """
    Teams
    """
    if request.method=="GET":
        teams = rugby.models.Team.all()
        teams_r = []
        for team in teams:
            teams_r.append({"name": team.name,
                        "shortname": team.shortname,
                        "url": url_for("team", shortname=team.shortname.replace("/", "~").replace(" ", "_"))})
        return teams_r
    elif request.method=="POST":
        team_new = rugby.models.Team.add(request.data)
        return team_new.to_dict()
    
@app.route("/teams/<shortname>", methods=["GET", "PUT", "DELETE"])
def team(shortname):
    shortname = shortname.replace("_", " ")
    shortname = shortname.replace("~", "/")
    if request.method=="GET":
        team = rugby.models.Team.from_query(shortname)
    elif request.method=="DELETE":
        team = rugby.models.Team.remove(shortname)
        return {}
    elif request.method=="PUT":
        team = rugby.models.Team.update(shortname, data=request.data)
    return {"name": team.name,
            "url": url_for("team", shortname=team.shortname.replace(" ", "_")),
            "country": team.country,
            "colors": {"primary": f"#{team.color_primary}"},
            "short name": team.shortname}

@app.route("/players/")
def all_players():
    return [{"firstname": playerd.firstname,
             "surname": playerd.surname,
             "url": url_for("player", firstname=playerd.firstname, surname=playerd.surname.replace(" ", "_"))
    } for playerd in rugby.models.Player.all()]

@app.route("/player/<firstname>+<surname>")
def player(firstname, surname):
    surname = " ".join(surname.split("_"))
    player = rugby.models.Player.from_query(firstname=firstname, surname=surname)
    return {"firstname": player.firstname, "surname": player.surname, "country": player.country}

@app.route("/matches/", methods=["GET", "POST"])
def all_matches():
    if request.method=="GET":
        return rugby.models.Match.all()
    elif request.method=="POST":
        return rugby.models.Match.add_dict(request.data).to_dict()

@app.route("/matches/<home>/<away>/<date>", methods=["GET", "PUT", "DELETE"])
def match(home, away, date):
    """
    .. :quickref: Match; Get the details for a given match.
    """
    home = home.replace("_", " ").replace("~", "/")
    away = away.replace("_", " ").replace("~", "/")
    
    if request.method=="GET":
        try:
            match = rugby.models.Match.from_query(home=home, away=away, date=date)
        except NoResultFound:
            return {}, status.HTTP_404_NOT_FOUND
        return match.to_rest()
    
    elif request.method=="PUT":
        match = rugby.models.Match.update(home=home, away=away, date=date, data=request.data)
        return match.to_rest()
    if request.method=="DELETE":
        match = rugby.models.Match.remove(home=home, away=away, date=date)
        return {}

@app.route("/event/<idnumber>", methods=["PUT"])
def event(idnumber):
    if request.method=="PUT":
        event = rugby.models.Event.update(idnumber=idnumber, data=request.data)
        return event.to_rest()
        
@app.route("/matches/<home>/<away>/<date>/events", methods=["GET", "POST"])
def events(home, away, date):
    """
    .. :quickref: Match; Get a list of events for a match.
    """
    home = home.replace("_", " ").replace("~", "/")
    away = away.replace("_", " ").replace("~", "/")
    
    if request.method=="GET":
        try:
            scores = rugby.models.Event.from_query(home=home, away=away, date=date)
        except NoResultFound:
            return {}, status.HTTP_404_NOT_FOUND
        #return [score.to_rest() for score in scores]
        return scores

    elif request.method=="POST":
        data = request.data
        data['home'] = home
        data['away'] = away
        data['date'] = date
        print(data)
        result = rugby.models.Event.add_dict(data)
        return result.to_rest()
            

        

    
@app.route("/matches/<home>/<away>/<date>/lineup")
def lineup(home, away, date):
    """
    The lineups for a given match.

    .. :quickref: Lineups; Get lineups for a given match.

    **Example request** (http)

    .. sourcecode:: http

          GET /rugby/matches/Blues/Hurricanes/2020-06-14/lineup HTTP/1.1
          Host: https://data.daniel-williams.co.uk/
          Accept: application/json

    **Example request** (cUrl)

    .. sourcecode:: bash

          curl https://data.daniel-williams.co.uk/rugby/matches/Blues/Hurricanes/2020-06-14/lineup

    **Example response**

    .. sourcecode:: json



    :query home: Short-name of the home team.
    :query away: Short-name of the away team.
    :query date: The date of the match in ``YYYY-MM-DD`` format.

    :returns: :class:`rugby.match.Match`

    :resheader Content-Type: application/json
    :status 200: lineups found
    """
    lineup = rugby.models.Position.from_query(home=home, away=away, date=date)
    home = rugby.models.Team.from_query(home.replace("_", " "), session).id
    away = rugby.models.Team.from_query(away.replace("_", " "), session).id
    return {"home": {position['number']: {"player": position['player'].name,
                                          "url": url_for("player", firstname=position['player'].firstname, surname=position['player'].surname.replace(" ", "_")),
                                          "on": position['on'],
                                          "ranges": position['time_ranges'],
                                          "total_time": utils.total_time_from_ranges(position['time_ranges'])[1],
                                          "off": position['off'],
                                          }
                                          for position in lineup if position['team'] == home},
            "away": {position['number']: {"player": position['player'].name,
                                          "url": url_for("player", firstname=position['player'].firstname, surname=position['player'].surname.replace(" ", "_")),
                                          "on": position['on'],
                                          "ranges": position['time_ranges'],
                                          "total_time": utils.total_time_from_ranges(position['time_ranges'])[1],
                                          "off": position['off'],
                                          } for position in lineup if position['team'] == away}
    } 

if __name__ == '__main__':
    
    app.run()
