#!/usr/bin/env python
#-*- coding:utf-8 -*-


class Player(object):
    def __init__(self, player_node, player_name_ru, player_id):
        self.id = player_id
        self.aka_name = player_node.find("aka-name").text
        self.team = player_node.find("current-team")
        if self.team:
            self.team_city = self.team.find("city").text
            self.team_name = self.team.find("name").text
            self.full_team = self.team_city + self.team_name
            self.team_ab = self.team.find("team-abbreviation").text
        else:
            return
        self.goals = player_node.find("goals")
        self.player_name_ru = player_name_ru.encode('utf-8') if player_name_ru else self.aka_name

