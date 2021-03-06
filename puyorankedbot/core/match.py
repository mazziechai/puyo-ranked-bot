import os
import pickle
from datetime import datetime

import config
from .glicko2.glicko2 import Glicko2
from .player import update_player


class ScoresEqualError(Exception):
	pass


class MatchHistory:
	"""
	Class for managing the Match History.
	This class stores the match count as an integer and the matches as a dictionary.
	It also implements methods to do various things to matches with itself.
	"""
	def __init__(self):
		self.match_count = 0
		self.matches = {}

	def add_match(self, match):
		"""
		Adds a match to the MatchHistory
		:param match: Any, but preferably Match
		:return: None
		"""
		self.matches.update({self.match_count: match})
		with open(os.path.join(os.path.dirname(__file__), "../matches/match_history"), "wb") as file_obj:
			pickle.dump(self, file_obj)
		self.match_count = increment_match_count()

	def fix_match(self, match_id):
		# TODO: Allow changing a match's variables after it has been saved into the match history from match ID.
		raise NotImplementedError("fix_match isn't implemented yet")

	def remove_match(self, match_id):
		# TODO: Allow removing a match from the match history from match ID.
		raise NotImplementedError("remove_match isn't implemented yet")


class Match:
	"""
	Stores information about a match done between two Players.
	"""

	def __init__(self, player1, player2, player1_score: int, player2_score: int):
		"""
		Creation of a Match.
		:param player1: Player object.
		:param player2: Player object.
		:param player1_score: int
		:param player2_score: int
		"""
		# Creation of the Glicko2 object, so we can later use one of its methods rate_1vs1().
		g2 = Glicko2()
		self.id = config.get_config("match_count")
		self.player1 = player1
		self.player2 = player2
		self.player1_score = player1_score
		self.player2_score = player2_score

		# Setting a winner and loser for reference purposes.
		if player1_score > player2_score:
			self.winner = self.player1
			self.loser = self.player2
		elif player2_score > player1_score:
			self.winner = self.player2
			self.loser = self.player1
		else:
			raise ScoresEqualError("The scores are equal.")

		# Rating the players and assigning them their new ratings, because rate_1vs1 returns the ratings as a tuple.
		ratings = g2.rate_1vs1(self.winner.rating, self.loser.rating)
		self.winner.rating = ratings[0]
		self.loser.rating = ratings[1]

		# Updating match count
		self.player1.match_count = self.player1.match_count + 1
		self.player2.match_count = self.player2.match_count + 1
		self.time_of_match = datetime.now()

		update_player(self.player1)
		update_player(self.player2)

		# Adding the match to the match history.
		match_history = get_match_history()
		match_history.add_match(self)

	def __str__(self):
		return "{self.time}, {self.match_id}: {self.player1} {self.score1} - {self.score2} {self.player2}" \
			.format(self=self)


def increment_match_count() -> int:
	"""
	This function gets the current match count and increments it.
	:return: int
	"""
	match_count = config.get_config("match_count")
	config.set_config("match_count", match_count + 1)
	return match_count + 1


def get_match_history() -> MatchHistory:
	if os.path.exists(os.path.join(os.path.dirname(__file__), "../matches/match_history")):
		with open(os.path.join(os.path.dirname(__file__), "../matches/match_history"), "rb") as file_obj:
			return pickle.load(file_obj)
	else:
		match_history = MatchHistory()
		with open(os.path.join(os.path.dirname(__file__), "../matches/match_history"), "wb") as file_obj:
			pickle.dump(match_history, file_obj)
		return match_history
