"""
Download Scottish rugby data
"""
import rugby.models
import click

scottish_competitions = dict(west3 = "915", west2 = "639", west1 = "638")
pro_competitions = dict(premiership = "Gallagher Premiership", pro14 = "Guinness Pro14")

@click.group()
def rugbycli():
    pass

@click.command()
@click.argument("tournament")
@click.argument("season")
@click.option('--query', default=None)
@click.option('-n', default=10)
def results(tournament, season, query=None, n=None):
        tournament = rugby.models.Season.from_query(tournament=tournament, season=season)
        for match in tournament.matches:
            click.echo(match)
                
rugbycli.add_command(results)

# @click.command()
# @click.argument('json')
# @click.option('--player', prompt="Player name")
# @click.option('--query', default=None)
# @click.option('-n', default=10)
# def players(json, player, query=None, n=None):
#         tournament = rdata.Tournament.from_json(json)
#         player = rdata.Player(player)
#         print(f"{player.name:<20} {player.scores(tournament).total:3}")
# rugby.add_command(players)

@click.command()
@click.argument("json")
@click.option('--query', default=None)
@click.option('-n', default=10)
def teams(json, query=None, n=None):
    tournament = rdata.Tournament.from_json(json)
    for team in tournament.teams():
        click.echo(team)   
rugbycli.add_command(teams)

@click.command()
@click.argument("json")
@click.option('-n', default=10)
def fixtures(json, query=None, n=10):
    tournament = rdata.Tournament.from_json(json)
    for match in tournament.future:
        click.echo(match)
rugbycli.add_command(fixtures)

# @click.command()
# @click.option('--league', default="Pro14", help='The league.')
# @click.option('--season', default="2019-2020", help='The season')
# def update(league, season):
#     if league.lower() in pro_competitions.keys():
#         league = pro_competitions[league]
#         pro.download_json(season, league)
#         pro.download_fixtures(season, league)
# rugby.add_command(update)


if __name__ == '__main__':
    rugbycli()
