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
		try:
			return (await self.bot.fetch_user(player_row["id"])).display_name
		except discord.NotFound:
			return "[No name.]"
	
	@commands.command(
		name="leaderboard",
		help="See the current top players in the system."
	)
	async def leaderboard(self, ctx):
		players = database.execute(
			"SELECT id, display_name, rating_mu, rating_phi "
			"FROM players WHERE platforms <> '' AND rating_phi < 150 "
			"ORDER BY rating_mu DESC, rating_phi DESC LIMIT 10"
		).fetchall()
		if len(players) == 0:
			await ctx.send("There are no players with ranks at the moment, so no leaders to display.")
			return

		index = 0
		lines = []
		for player in players:
			index += 1
			lines.append(
				str(index) + ". " +
				utils.escape_markdown(await self.get_player_name(player)) +
				" | " + str(int(player["rating_mu"])) + " \u00B1 " + str(int(2 * player["rating_phi"]))
			)
		await ctx.send("**Top Puyo players**\n" + "\n".join(lines))

	@leaderboard.error
	async def leaderboard_OnError(self, ctx, error):
		await utils.handle_command_error(ctx, error)

def setup(bot):
	bot.add_cog(Leaderboard(bot))