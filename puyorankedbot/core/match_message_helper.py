# This module contains common functions regarding match report
# messages used by cogs.matches and core.match_manager

from core import utils
from core.database import database

async def get_player_name(player):
	if player["display_name"] is None:
		user = await utils.get_member(player["id"])
		return "[No name.]" if user is None else user.display_name
	else:
		return player["display_name"]

async def add_report_field(embed, player, score, old_mu, old_phi, new_mu, new_phi):
	rating_change = int(new_mu) - int(old_mu)
	rating_change_sign = '+' if rating_change >= 0 else '\u2013'
	embed.add_field(
		name=utils.escape_markdown(await get_player_name(player)),
		value=(
			(f"**{score}**\n" if score is not None else "") +
			f"{int(new_mu)} \u00B1 {int(2 * new_phi)}\n"
			f"{rating_change_sign} {abs(rating_change)}\n" +
			utils.get_rank_with_comparison(old_mu, old_phi, new_mu, new_phi)
		)
	)

def get_player_by_ID(id_in):
	return database.execute(
		"SELECT id, display_name, rating_mu, rating_phi, rating_sigma "
		"FROM players WHERE id=? AND platforms<>''",
		(id_in,)
	).fetchone()
