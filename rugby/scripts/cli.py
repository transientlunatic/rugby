"""
Download Scottish rugby data
"""
import rugby as rugbymod
import rugby.sru as sru
import rugby.professional as pro
import click
import pandas as pd
import rugby.data as rdata

scottish_competitions = dict(west3 = "915", west2 = "639", west1 = "638")
pro_competitions = dict(premiership = "Gallagher Premiership", pro14 = "Guinness Pro14")

@click.group()
def rugby():
    pass

@click.command()
@click.option('--league', default="west3", help='The league.')
@click.option('--season', prompt='season',
              help='The season')
@click.option('--query', default=None)
@click.option('-n', default=10)
def results(league, season, query=None, n=None):
    if league.lower() in scottish_competitions.keys():
        league = sru.SRUResults(scottish_competitions[league], season)
        for match in league.results_list():
            if "P" in match['home_score'].strip():
                continue
            else:
                print(f"{match['date']:%Y-%m-%d} {match['home']:>30} {match['home_score']:>3} v {match['away_score']:<3} {match['away']:<30}")
    elif league.lower() in pro_competitions.keys():
        league = pro_competitions[league]
        data = pd.read_json(rugbymod.__path__[0]+f"/json/{league}-{season}.json")
        if query:
            data = data.query(query)
        if n:
            data = data.loc[:n]
        #matches = [rdata.Match(row) for index, row in data.iterrows()]
        tournament = rdata.Tournament(league, season, data)
        for match in tournament.matches:
            print(match)
                
rugby.add_command(results)

@click.command()
@click.option('--league', default="west3", help='The league.')
@click.option('--season', prompt='season',
              help='The season')
@click.option('--player', prompt="Player name")
@click.option('--query', default=None)
@click.option('-n', default=10)
def players(league, season, player, query=None, n=None):
    if league.lower() in scottish_competitions.keys():
        league = sru.SRUResults(scottish_competitions[league], season)
        for match in league.results_list():
            if "P" in match['home_score'].strip():
                continue
            else:
                print(f"{match['date']:%Y-%m-%d} {match['home']:>30} {match['home_score']:>3} v {match['away_score']:<3} {match['away']:<30}")
    elif league.lower() in pro_competitions.keys():
        league = pro_competitions[league]
        data = pd.read_json(rugbymod.__path__[0]+f"/json/{league}-{season}.json")
        tournament = rdata.Tournament(league, season, data)

        player = rdata.Player(player)
        print(f"{player.name:<20} {player.scores(tournament).total:3}")
                
rugby.add_command(players)

@click.command()
@click.option('--league', default="west3", help='The league.')
@click.option('--season', prompt='season',
              help='The season')
@click.option('--query', default=None)
@click.option('-n', default=10)
def teams(league, season, query=None, n=None):
    if league.lower() in scottish_competitions.keys():
        league = sru.SRUResults(scottish_competitions[league], season)
        for match in league.results_list():
            if "P" in match['home_score'].strip():
                continue
            else:
                print(f"{match['date']:%Y-%m-%d} {match['home']:>30} {match['home_score']:>3} v {match['away_score']:<3} {match['away']:<30}")
    elif league.lower() in pro_competitions.keys():
        league = pro_competitions[league]
        data = pd.read_json(rugbymod.__path__[0]+f"/json/{league}-{season}.json")
        if query:
            data = data.query(query)
        if n:
            data = data.loc[:n]
        #matches = [rdata.Match(row) for index, row in data.iterrows()]
        tournament = rdata.Tournament(league, season, data)
        for team in tournament.teams():
            print(team)
                
rugby.add_command(teams)

@click.command()
@click.option('--league', default="west3", help='The league.')
@click.option('--season', prompt='season', help='The season')
@click.option('--query', default=None)
@click.option('-n', default=10)
@click.option('--json', default=None, help='Save results as JSON')
@click.option('--yaml', default=None, help='Save results as YAML')
def fixtures(league, season, query=None, n=10, json=None, yaml=None):
    if league.lower() in scottish_competitions.keys():
        league = sru.SRUResults(competitions[league], season)
        for match in league.fixtures_list():
            print(f"{match['date']:%Y-%m-%d} {match['home']:>30} v {match['away']:<30}")
    elif league.lower() in pro_competitions.keys():
        league = pro_competitions[league]
        data = pd.read_json(rugbymod.__path__[0]+f"/json/{league}-fixtures.json")
        if query:
            data = data.query(query)
        if n:
            data = data.loc[:n]
        matches = [rdata.Match(row) for index, row in data.iterrows()]
        for match in matches:
            print(match)
rugby.add_command(fixtures)

@click.command()
@click.option('--league', default="Pro14", help='The league.')
@click.option('--season', default="2019-2020", help='The season')
def update(league, season):
    if league.lower() in pro_competitions.keys():
        league = pro_competitions[league]
        pro.download_json(season, league)
        pro.download_fixtures(season, league)
rugby.add_command(update)


if __name__ == '__main__':
    rugby()
