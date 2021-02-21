from datetime import datetime

import gspread
from puyorankedbot import config
from puyorankedbot.core.match import Match
from puyorankedbot.core.player import Player

google_sheets = gspread.service_account(config.get_config("service_account_file"))
spreadsheet = google_sheets.open_by_key(config.get_config("spreadsheet_id"))
player_sheet = spreadsheet.worksheet("Players")
match_sheet = spreadsheet.worksheet("Matches")


class NotPlayerOrMatchError(Exception):
	pass


def new(obj):
	"""
	Writes a new Player or Match to the appropriate spreadsheet given a Player or Match.
	:param obj: A Player or Match
	:return: None
	"""
	if isinstance(obj, Player):
		player = obj
		player_sheet.append_row([str(player.time_of_registration), str(player.id), player.get_username(),
								 player.display_name, ', '.join(map(str, player.platform)), str(player.match_count),
								 str(player.rating.mu), str(player.rating.phi), str(player.rating.sigma)])
	elif isinstance(obj, Match):
		match = obj
		match_sheet.append_row([match.id, str(match.time_of_match), match.player1.name, match.player1_score,
								match.player2_score, match.player2.name, match.player1.rating.mu,
								match.player2.rating.mu])
	else:
		raise NotPlayerOrMatchError("obj was not a Player or Match.")


def update(obj):
	if isinstance(obj, Player):
		player = obj
		# this is inefficient and bad but i can't figure out a way to do it otherwise (batch_update doesn't seem to work)
		# TODO: Fix this
		cell = player_sheet.find(str(player.id))
		player_sheet.delete_row(cell.row)
		player_sheet.append_row([str(player.time_of_registration), str(player.id), player.get_username(),
								 player.display_name, ', '.join(map(str, player.platform)), str(player.match_count),
								 str(player.rating.mu), str(player.rating.phi), str(player.rating.sigma)])
	elif isinstance(obj, Match):
		# TODO: Allow updating of matches on the spreadsheet.
		raise NotImplementedError("Updating matches on the spreadsheet is not implemented yet.")
	else:
		raise NotPlayerOrMatchError("obj was not a Player or Match.")


def find_player_id(search_term):
	try:
		cell = player_sheet.find(search_term)
	except gspread.exceptions.CellNotFound:
		return
	new_cell = player_sheet.cell(cell.row, 2)
	return new_cell.value