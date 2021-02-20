import os
import pickle
from datetime import datetime

from puyorankedbot import config


class ScoresEqualError(Exception):
	pass


class MatchHistory:
	def __init__(self):
		self.match_count = 0
		self.matches = []

	def add_match(self, match):
		self.matches.append(match)
		with open("..{0}matches{0}match_history".format(os.sep), "wb") as file_obj:
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

	def __init__(self, player1, player2, player1_score, player2_score):
		self.id = config.get_config("match_count")
		self.player1 = player1
		self.player2 = player2
		self.player1_score = player1_score
		self.player2_score = player2_score

		if player1_score > player2_score:
			self.winner = self.player1
			self.loser = self.player2
		elif player2_score > player1_score:
			self.winner = self.player2
			self.loser = self.player1
		else:
			raise ScoresEqualError("The scores are equal.")

		self.time_of_match = datetime.now()

		match_history = get_match_history()
		match_history.add_match(self)

	def __str__(self):
		return "{self.time}, {self.match_id}: {self.player1} {self.score1} - {self.score2} {self.player2}" \
			.format(self=self)


def increment_match_count():
	match_count = config.get_config("match_count")
	config.set_config("match_count", match_count + 1)
	return match_count + 1


def get_match_history():
	if os.path.exists("..{0}matches{0}match_history".format(os.sep)):
		with open("..{0}matches{0}match_history".format(os.sep), "rb") as file_obj:
			return pickle.load(file_obj)
	else:
		match_history = MatchHistory()
		with open("..{0}matches{0}match_history".format(os.sep), "wb") as file_obj:
			pickle.dump(match_history, file_obj)
		return match_history
