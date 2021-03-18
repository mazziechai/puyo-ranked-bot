import discord
from discord.ext import commands

from core import utils
from core.database import database

class Leaderboard(commands.Cog):
	def __init__(self, bot):
		self.bot = bot

	async def get_player_name(self, player_row):
		if player_row["display_name"] is not None:
			return player_row["display_name"]
		user = await utils.get_member(player_row["id"])
		return "[No name.]" if user is None else user.display_name
	
	@commands.command(
		name="leaderboard",
		help="See the current top players in the system."
	)
	async def leaderboard(self, ctx):
		players = database.execute(
			"SELECT id, display_name, rating_mu, rating_phi "
			"FROM players WHERE platforms <> '' AND rating_phi < 150 "
			"ORDER BY rating_mu DESC, rating_phi ASC LIMIT 10"
		).fetchall()
		if len(players) == 0:
			await ctx.send("There are no players with ranks at the moment, so no leaders to display.")
			return

		index = 0
		message = "**Top Puyo players**"
		for player in players:
			index += 1
			message += (
				"\n" + str(index) + ". " +
				utils.escape_markdown(await self.get_player_name(player)) +
				" | " + str(int(player["rating_mu"])) + " \u00B1 " + str(int(2 * player["rating_phi"]))
			)
		await ctx.send(message)

	@leaderboard.error
	async def leaderboard_OnError(self, ctx, error):
		if isinstance(error, commands.CheckFailure):
			return
		await utils.handle_command_error(ctx, error)

def setup(bot):
	bot.add_cog(Leaderboard(bot))
