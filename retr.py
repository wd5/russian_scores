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
    
    
def process_player(player_id):
    URL = "http://video.nhl.com/videocenter/highlights?xml=2&id=%s" % player_id
    GET_LAST_GOAL_QUERY = "SELECT web_tracking_id, player_name FROM last_goal WHERE player_id=?"

    c.execute(GET_LAST_GOAL_QUERY, (player_id,))
    last_wtid, player_name_ru = c.fetchone()
    player_node = ET.fromstring(urllib2.urlopen(URL).read())
    player_obj = Player(player_node, player_name_ru, player_id)

    print URL, player_name_ru

    if player_obj.team and player_obj.goals:
        # take all goals, before last goal on previous work
        to_add = takewhile(lambda goal: not goal.find("web-tracking-id").text==last_wtid, player_obj.goals)

        if to_add:
            last_goal = player_obj.goals[0].find("web-tracking-id").text
            c.execute("UPDATE last_goal SET web_tracking_id=? WHERE player_id=?", (last_goal, player_id))
            for goal in to_add:
                goal_obj = Goal(goal, player_obj)
                tw = goal_obj.get_twitter_text()
                print tw, len(tw)

            #if not DEBUG:
                #api.PostUpdate(tw[:140])
        conn.commit()

conn = sqlite3.connect(DATABASE_PATH)
c = conn.cursor()

players = get_list_of_active_players()
players_in_db = update_players_db(players)


#api = twitter.Api(consumer_key=TWITTER_CONSUMER_KEY,
#                  consumer_secret=TWITTER_CONSUMER_SECRET,
#                  access_token_key=TWITTER_ACCESS_TOKEN_KEY,
#                  access_token_secret=TWITTER_ACCESS_TOKEN_SECRET)

#for player_id in players_in_db:
#    goals_to_add = process_player(player_id)

process_player(8467496)

c.close()