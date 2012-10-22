#!/usr/bin/env python
#-*- coding:utf-8 -*-

import re
import random
import urllib2
import sqlite3
import datetime
import elementtree.ElementTree as ET
from itertools import takewhile

import bitly
import twitter

from player import Player
from goal import Goal


from settings import *

#api = twitter.Api(consumer_key=TWITTER_CONSUMER_KEY,
#                  consumer_secret=TWITTER_CONSUMER_SECRET,
#                  access_token_key=TWITTER_ACCESS_TOKEN_KEY,
#                  access_token_secret=TWITTER_ACCESS_TOKEN_SECRET)

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
    for player in set(players).difference(set(db_players)):
        c.execute("INSERT INTO last_goal VALUES (?, NULL);", (str(player),))
    conn.commit()
    return db_players
    
    
def process_player(player_data):
    player_id, player_name_ru, last_wtid = player_data
    URL = "http://video.nhl.com/videocenter/highlights?xml=2&id=%s" % player_id
    player_node = ET.fromstring(urllib2.urlopen(URL).read())
    player_obj = Player(player_node, player_name_ru, player_id)

    if player_obj.team and player_obj.goals:
        # take all goals since last update
        to_add = takewhile(lambda goal: not goal.find("web-tracking-id").text==last_wtid, player_obj.goals)
        if to_add:
            last_goal = player_obj.goals[0].find("web-tracking-id").text
            for goal in to_add:
                goal_obj = Goal(goal, player_obj)
                tw = goal_obj.get_twitter_text()
                return tw, player_id, last_goal

conn = sqlite3.connect(DATABASE_PATH)
c = conn.cursor()

#players = get_list_of_active_players() # brocken with new version of nhl site
#players_in_db = update_players_db([]) # moved to get_players_data

def get_players_data():
    c.execute("SELECT player_id, player_name, web_tracking_id FROM last_goal")
    return c.fetchall()

def after_retrieve_action(out_pdata):
    message, player_id, last_goal = out_pdata
    print message
    c.execute("UPDATE last_goal SET web_tracking_id=? WHERE player_id=?", (last_goal, player_id))

players_data = get_players_data()

for player_data in players_data:
    retrieve_out_data = process_player(player_data)
    if retrieve_out_data:
        after_retrieve_action(retrieve_out_data)
    conn.commit()

c.close()