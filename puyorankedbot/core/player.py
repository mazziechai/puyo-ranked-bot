import os
import pickle
import traceback
from datetime import datetime

import discord

from puyorankedbot.core.glicko2.glicko2 import Rating


class Player:
	def __init__(self, user, display_name, platform):
		self.id = user.id
		self.name = user.name
		self.discriminator = user.discriminator
		self.display_name = display_name
		self.platform = [platform]
		self.rating = Rating()
		self.time_of_registration = datetime.now()
		self.match_count = 0

	def get_username(self):
		return "{self.name}#{self.discriminator}".format(self=self)


def get_player(id):
	with open(os.path.join(os.path.dirname(__file__), "../players/{}".format(str(id))), "rb") as file:
		player_file = pickle.load(file)
		return player_file


def update_player(player):
	with open(os.path.join(os.path.dirname(__file__), "../players/{}".format(str(player.id))), "wb") as file:
		pickle.dump(player, file)
