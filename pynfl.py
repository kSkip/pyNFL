#pyNFL
#Copyright (c) 2015, Kane Scipioni
#All rights reserved.
#
#Redistribution and use in source and binary forms, with or without modification, are permitted provided that the following conditions are met:
#
#1. Redistributions of source code must retain the above copyright notice, this list of conditions and the following disclaimer.
#
#2. Redistributions in binary form must reproduce the above copyright notice, this list of conditions and the following disclaimer in the documentation and/or other materials provided with the distribution.
#
#3. Neither the name of the copyright holder nor the names of its contributors may be used to endorse or promote products derived from this software without specific prior written permission.
#
#THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

import requests
import re
import xml.etree.ElementTree as ET
import pandas as pd
import sqlite3

def get_player_position_team(pos_team):
    '''
    Takes the string containing the player's position and team
    Returns the position and team seperately

    Parameters
    ----------
    pos_team: a string

    Returns
    -------
    a tuple
    '''

    pos_team_list = pos_team.split(" - ")

    if len(pos_team_list) < 2:

        pos_team_list.append('Free')

    return pos_team_list[0].strip(), pos_team_list[1].strip()

def isfloat(value):
    '''
    Takes a variable and returns True if it's a float
    and returns False if it's not

    Parameters
    ----------
    value: a variable

    Returns
    -------
    a boolean
    '''

    try:
        
        float(value)
        return True

    except ValueError:

        return False

def get_stat_value(stat):
    '''
    Takes a string containing the stat
    Returns the numerical value associated with stat

    Parameters
    ----------
    stat: a string

    Returns
    -------
    a float
    '''

    if isfloat(stat):

        return float(stat)

    else:

        return float(0.0)

def get_player_data(player_xml_data):
    '''
    Takes the xml element whose children contain the player's stats
    Returns the dictionary of the player's stats

    Parameters
    ----------
    player_xml_data: xml element

    Returns
    -------
    a dict
    '''

    player_data = dict()

    player_data['name'] = player_xml_data[1][0][1].text

    position, team = get_player_position_team(player_xml_data[1][0][2].text)

    player_data['position'] = position
    player_data['team']     = team

    player_data['opponent'] = player_xml_data[2].text

    #take the text from these tags and convert to numerical values
    player_data['yds_passing']   = get_stat_value(player_xml_data[4][0].text)
    player_data['td_passing']    = get_stat_value(player_xml_data[5][0].text)
    player_data['int_passing']   = get_stat_value(player_xml_data[6][0].text)
    player_data['yds_rushing']   = get_stat_value(player_xml_data[7][0].text)
    player_data['td_rushing']    = get_stat_value(player_xml_data[8][0].text)
    player_data['yds_receiving'] = get_stat_value(player_xml_data[9][0].text)
    player_data['td_receiving']  = get_stat_value(player_xml_data[10][0].text)
    player_data['yds_return']    = get_stat_value(player_xml_data[11][0].text)
    player_data['td_return']     = get_stat_value(player_xml_data[12][0].text)
    player_data['fumtd_misc']    = get_stat_value(player_xml_data[13][0].text)
    player_data['two_pt_misc']   = get_stat_value(player_xml_data[14][0].text)
    player_data['lost_fum']      = get_stat_value(player_xml_data[15][0].text)
    player_data['fantasy_pts']   = get_stat_value(player_xml_data[16][0].text)

    return player_data

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

    login_url = 'https://id2.s.nfl.com/fans/login?'

    payload = {'action':'/fans/login','username':login_details['username'],'password':login_details['password']}

    login_req = requests.post(login_url,params=payload)

    url = 'http://fantasy.nfl.com/league/{0}/players?offset={1}&playerStatus=all&position=0&statCategory=stats&statSeason={2:4d}&statType=weekStats&statWeek={3:2d}'

    players = list()

    year = begin_week[0]
    week = begin_week[1]
    
    while year <= end_week[0]:

        while week <= season_weeks:

            offset = 0

            print("pulling week: ",week," season: ",year)
            
            #the page will only show 25 players at a time so we need to loop until we get all the players
            while 1:

                page = requests.get(url.format(login_details['league-id'],offset,year,week),cookies=login_req.cookies)

                results = re.search(r'<table.*>(.*)</table>',re.sub('\n','',page.text))

                if results:

                    xml_text = re.sub(r'&', '&amp;',results.group(0))

                    parser = ET.XMLParser(encoding='utf-8')
                    #parser._parser.UseForeignDTD(True)
                    parser.entity['nbsp'] = ''
                    tree = ET.fromstring(xml_text, parser=parser)

                    #append each player dictionary to "players"
                    for player in tree[1].findall('tr'):

                        player_data = get_player_data(player)

                        player_data['year'] = year
                        player_data['week'] = week

                        players.append(player_data)

                    offset = offset + 25

                else:

                    break
                    
            if year == end_week[0] and week == end_week[1]:
                break;
            else:
                week = week + 1
                
        year = year + 1
        week = 1

    return pd.DataFrame(players).drop_duplicates()

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
    
    conn = sqlite3.connect(database)
    c = conn.cursor()

    query = 'SELECT MAX(year) FROM {0}'
    c.execute(query.format(table))
    year = c.fetchall()[0][0]

    query = 'SELECT MAX(week) FROM {0} WHERE year = {1:4d}'
    c.execute(query.format(table,year))
    week = c.fetchall()[0][0];
    
    conn.close()
    
    return year, week

def get_matchup_data(matchup_data):
    '''
    Takes a list of strings containing the 
    desired matchup data and returns a 
    dictionary of the data

    Parameters
    ----------
    matchup_data: a list

    Returns
    -------
    a dict
    '''
    
    matchup = dict()
    
    matchup['team-1']   = matchup_data[0]
    matchup['owner-1']  = matchup_data[1]
    
    #win/loss/tie record
    record = matchup_data[2].split('-')
    
    matchup['wins-1']   = record[0]
    matchup['losses-1'] = record[1]
    matchup['ties-1']   = record[2]
    
    matchup['rank-1']      = int(matchup_data[3])
    matchup['streak-1']    = matchup_data[4]
    matchup['waiver-1']    = int(matchup_data[5])
    matchup['fantasy_pts-1'] = float(matchup_data[6])
                                   
    matchup['team-2']   = matchup_data[7]
    matchup['owner-2']  = matchup_data[8]
    
    #win/loss/tie record
    record = matchup_data[9].split('-')
    
    matchup['wins-2']   = record[0]
    matchup['losses-2'] = record[1]
    matchup['ties-2']   = record[2]
    
    matchup['rank-2']      = int(matchup_data[10])
    matchup['streak-2']    = matchup_data[11]
    matchup['waiver-2']    = int(matchup_data[12])
    matchup['fantasy_pts-2'] = float(matchup_data[13])
    
    return matchup

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
    
    login_url = 'https://id2.s.nfl.com/fans/login?'
    
    payload = {'action':'/fans/login','username':login_details['username'],'password':login_details['password']}

    login_req = requests.post(login_url,params=payload)

    url = 'http://fantasy.nfl.com/league/{0}/history/{1}/schedule?leagueId={0}&scheduleDetail={2}&scheduleType=week&standingsTab=schedule'
    
    matchups = list()
    
    year = begin_week[0]
    week = begin_week[1]

    while year <= end_week[0]:

        while week <= season_weeks:

            page = requests.get(url.format(login_details['league-id'],year,week),cookies=login_req.cookies)

            results = re.search(r'<li class="matchup[^>]*">(.*)</li>',page.text)

            #removing the unwanted text from the first regex match
            trimmed = re.sub(r'<[^<>]*>','\n',results.group(1))
            trimmed = re.sub(r'Waiver:','',trimmed)
            trimmed = re.sub(r'Streak:','',trimmed)
            trimmed = re.sub(r'View Game Center','',trimmed)
            trimmed = re.sub(r'[,\(\)]','',trimmed)

            #this loop cleans up the string so that all data is separated by newlines
            stripped = ""
            for l in trimmed.split("\n"):
                if l.strip() != '':
                    stripped += l + "\n"

            #split at the newlines
            data = stripped.strip().split("\n")

            #append this set of matchups to the list of dictionaries
            for i in range(0,len(data),14):

                matchup = get_matchup_data(data[i:i+14])
                
                matchup['year'] = year
                matchup['week'] = week
                
                matchups.append(matchup)
                
            if year == end_week[0] and week == end_week[1]:
                break;
            else:
                week = week + 1
                
        year = year + 1
        week = 1
        
        return pd.DataFrame(matchups)
