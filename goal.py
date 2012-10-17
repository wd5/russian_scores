#!/usr/bin/env python
#-*- coding:utf-8 -*-

import bitly

import settings


class Goal(object):
    def __init__(self, goal_node, player_obj):
        self.player = player_obj
        self.home_team_ab = goal_node.find("home-team").find("team-abbreviation").text
        self.away_team_ab = goal_node.find("away-team").find("team-abbreviation").text
        self.event_id = goal_node.find("event-id").text
        vs_side = 'away-team' if self.player.team_ab == self.home_team_ab else 'home-team'
        vs_team_city = goal_node.find(vs_side).find("city").text
        vs_team_name = goal_node.find(vs_side).find("name").text
        self.vs_team = "%s %s" % (vs_team_city, vs_team_name)
        self.goal_date_raw = goal_node.find("game-date").text
        self.goal_date = '.'.join(self.goal_date_raw.split("/")[1::-1])  # 12/31/2012 -> 31.12;

    def get_text(self):
        goal_dict = {'goal_date': self.goal_date,
                     'player_name': self.player.player_name_ru,
                     'player_team': self.player.team_ab,
                     'vs_team': self.vs_team}
        return "%(goal_date)s %(player_name)s (%(player_team)s) " \
               "забил в матче против %(vs_team)s" % goal_dict

    def get_twitter_text(self):
        return "%s %s" % (self.get_text(), self.get_video_url())

    def get_video_url(self):
        video_url_template = "http://video.nhl.com/videocenter/console?hlp=%s&event=%s"
        bitly_api = bitly.Api(login=settings.BITLY_LOGIN, apikey=settings.BITLY_API_KEY)
        video_url =  video_url_template % (self.player.id, self.event_id)
        return bitly_api.shorten(video_url)