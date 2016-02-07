# pyNFL
pyNFL is a python library for scraping nfl.com for player and fantasy league statistics. It consists of only three functions that should be called directly by the user. Their descriptions are below. The basic function of the library is to take login credentials for a user's nfl.com fantasy football league profile, download certain poages that contain either player or league matchup data, and then parse it to construct a Pandas DataFrame object out of the result. Included is an [IPython notebook](./pyNFL-demo.ipynb) demostrating the use of the data scraped from the site. Also, included is a SQLite3 database already populated with NFL players' statistics from the 2010 to 2015 seasons.

##Functions descriptions
```python
def pull_players_data(begin_week,end_week,season_weeks,login_details):  
'''
Takes year/week range of desired stats, the number of weeks in season, and login details  
Returns all the nfl players stats for these time periods  

Parameters  
----------  
begin_week: a tuple  
end_week: a tuple  
season_weeks: an integer  
login_details: a dictionary  

Returns  
-------  
a Pandas DataFrame  
'''
```
```python
def get_last_week(database,table):
'''
Takes the name of database and table where
to pull the most recent record and returns the year and week

Parameters
----------
database: a string
table: a string

Returns
-------
a tuple
'''
```
```python
def pull_league_data(begin_week,end_week,season_weeks,login_details):
'''
Takes year/week range of desired stats, the number of weeks in season, and login details
Returns all the fantasy league's matchup stats for these time periods

Parameters
----------
begin_week: a tuple
end_week: a tuple
season_weeks: an integer
login_details: a dictionary

Returns
-------
a Pandas DataFrame
'''
```
