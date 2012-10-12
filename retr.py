#!/usr/bin/env python
#-*- coding:utf-8 -*-

import re
import random
import urllib2
import sqlite3
import datetime
import elementtree.ElementTree as ET

import bitly
import twitter

from settings import *



class Player(object):
    def __init__(self, player_node, player_name_ru):
        self.aka_name = player_node.find("aka-name").text
        self.team = player_node.find("current-team")
        if not self.team:
            return
        self.full_team = self.team.find("city").text + " " + self.team.find("name").text
        self.goals =  player_node.find("goals")
        self.team_ab = self.team.find("team-abbreviation").text
        self.player_name_ru = player_name_ru.encode('utf-8')
        
        
class Goal(object):
    def __init__(self, goal_node, player_obj):
        self.player = player_obj
        self.home_team_ab = goal_node.find("home-team").find("team-abbreviation").text
        self.away_team_ab = goal_node.find("away-team").find("team-abbreviation").text
        
        if (self.player.team_ab == self.home_team_ab):
            self.vs_team = goal_node.find("away-team").find("city").text + " " + goal_node.find("away-team").find("name").text
        else:
            self.vs_team = goal_node.find("home-team").find("city").text + " " + goal_node.find("home-team").find("name").text
                
        self.period = goal_node.find("period").text
        time = goal_node.find("time").text
        self.goal_date = goal_node.find("game-date").text                
        self.event_id = goal_node.find("event-id").text                
        period = self.period
        period_text = ""
        if period=='1':
            period_text = "в первом периоде " + time
        elif period=='2':
            period_text = "во втором периоде " + time
        elif period=='3':
            period_text = "в третем периоде " + time
        elif period=='4':
            period_text = "в овертайме " + time
        elif period=='5':                                    
            period_text = "буллит"
        self.period_text = period_text
        self.goal_date = self.goal_date.split("/")
        self.goal_date = self.goal_date[1]+"."+self.goal_date[0]#+"."+self.goal_date[2]        
        
    def get_text(self):
        print self.player.player_name_ru
        print self.goal_date
        print self.player.team_ab
        print self.vs_team.encode('utf-8', 'replace')
        txt = self.goal_date + " " + self.player.player_name_ru+"("+self.player.team_ab+") забил в матче против "+self.vs_team.encode('utf-8', 'replace')#+ " "+self.period_text
        return txt

def get_list_of_active_players():
    BEGIN = "<!-- player search -->"
    END = "<!-- end player search -->"
    url = "http://www.nhl.com/ice/playersearch.htm?season=20102011&bc=RUS"
    """http://www.nhl.com/ice/playersearch.htm?adv=true&position=&country=RUS&tm=&season=20102011"""

    html = urllib2.urlopen(url).read()
    
    active_players_table = html.partition(BEGIN)[2].partition(END)[0]    
    result = re.finditer('/ice/player.htm\?id=(\d*)', active_players_table)
    players = []
    for match in result:
        players.append(int(match.group(1)))
    return players

def update_players_db(players):
    rows = c.execute("""SELECT player_id, web_tracking_id FROM last_goal""")
    db_players = []
    for row in rows:
        db_players.append(row[0])
    #print db_players
    for player in set(players).difference(set(db_players)):
        c.execute("INSERT INTO last_goal VALUES (?, NULL);", (str(player),))
    conn.commit()
    return db_players
    
    
def process_player(player_id):
    URL = "http://video.nhl.com/videocenter/highlights?xml=2&id=" + str(player_id)
    q = "SELECT web_tracking_id, player_name FROM last_goal WHERE player_id="+ str(player_id)
    
    
    for i in c.execute(q):
        last_wtid = i[0]
        player_name_ru = i[1]

    player_node = ET.fromstring(urllib2.urlopen(URL).read())
    player_obj = Player(player_node, player_name_ru)

    if player_obj.team and player_obj.goals:
        to_add = []
        for goal in player_obj.goals:
            wtid = goal.find("web-tracking-id").text
            if wtid == last_wtid:
                break
            else:
                to_add.append(goal)

                        
        last_goal = player_obj.goals[0].find("web-tracking-id").text
        if not DEBUG:
            c.execute("UPDATE last_goal SET web_tracking_id=? WHERE player_id=?", (last_goal, player_id))          
        for goal in to_add:
            goal_obj = Goal(goal, player_obj)
            video_url = ("http://video.nhl.com/videocenter/console?hlp=%s&event=%s")\
                    %(player_id, goal_obj.event_id)
            short_video_url = bitly_api.shorten(video_url)              
            tw = goal_obj.get_text() + " " + short_video_url.encode("utf-8")
            print tw, len(tw)
            

            print short_video_url
            if not DEBUG:
                api.PostUpdate(tw[:140])
        conn.commit()

conn = sqlite3.connect(DATABASE_PATH)
c = conn.cursor()

players = get_list_of_active_players()
players_in_db = update_players_db(players)

bitly_api = bitly.Api(login=BITLY_LOGIN, apikey=BITLY_API_KEY) 
api = twitter.Api(consumer_key=TWITTER_CONSUMER_KEY, 
                  consumer_secret=TWITTER_CONSUMER_SECRET, 
                  access_token_key=TWITTER_ACCESS_TOKEN_KEY, 
                  access_token_secret=TWITTER_ACCESS_TOKEN_SECRET) 

for player_id in players_in_db:
    goals_to_add = process_player(player_id)

c.close()

