from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Boolean
from sqlalchemy.ext.declarative import declarative_base

from sqlalchemy import create_engine
from sqlalchemy.orm.exc import NoResultFound

from sqlalchemy import or_

from datetime import datetime, timedelta

Base = declarative_base()

import rugby
from flask import url_for

import os
if 'RUGBYDB' in os.environ:
    db = os.environ['RUGBYDB']
else:
    db = f"{rugby.__path__[0]}/rugby.db"

import bcrypt

engine = create_engine("sqlite:///"+db)

Base.metadata.create_all(engine)

# from sqlalchemy.orm import sessionmaker
# DBSession = sessionmaker(bind=engine)
# session = DBSession()

from flask_sqlalchemy_session import current_session as session

import rugby.data

class User(Base):
    __tablename__ = 'user'
    id = Column(Integer, primary_key=True)
    name = Column(String(250), nullable=False)
    username = Column(String(250), nullable=False)
    password = Column(String(250), nullable=False)
    registered_on = Column(DateTime, nullable=False)
    admin = Column(Boolean, nullable=False, default=False)

    @classmethod
    def find_user(cls, username, session=session):
        """Find a user from a username."""
        return session.query(cls).filter_by(username=username).one()

    @classmethod
    def create_user(cls, name, username, password, session=session):
        """Create a new user in the database."""
        try:
            user = cls.find_user(username, session)
        except NoResultFound:
            salt = bcrypt.gensalt()
            user = cls(name=name,
                       username=username,
                       password=bcrypt.hashpw(password.encode(), salt),
                       registered_on=datetime.now())
            session.add(user)
            session.commit()
        return user

    @classmethod
    def login(cls, username, password):
        """Log the user in."""
        db_user = cls.find_user(username)
        salt = bcrypt.gensalt()
        if bcrypt.checkpw(password.encode(), db_user.password):
            return {"id": db_user.username}
        else:
            return False

class Tournament(Base):
    __tablename__ = 'tournament'
    id = Column(Integer, primary_key=True)
    name = Column(String(250), nullable=False)
    @classmethod
    def all(cls, session=session):
        return session.query(cls).all()
    @classmethod
    def get(cls, id):
        try:
            return session.query(cls).filter_by(id=id).one()
        except NoResultFound:
            return None
    
    @classmethod
    def add(self, tournament,  session=session):
        try:
            tournament = session.query(Tournament).filter_by(name=tournament.name).one()
        except NoResultFound:
            tournament = Tournament(name=tournament.name)
            session.add(tournament)
            session.commit()
        return tournament

class Season(Base):
    __tablename__ = "season"
    id = Column(Integer, primary_key=True)
    name = Column(String(250), nullable=False)
    tournament = Column(Integer, ForeignKey("tournament.id"))

    @classmethod
    def all(cls, session=session):
        return session.query(cls).all()
    
    @classmethod
    def add(self, tournament, session=session):
        tournament_id = Tournament.add(tournament).id
        try:
            season = session.query(Season).filter_by(name=tournament.season, tournament=tournament_id).one()
        except NoResultFound:
            season = Season(name=tournament.season, tournament=tournament_id)
            session.add(season)
            session.commit()
        return season
    
    @classmethod
    def from_query(self, tournament, season=None, session=session):
        tournament = session.query(Tournament).filter_by(name=tournament).one()

        if season:
            season = session.query(Season).filter_by(name=season, tournament=tournament.id).one()
        
            return rugby.data.Tournament(
                name=tournament.name,
                season=season.name, 
                matches=season.matches(session))
        else:
            seasons = session.query(Season).filter_by(tournament=tournament.id).all()
            return [rugby.data.Tournament(
                name=tournament.name,
                season=season.name, 
                matches=season.matches(session)) for season in seasons]
        
    
    def matches(self, session=session):
        matches = session.query(Match).filter_by(season=self.id).all()
        matches = [match.to_dict(session) for match in matches]
        return matches

class Team(Base):
    __tablename__ = "team"
    id = Column(Integer, primary_key=True)
    name = Column(String(250), nullable=False)
    shortname = Column(String(250), nullable=False)
    color_primary = Column(String(6), nullable=False)
    color_secondary = Column(String(6), nullable=False)
    color_extra = Column(String(6), nullable=False)
    country = Column(String(250), nullable=False)

    @classmethod
    def all(self):
        return session.query(Team).all()
    
    @classmethod
    def from_query(self, shortname, session=session):
        return session.query(Team).filter_by(shortname=shortname).one()
    
    @classmethod
    def add(self, team, session=session):
        """
        Add a team to the database if it doesn't exist already.
        Return its ID.
        """
        try:
            team = Team.from_query(team.short_name)
        except NoResultFound:
            team = Team(name=team.name, shortname=team.short_name)
            session.add(team)
            session.commit()
        return team
    
    def to_dict(self):
        return dict(name=self.name, 
                    short_name=self.shortname,
                    colors={"primary": self.color_primary,
                            "secondary": self.color_secondary,
                            "extra": self.color_extra},
                    country=self.country                    
                   )
    
class Match(Base):
    __tablename__ = "match"
    id = Column(Integer, primary_key=True)
    date = Column(DateTime)
    season = Column(Integer, ForeignKey("season.id"))
    home = Column(Integer, ForeignKey("team.id"))
    away = Column(Integer, ForeignKey("team.id"))
    home_score = Column(Integer)
    away_score = Column(Integer)

    @classmethod
    def all(self):
        return [rugby.data.Match(match.to_dict(session)).to_rest()
                for match in session.query(Match).all()]
    
    @classmethod
    def from_query(self, home, away, date=None, session=session):
        
        home = Team.from_query(home, session).id
        away = Team.from_query(away, session).id

        if date:
            date = datetime.strptime(date, "%Y-%m-%d")
        
            match = session.query(Match).filter(Match.date.between(date, date+timedelta(days=1))).filter_by(home=home, away=away).one()
            match_o = rugby.data.Match(match.to_dict(session))
            match_o.id = match.id
            return match_o
            

        else:
            matches = session.query(Match).filter(
                (Match.home.in_([home, away]) & (Match.away.in_([home, away]))))
            return [rugby.data.Match(match.to_dict(session)).to_rest() for match in matches]


    
    @classmethod
    def add(self, match):
        """
        Add a match object to the database.
        """
        tournament = session.query(Tournament).filter_by(name=match.tournament).one()
        season = session.query(Season).filter_by(tournament=tournament.id, name=match.season).one()
        home = Team.from_query(match.teams['home'].short_name)
        away = Team.from_query(match.teams['away'].short_name)

        try:
            match = session.query(Match).filter_by(date=match.date, home=home.id, away=away.id, season=season.id).one()
        except NoResultFound:
            match = Match(date=match.date,
                 season=season.id,
                  home=home.id,
                  away=away.id,
                  home_score = match.score['home'],
                          away_score = match.score['away'],
                 )
            session.add(match)
            session.commit()
        return match
    
    def to_dict(self, session=session):
        home = rugby.data.Team(**session.query(Team).filter_by(id=self.home).one().to_dict())
        away = rugby.data.Team(**session.query(Team).filter_by(id=self.away).one().to_dict())
        if self.home_score:
            home=dict(score=self.home_score, team=home)
            away=dict(score=self.away_score, team=away)
        else:
            home=dict(team=home, score=float('nan'))
            away=dict(team=away, score=float('nan'))
        return dict(date=self.date, 
                    season=self.season,
                    stadium=None,
                    home=home, 
                    away=away)


class Player(Base):
    __tablename__ = 'player'
    id = Column(Integer, primary_key=True)
    firstname = Column(String(250), nullable=False)
    surname = Column(String(250), nullable=False)
    country = Column(String(250), nullable=True)
    @classmethod
    def all(cls, session=session):
        return session.query(cls).all()
    @classmethod
    def get(cls, id):
        try:
            return session.query(cls).filter_by(id=id).one()
        except NoResultFound:
            return None

    @property
    def name(self):
        return f"{self.firstname} {self.surname}"
        
    @classmethod
    def from_query(cls, firstname, surname, session=session):
        return session.query(cls).filter_by(firstname=firstname, surname=surname).one()
    
    @classmethod
    def add(self, firstname, surname, country=None,  session=session):
        try:
            player = session.query(Player).filter_by(firstname=firstname, surname=surname).one()
        except NoResultFound:
            player = Player(firstname=firstname, surname=surname, country=country)
            session.add(player)
            session.commit()
        return player

class Position(Base):
    __tablename__ = 'position'
    id = Column(Integer, primary_key=True)
    match = Column(Integer, ForeignKey("match.id"))
    team = Column(Integer, ForeignKey("team.id"))
    player = Column(Integer, ForeignKey("player.id"), nullable=False)
    number = Column(Integer)
    on = Column(String(250))
    off = Column(String(250))
    reds = Column(String(250))
    yellows = Column(String(250))

    @classmethod
    def from_query(cls, home, away, date, session=session):
        home = Team.from_query(home.replace("_", " "), session).id
        away = Team.from_query(away.replace("_", " "), session).id
        date = datetime.strptime(date, "%Y-%m-%d")
        
        match = session.query(Match).filter(Match.date.between(date, date+timedelta(days=1))).filter_by(home=home, away=away).one()
        positions = session.query(cls).filter_by(match=match.id).all()

        out = []
        for position in positions:
            try:
                on = position.on.split(",")
                if on[0] != '':
                    on = list(map(float, on))
                else:
                    on = None
            except:
                on = position.on

            try:
                off = position.off.split(",")
                if off[0] != '':
                    off = list(map(float, off))
                elif on != None:
                    off = [80]
                else:
                    off = None
            except:
                if on:
                    off = [80]
                else:
                    off = position.off
                
            out.append({
                "number": position.number,
                "player": Player.get(position.player),
                "on": on,
                "off": off,
                "team": position.team
                })
        
        return out
    
    @classmethod
    def all(cls, session=session):
        return session.query(cls).all()
    
    @classmethod
    def get(cls, id):
        try:
            return session.query(cls).filter_by(id=id).one()
        except NoResultFound:
            return None
    
    @classmethod
    def add(cls, match, player, team, number, on, off, reds, yellows, session=session):
        firstname = player.split()[0]
        surname = " ".join(player.split()[1:])
        player = Player.from_query(firstname=firstname, surname=surname, session=session)
        team = Team.from_query(shortname=team, session=session)
        try:
            
            position = session.query(cls).filter_by(match=match, team=team.id, player=player.id, number=number).one()
        except NoResultFound:
            position = cls(match=match, team=team.id, player=player.id, number=number, on=on, off=off, reds=reds, yellows=yellows)
            session.add(position)
            session.commit()
        return position
