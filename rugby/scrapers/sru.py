import requests
import bs4
from bs4 import BeautifulSoup
import dateparser
import yaml
import json
import pandas as pd

from .data import Match, Tournament

class SRUResults():
    """
    A class to handle an SRU results page, and parse out the relevent parts.
    """
    
    def __init__(self, competition, season):
        """
        Create an SRU page parser.
        
        Parameters
        ----------
        competition: int
            The number of the competition from the SRU website URL
        """
        #if competition > 10000:

        self.url = "https://www.scottishrugby.org/fixtures-and-results/club-rugby/competition?comp={}_{}".format(competition, season)
        #else:
            #self.url = "http://www.scottishrugby.org/fixtures-and-results?competition={}".format(competition)
        r2 = requests.get(self.url)
        soup = BeautifulSoup(r2.text, 'html.parser')
        self.body = soup.find("main")

        self.league = self.body.find("h1").text
        self.season = season # competition.split("_")[1] #2000 + int(self.body.find("div", {"class": "fixtures-heading"}).find("h2").text.split(" ")[-1])
        
    def fixtures_list(self):
        """
        Generate the fixtures list for a given page.

        Parameters
        ----------
        body: `bs4.element.tag`
            The body element of the page.

        Returns
        -------
        list
            A list of fixtures in the format [date, home, away]
        """
        matches = self.body.find_all("div", {"id": "fixtures-list"})[0].find_all("div", {"class", "match_item"})
        matches_list = []
        for match in matches:
            match_data = {}
            match_data['home'] = match.find("span", {"class": "club-home"}).text
            match_data['away'] = match.find("span", {"class": "club-away"}).text
            match_data['status'] = match.find("span", {"class": "matches__status"}).text
            match_data['date'] = dateparser.parse(match.find_previous("div", {"class": "club-match-dates"}).text.strip())

            data = {"home": {"team": match_data["home"]}, 
                    "away": {"team": match_data["away"]},
                    "stadium": None,
                    "status": match_data["status"],
                    "date": match_data["date"]
            }
            
            matches_list.append(data)
        
        return matches_list
    
    def results_list(self):
        """
        Generate the results list for a given page.

        Parameters
        ----------
        body: `bs4.element.tag`
            The body element of the page.

        Returns
        -------
        list
            A list of fixtures in the format [date, home, away]
        """
        matches = self.body.find_all("div", {"id": "results-list"})[0].find_all("div", {"class", "match_item"})
        matches_list = []
        for match in matches:
            match_data = {}
            match_data['home'] = match.find("span", {"class": "club-home"}).text
            match_data['away'] = match.find("span", {"class": "club-away"}).text
            match_data['home_score'], match_data['away_score'] = match.find("span", {"class": "matches__status"}).text.split(" - ")
            match_data['date'] = dateparser.parse(match.find_previous("div", {"class": "club-match-dates"}).text.strip())

            data = {"home": {"score": match_data["home_score"], "team": match_data["home"]}, 
                    "away": {"score": match_data["away_score"], "team": match_data["away"]},
                    "stadium": None,
                    "date": match_data["date"]
            }
            
            matches_list.append(data)
        return matches_list
    
    def to_json(self, filename=None):
        """
        Produce a json string of fixtures and results.
        """
        output = Tournament(self.league, self.season, self.fixtures_list()+self.results_list())
        
        return output.to_json(filename)
