from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.ext.declarative import declarative_base

from sqlalchemy import create_engine
from sqlalchemy.orm.exc import NoResultFound

from sqlalchemy import or_

from datetime import datetime, timedelta

Base = declarative_base()

import rugby
from flask import url_for

engine = create_engine(f'sqlite:///{rugby.__path__[0]}/rugby.db')

Base.metadata.create_all(engine)

# from sqlalchemy.orm import sessionmaker
# DBSession = sessionmaker(bind=engine)
# session = DBSession()

from flask_sqlalchemy_session import current_session as session

import rugby.data


class Tournament(Base):
    __tablename__ = 'tournament'
    id = Column(Integer, primary_key=True)
    name = Column(String(250), nullable=False)

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
    def from_query(self, tournament, season, session=session):
        tournament = session.query(Tournament).filter_by(name=tournament).one()
        season = session.query(Season).filter_by(name=season, tournament=tournament.id).one()
        
        return rugby.data.Tournament(
                name=tournament.name,
                season=season.name, 
                matches=season.matches(session))
    
    def matches(self, session=session):
        matches = session.query(Match).filter_by(season=self.id).all()
        matches = [match.to_dict() for match in matches]
        return matches

class Team(Base):
    __tablename__ = "team"
    id = Column(Integer, primary_key=True)
    name = Column(String(250), nullable=False)
    shortname = Column(String(250), nullable=False)

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
                    colors={"primary": "#000000"},
                    country="None"                    
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
        return [rugby.data.Match(match.to_dict()).to_rest()
                for match in session.query(Match).all()]
    
    @classmethod
    def from_query(self, home, away, date=None, session=session):
        
        home = Team.from_query(home).id
        away = Team.from_query(away).id

        if date:
            date = datetime.strptime(date, "%Y-%m-%d")
        
            match = session.query(Match).filter(Match.date.between(date, date+timedelta(days=1))).filter_by(home=home, away=away).one()
            return rugby.data.Match(match.to_dict())

        else:
            matches = session.query(Match).filter(
                (Match.home.in_([home, away]) & (Match.away.in_([home, away]))))
            return [rugby.data.Match(match.to_dict()).to_rest() for match in matches]


    
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
        return dict(date=self.date, 
                    season=self.season,
                    stadium=None,
                    home=dict(score=self.home_score, team=home), 
                    away=dict(score=self.away_score, team=away))


