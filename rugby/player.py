"""Player and position data."""

from .scores import Scores

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

    @classmethod
    def from_dict(cls, position, player):
        cls.name = player['name']
        cls.position = int(position)
        cls.on_times = player['on']
        cls.off_times = player['off']
        cls.cards = {'red': player['reds'], 'yellow': player['yellows']}

    def __repr__(self):
        output_string = "{}\t| {}"
        return output_string.format(self.position, self.player.name)



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
        return Scores(player_scores)

    def _find_position(self, match):
        """
        Find what position this player was playing in for a given match.
        """

        df = match.lineups['home'].lineup
        position = df[df.name==self.name]

        if len(position)==1:
            side = match.teams['home']

        else:
            df = match.lineups['away'].lineup
            position = df[df.name==self.name]
            side = match.away
            
        if len(position) == 0: 
            return None, None # This player wasn't playing in this match
        
        return position.index[0], side
        
    def play_time(self, match):
        """Find this player's game time in a given match."""
        df = pd.concat([match.lineups['home'].lineup, match.lineups['away'].lineup])
        return df[df.name==self.name].iloc[0]['game time']
        
    
    def total_play_time(self, tournament):
        """Find this player's total game time in a tournament."""
        df = tournament.lineup_summary()
        return df[df.name==self.name].sum()['game time']

    def __eq__(self, other):
        return self.name == other.name
    
    def __repr__(self):
        return self.name
    
    def __hash__(self):
        return self.name.__hash__()
