import json
import glob
import re

import rugby as rugby
import rugby.sru as sru
import rugby.professional as pro
import pandas as pd
import rugby.data as rdata

from flask_api import FlaskAPI
from flask_compress import Compress
from flask_cors import CORS

app = FlaskAPI(__name__)
Compress(app)
CORS(app)


scottish_competitions = {"SRU West 3": "915", "SRU West 2": "639", "SRU West 1": "638"}
pro_competitions = {"English Premiership": "Gallagher Premiership", "Pro14": "Guinness Pro14"}

@app.route("/leagues/")
def leagues():
    leagues = list(pro_competitions.keys()) + list(scottish_competitions.keys())
    out = []

    for league in leagues:
        out.append({"name": league,
                    "seasons": seasons(league)})
    return out


def seasons(league):
    league = dict(list(pro_competitions.items()) + list(scottish_competitions.items()))[league]
    files = glob.glob(rugby.__path__[0]+f"/json_data/{league}-*.json")
    out = []
    for file in files:
        try:
            out.append(re.search("-([0-9\-]*[0-9]+)(?:.json)", file).groups()[0])
        except:
            pass
    return out

@app.route("/teams/<league>/<season>", methods=['GET'])
def teams(league="west3", season="2019-2020"):

    out = []
    
    if league in scottish_competitions.keys():
        league = sru.SRUResults(scottish_competitions[league], season)
        for match in league.results_list():
            if "P" in match['home_score'].strip():
                continue
            else:
                out.append(match)
                #out.append(f"{match['date']:%Y-%m-%d} {match['home']:>30} {match['home_score']:>3} v {match['away_score']:<3} {match['away']:<30}")
    elif league in pro_competitions.keys():
        league = pro_competitions[league]
        data = pd.read_json(rugby.__path__[0]+f"/json_data/{league}-{season}.json")
        tournament = rdata.Tournament(league, season, data)

        return list(tournament.teams())
    return None

@app.route("/results/", defaults={"league": "west3", "season":"2019-2020"})
@app.route("/results/<league>/", defaults={"season":"2019-2020"})
@app.route("/results/<league>/<season>", methods=['GET'])
def results(league="west3", season="2019-2020"):

    out = []
    
    if league in scottish_competitions.keys():
        league = sru.SRUResults(scottish_competitions[league], season)
        for match in league.results_list():
            if "P" in match['home_score'].strip():
                continue
            else:
                out.append(match)
                #out.append(f"{match['date']:%Y-%m-%d} {match['home']:>30} {match['home_score']:>3} v {match['away_score']:<3} {match['away']:<30}")
    elif league in pro_competitions.keys():
        league = pro_competitions[league]
        data = pd.read_json(rugby.__path__[0]+f"/json_data/{league}-{season}.json")
        tournament = rdata.Tournament(league, season, data)

        for match in tournament.matches:
            out.append(dict(teams = dict(home=match.teams['home'],
                                         away=match.teams['away']),
                            date = match.date,
                            scores = {"home": int(match.scores['home'].total),
                                      "away": int(match.scores['away'].total)}
                            )
            )
            
    return {"matches": out, "teams": tournament.teams(), "matrix": tournament.matrix()}


if __name__ == '__main__':
    
    app.run()
