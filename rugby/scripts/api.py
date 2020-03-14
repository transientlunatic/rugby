import json

import rugby as rugby
import rugby.sru as sru
import rugby.professional as pro
import pandas as pd
import rugby.data as rdata


from flask_api import FlaskAPI
app = FlaskAPI(__name__)


scottish_competitions = dict(west3 = "915", west2 = "639", west1 = "638")
pro_competitions = dict(premiership = "Gallagher Premiership", pro14 = "Guinness Pro14")

@app.route("/results/", defaults={"league": "west3", "season":"2019-2020"})
@app.route("/results/<league>/", defaults={"season":"2019-2020"})
@app.route("/results/<league>/<season>", methods=['GET'])
def results(league="west3", season="2019-2020"):

    out = []
    
    if league.lower() in scottish_competitions.keys():
        league = sru.SRUResults(scottish_competitions[league], season)
        for match in league.results_list():
            if "P" in match['home_score'].strip():
                continue
            else:
                out.append(match)
                #out.append(f"{match['date']:%Y-%m-%d} {match['home']:>30} {match['home_score']:>3} v {match['away_score']:<3} {match['away']:<30}")
    elif league.lower() in pro_competitions.keys():
        league = pro_competitions[league]
        data = pd.read_json(rugby.__path__[0]+f"/json_data/{league}-{season}.json")
        tournament = rdata.Tournament(league, season, data)

        for match in tournament.matches:
            out.append(dict(home=match.teams['home'], away=match.teams['away']))
    return out
