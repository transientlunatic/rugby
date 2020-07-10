import ast

import pandas as pd
import numpy as np
from itertools import chain

class Scores(object):
    
    def __init__(self, data):
        self.scores = pd.DataFrame.from_dict(data)
        try:
            self.scores.sort_values('minute', inplace=True)
            self.scores['cumulative'] = self.scores.value.cumsum() 
        
            self.total = self.scores['cumulative'].iloc[-1]
        except:
            self.total = 0
        
        
    def __repr__(self):
        out = []
        for key, value in self.scores.iterrows():
            out.append("{b[player]}\t{b[type]}".format(b=value))
        return ("\n").join(out) #, "\n")
    
    @property
    def html(self):
        out = []
        for key, value in self.scores.iterrows():
            out.append("<tr><td>{b[minute]}</td><td>{b[player]}</td><td>{b[type]}</td><td>{b[cumulative]}</td></tr>".format(a=key, b=value))
        return "<table>" + ("\n").join(out) + "</table>" #, "\n")
    
    def _repr_html_(self):
        return self.html

class Match(object):
    
    def __init__(self, row):
        """
        A row from the JSON data file.
        """
        
        self.teams = {'home': row['home']['team'],
                      'away': row['away']['team']
                     }
        try:
            self.date =  row.date.to_datetime()
        except AttributeError:
            self.date = row.date
            
        self.stadium = row.stadium
        
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
            layout = f"""{self.date:%Y-%m-%d %H:%M} {self.teams['home']:>30} {self.scores['home'].total:>3} v {self.scores['away'].total:<3} {self.teams['away']:<30}"""
        else:
            layout = f"""{self.date:%Y-%m-%d %H:%M} {self.teams['home']:>30} v {self.teams['away']:<30}"""
            
        return layout

    def _repr_html_(self):
        """
        HTML Representation
        """
        layout ="""<h2> {a.scores[home].total}\t{a.teams[home]} - {a.teams[away]}\t{a.scores[away].total} </h2>
        <h3> {a.date:%Y-%m-%d %H:%M}</h3>
        <table>
        <tr>
        <td> {a.lineups[home].html} </td>
        <td> {a.scores[home].html} </td>
        <td> {a.scores[away].html} </td>
        <td> {a.lineups[away].html} </td>
        </tr>
        </table>"""
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
            if isinstance(value['on'], (type(None), int, float)):
                if isinstance(value['on'], type(None)):
                    value['on'] = "NaN"
                value['on'] = [float(value['on'])]
            if isinstance(value['off'], (type(None), int, float)):
                if isinstance(value['off'], type(None)):
                    value['off'] = "NaN"
                value['off'] = [float(value['off'])]

            
            
            try:
                if not pd.isna(value['on']) and pd.isna(value['off']):
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

class Player():
    def __init__(self, name):
        self.name = name
    
    def matches(self, tournament):
        return [x for x in tournament.matches if (self in x.players())]
    
    def positions(self, tournament):
        positions = tournament.positions()
        positions = [x for x in tournament.positions() if x.player == self]
        return positions
    
    def scores(self, tournament):
        scores = tournament.scores()
        player_scores = []
        for match_score in scores:
            player_scores += [score for i, score in match_score.scores.iterrows() if score.player in self.name]
            print(player_scores)
        
        return Scores(player_scores)#[score for score in scores if score.scores.player.values in self.name]
       
    def _find_position(self, match):
        """
        Find what position this player was playing in for a given match.
        """
        
        position = [position for position in match.home.lineup if position.player == self]
        if len(position)==1:
            side = match.home

        else:
            position = [position for position in match.away.lineup if position.player == self]
            side = match.away
            
        if len(position) == 0: 
            return None, None # This player wasn't playing in this match
        
        return position[0], side
        
    def play_time(self, match):
        position, side = self._find_position(match)
        if position == None: return 0
        return position.play_time()
    
    def total_play_time(self, tournament):
        play_time = sum([self.play_time(x) for x in self.matches(tournament)])
        return play_time
    
    def on_field_points(self, match):
        
        position, side = self._find_position(match)
        
        if position == None: 
            return 0
        
        on_field = sum([score.value for score in side.scores if (score.minute in chain(*position.playing)) 
                    and (score.type is not "conversion")
                   ])
        own_conv = sum([score.value for score in side.scores if (score.player == self) 
                    and (score.type is "conversion")
                   ])
        
        return own_conv + on_field
    
    def total_on_field_points(self, tournament):
        points = sum([self.on_field_points(x) for x in self.matches(tournament)])
        return points

    def __eq__(self, other):
        return self.name == other.name
    
    def __repr__(self):
        return self.name
    
    def __hash__(self):
        return self.name.__hash__()

class Position():
    
    def __init__(self, position, name, on, off, reds, yellows):
        self.player = Player(name)
        self.position = int(position)
        self.on_times = on
        self.off_times = off
        self.cards = {'red': reds, 'yellow': yellows}
        
        self.determine_playing()
        
    def play_time(self):
        return sum([len(time) for time in self.playing])
        
    def determine_playing(self):
        self.playing = []
        if len(self.on_times) > 0:
            if len(self.off_times) < len(self.on_times):
                self.off_times.append(80)
            for i, on_times in enumerate(self.on_times):
                try:
                    self.playing.append(range(self.on_times[i], self.off_times[i]))
                except IndexError:
                    print(self.on_times, self.off_times)
        if len(self.playing)==0: 
            self.playing += range(0)

    def from_dict(self, position, player):
        self.name = player['name']
        self.position = int(position)
        self.on_times = player['on']
        self.off_times = player['off']
        self.cards = {'red': player['reds'], 'yellow': player['yellows']}
        
    def __repr__(self):
        output_string = "{}\t| {}"
        return output_string.format(self.position, self.player.name)

class Score():
    
    def __init__(self, match, player, type, value, minute):
        self.match = match
        self.player = Player(player)
        self.type = type
        self.value = value
        self.minute = minute


    def __repr__(self):
        return "{} by {} ({}-{})".format(self.type, self.player.name, self.match.home, self.match.away)

class Team(): 
    
    def __init__(self, name):
        self.name = name.strip()
    
    def __repr__(self):
        return "{}".format(self.name)
    
    def __eq__(self, other):
        return self.name == other.name
    
    def __hash__(self):
        return self.name.__hash__()
    
    def matches(self, tournament, filts=None):
        if filts=="home":
            return [x for x in tournament.matches if (x.home.team == self)]
        elif filts=="away":
            return [x for x in tournament.matches if (x.away.team == self)]
        else:
            return [x for x in tournament.matches if (x.home.team == self) or (x.away.team == self)]
        
    def squad(self, tournament):
        positions = []
        positions += [x.away.lineup for x in self.matches(tournament, filts="away")]
        positions += [x.home.lineup for x in self.matches(tournament, filts="home")]
        positions = chain(*positions)
        players = set([y.player for y in positions])
        return list(players)

class Tournament():
    
    def __init__(self, name, season, matches):
        
        self.matches = [Match(x) for i, x in matches.iterrows()]
        self.season=season
        self.name = name
        
    def teams(self):
        """
        Return a set of all of the teams which had matches in this tournament.
        """
        return list(set(chain.from_iterable((x.teams['home'], x.teams['away']) for x in self.matches)))

    def positions(self):
        """
        Provide a list of all of the positions played.
        """
        positions = pd.DataFrame([])
        positions = positions.append([x.lineups['home'].lineup for x in self.matches], ignore_index=True)
        positions = positions.append( [x.lineups['away'].lineup for x in self.matches], ignore_index=True)
        #positions = chain(*positions)
        return positions #list(positions)

    def fixtures_table(self):
        data = [[pd.to_datetime(match.date), match.teams['home'], match.teams['away']] for match in self.matches]
        return pd.DataFrame(data, columns=["date", "home", "away"])
    
    def results_table(self):
        scores = [[match.teams['home'], match.teams['away'], match.scores['home'].total, match.scores['away'].total, match.scores['home'].total-match.scores['away'].total] for match in self.matches]
        return pd.DataFrame(scores, columns=["home", "away", "home_score", "away_score", "difference"])
    
    # def matrix(self):
    #     scores = [[match.teams['home'], match.teams['away'], match.scores['home'].total, match.scores['away'].total, match.scores['home'].total-match.scores['away'].total] for match in self.matches]
    #     matrix = {}
    #     for match in self.matches:
    #         if not match.teams['home'] in matrix:
    #             matrix[match.teams['home']] = {}

    #         matrix[match.teams['home']][match.teams['away']] = {"home":int(match.scores['home'].total),
    #                                                             "away": int(match.scores['away'].total)}
    #     return matrix
    
    def scores(self):
        scores = []
        for match in self.matches:
            scores.append(match.all_scores())
        return scores
    
    def players(self):
        positions = self.positions()
        players = set([y.name for i,y in positions.iterrows()])
        return list(players)
