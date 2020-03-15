import requests
import bs4
from bs4 import BeautifulSoup
import dateparser
import yaml
import json

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

            matches_list.append(match_data)
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

            matches_list.append(match_data)
        return matches_list
    
    def to_json(self):
        """
        Produce a json string of fixtures and results.
        """
        output = []
        output += self.fixtures_list()
        output += self.results_list()
        
        return json.dumps(output, default=str, indent=3)
    
    def to_yaml(self):
        """
        Produce a yaml string of fixtures and results.
        """
        output = []
        output += self.fixtures_list()
        output += self.results_list()
        
        return yaml.dump(output, indent=3, default_flow_style=False)
