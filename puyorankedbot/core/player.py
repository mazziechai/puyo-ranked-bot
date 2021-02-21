import os
import pickle
from datetime import datetime


from puyorankedbot.core.glicko2.glicko2 import Rating


class Player:
	"""
	Class for storing player information.
	"""
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


class PlayerNotFoundError(Exception):
	pass


def get_player(id) -> Player:
	"""
	Gets the player from a file, unpickles it, and returns a Player.
	:param id: A valid Discord user ID.
	:return:
	"""
	try:
		with open(os.path.join(os.path.dirname(__file__), "../players/{}".format(str(id))), "rb") as file:
			player_file = pickle.load(file)
			return player_file
	except FileNotFoundError:
		raise PlayerNotFoundError("Could not get player")


def update_player(player: Player):
	"""
	A function to pickle a Player and write the pickled Player to the file system.
	:param player: Player
	:return: None
	"""
	with open(os.path.join(os.path.dirname(__file__), "../players/{}".format(str(player.id))), "wb") as file:
		pickle.dump(player, file)
