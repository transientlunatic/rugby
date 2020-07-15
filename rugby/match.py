"""
Match information.
"""

import ast
import json, yaml

import pandas as pd
import numpy as np

from .player import Player
from .scores import Scores
from .utils import json_serial


class Match(object):

    def __init__(self, row, tournament=None):
        """
        A row from the JSON data file.
        """
        self.score = {"home": row['home']['score'],
                      "away": row['away']['score']}

        if tournament and hasattr(tournament, "teams_dict"):
            self.teams = {'home': tournament.teams_dict[row['home']['team']],
                          'away': tournament.teams_dict[row['away']['team']]
                     }
        else:
            self.teams = {'home': row['home']['team'],
                          'away': row['away']['team']
            }
        try:
            self.date =  row.date.to_datetime()
        except AttributeError:
            self.date = pd.to_datetime(row.date)
            
        self.stadium = row.stadium
        if hasattr(row, "tround"):
            self.round = row['tround']

        # Store tournament metadata
        if not isinstance(tournament, type(None)):
            self.season = tournament.season
            self.tournament = tournament.name
            
        # Handle the lineups
        if "lineup" in row['home']:
            self.lineups = {'home': Lineup(row['home']['lineup']),
                            'away': Lineup(row['away']['lineup'])
            }

        if "scores" in row['home']:
            # Handle the scores
            self.scores = {'home': Scores(row['home']['scores']),
                           'away': Scores(row['away']['scores'])
            }
            for i, score in self.scores['home'].scores.iterrows():
                if score['player']==None:
                    continue
                self.scores['home'].scores.at[i, 'player'] = (self.find_player(score['player']))
            for i, score in self.scores['away'].scores.iterrows():
                self.scores['away'].scores.at[i, 'player'] = (self.find_player(score['player']))
                
        else:
            self.scores = None
        try:
            self.url = row.url
        except:
            self.url = None

    def find_player(self, search):
        for i, player in pd.concat([self.lineups['home'].lineup, self.lineups['away'].lineup]).iterrows():
            if search in player['name']: 
                return player['name']
            
    def all_scores(self):
        """
        Get a list of all of the scoring events in this match.
        """
        scores = self.scores['home'].scores.append(self.scores['away'].scores)
        return Scores(scores)

    def to_dict(self):
        """
        Serialise this match object in a dict.
        """
        data = {}
        data['date'] = self.date.isoformat()
        data['stadium'] = self.stadium
        data['tournament'] = self.tournament
        data['season'] = self.season
        for state in ["home", "away"]:
            data[state] = {}
            data[state]['team'] = self.teams[state]
            data[state]['score'] = self.score[state]
            if hasattr(self, "lineups"):
                data[state]['lineup'] = self.lineups[state].to_dict()
            if hasattr(self, "scores") and self.scores != None:
                data[state]['scores'] = self.scores[state].to_dict()

        return data

    def to_json(self, filename=None):
        """Serialise this object in JSON format."""
        if filename:
            with open(filename, "w") as f:
                json.dump(self.to_dict(), f, default=json_serial)
        else:
            return json.dumps(self.to_dict(), default=json_serial)
    

    def to_yaml(self, filename=None):
        """Serialise this object in YAML format."""
        if filename:
            with open(filename, "w") as f:
                yaml.safe_dump(self.to_dict(), stream=f)
        else:
            return yaml.safe_dump(self.to_dict())

    @classmethod
    def from_json(cls, file):
        """
        Create a match from a json file.
        """
        with open(file, "r") as f:
            data = json.load(f)
        data = pd.DataFrame.from_dict([data]).iloc[0]

        return cls(data)

    @classmethod
    def from_yaml(cls, file):
        """
        Create a match from a yaml file.
        """
        with open(file, "r") as f:
            data = yaml.safe_load(f)
        data = pd.DataFrame.from_dict([data]).iloc[0]

        return cls(data)

    def players(self):
        """
        Get a list of all of the players named in the lineups.
        """
        players = []
        players += self.lineups['home'].players()
        players += self.lineups['away'].players()
        return players
            
    def __repr__(self):
        if self.scores:
            layout = f"""{self.date:%Y-%m-%d %H:%M} {self.teams['home']} {self.scores['home'].total:>3} v {self.scores['away'].total:<3} {self.teams['away']}"""
        else:
            layout = f"""{self.date:%Y-%m-%d %H:%M} {self.teams['home']} v {self.teams['away']}"""
            
        return layout

    def _repr_html_(self):
        """
        HTML Representation
        """
        if self.scores!=None:
            layout ="""<h2> {a.scores[home].total}\t{a.teams[home]} - {a.teams[away]}\t{a.scores[away].total} </h2>"""
            layout +="""
        <h3> {a.date:%Y-%m-%d %H:%M}</h3>
        <table>
        <tr>
        <td> {a.lineups[home].html} </td>
        <td> {a.scores[home].html} </td>
        <td> {a.scores[away].html} </td>
        <td> {a.lineups[away].html} </td>
        </tr>
        </table>"""
        else:
            layout ="""<h2> {a.teams[home]} - {a.teams[away]}</h2> <h3> {a.date:%Y-%m-%d %H:%M}</h3>"""
        return layout.format(a=self)



class Lineup(object):
    def __init__(self, data):
        """
        Represent a team's lineup
        """
        self.lineup = pd.DataFrame.from_dict(data, orient='index')
        # print(self.lineup.name.values)
        self.lineup.index = np.array(self.lineup.index, dtype=int)
        self.lineup.sort_index(inplace=True)
        
        self.lineup['game time'] = 0
        for key, value in self.lineup.iterrows():
            time = []
            total_time = 0

            if isinstance(value['on'], (str)):
                value['on'] = ast.literal_eval(value['on'])

            if isinstance(value['off'], (str)):
                value['off'] = ast.literal_eval(value['off'])
                
            if isinstance(value['on'], (type(None), int, float)):
                if isinstance(value['on'], type(None)):
                    valuea['on'] = "NaN"
                value['on'] = [float(value['on'])]
                
            if isinstance(value['off'], (type(None), int, float, str)):
                if isinstance(value['off'], type(None)):
                    value['off'] = "NaN"
                value['off'] = [float(value['off'])]

            if not pd.isna(value['on']).any() and not pd.isna(value['off']).any() and len(value['on'])>len(value['off']):
                value['off'] += [80]
            
            try:
                if not pd.isna(value['on']).any() and pd.isna(value['off']).any():
                    value['off'] = [80]
            except:
                print(value)
            if isinstance(value['on'], str):
                value['on'] = ast.literal_eval(value['on'])
            if isinstance(value['off'], str):
                value['off'] = ast.literal_eval(value['off'])

            try:
                if len(value['on'])<len(value['off']): value['off']+=[80]
            except TypeError:
                print(value)
            subs = sorted(value['on'] + value['off'])
            if len(subs)%2: subs.append(80)
            for i in range(int(len(subs)/2)):
                    time.append([subs[i], subs[i+1]])
                    total_time += (subs[i+1] - subs[i])
            if pd.isna(total_time): total_time = 0
            self.lineup.at[key, 'game time'] = total_time

    def players(self):
        players = [Player(name) for name in self.lineup.name.values]
        return players

    def to_dict(self):
        """Represent this lineup as a dict."""
        return self.lineup[['name', 'on', 'off', 'reds', 'yellows']].T.to_dict()
    
    def __repr__(self):
        out = []
        for key, value in self.lineup.iterrows():
            out.append("{a}\t{b[name]}\t{b[game time]}".format(a=key, b=value))
            if key == 15:
                out.append("---"*5)
        return ("\n").join(out) #, "\n")
    
    
    @property
    def html(self):
        out = []
        header = """
        <tr><th>Pos</th><th>Player</th><th>Play time</th></tr>
        """
        for key, value in self.lineup.iterrows():
            
            time = []
            #subs = value['game time'].split(",")
            #for sub in value['game time']:
            #    time.append("{}→{}".format(sub[0], sub[1]))
                    
            value['game time rep']= " ".join(time)
            
            if key == 15: 
                out.append('<tr style="border-bottom: 1px solid #000;"><td>{a}</td><td>{b[name]}</td><td>{b[game time]}</td></tr>'.format(a=key, b=value))
            else:
                out.append("<tr><td>{a}</td><td>{b[name]}</td><td>{b[game time]}</td></tr>".format(a=key, b=value))
        return "<table>" +  header + ("\n").join(out) + "</table>" #, "\n")
    
    def _repr_html_(self):
        return self.html
