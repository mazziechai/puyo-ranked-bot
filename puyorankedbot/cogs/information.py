import discord
from discord.ext import commands

from puyorankedbot.core import spreadsheets
from puyorankedbot.core.player import get_player


class Information(commands.Cog):
	"""
	Cog for printing information about various things, such as Players and Matches.
	"""

	def __init__(self, bot):
		self.bot = bot

	@commands.group(name="info")
	async def info(self, ctx):
		if ctx.invoked_subcommand is None:
			await ctx.send("You must specify a `player` or `match` to receive information about.")

	@info.group(name="player")
	async def player(self, ctx):
		if ctx.invoked_subcommand is None:
			await ctx.send("You must specify either `user` or `name` to tell me how to find the player.")

	@player.command(name="user")
	async def id(self, ctx, user: discord.User):
		try:
			player = get_player(user.id)
		except FileNotFoundError:
			await ctx.send("Could not find that player!")
			return
		await ctx.send("Player information:\n"
					   "```Registration date: {player.time_of_registration}\n"
					   "ID: {player.id}\n"
					   "Username: {}\n"
					   "Display Name: {player.display_name}\n"
					   "Platform(s): {player.platform}\n"
					   "Rating: {player.rating.mu}\n"
					   "Rating Deviation: {player.rating.phi}\n"
					   "Match count: {player.match_count}```"
					   .format(player.get_username(), player=player)
					   )

	@player.command(name="name")
	async def name(self, ctx, *, name):
		player_id = spreadsheets.find_player_id(name)
		if player_id is not None:
			player = get_player(player_id)
			await ctx.send("Player information:\n"
						   "```Registration date: {player.time_of_registration}\n"
						   "ID: {player.id}\n"
						   "Username: {}\n"
						   "Display Name: {player.display_name}\n"
						   "Platform(s): {player.platform}\n"
						   "Rating: {player.rating.mu}\n"
						   "Rating Deviation: {player.rating.phi}\n"
						   "Match count: {player.match_count}```"
						   .format(player.get_username(), player=player)
						   )
		else:
			await ctx.send("Could not find that player!")


def setup(bot):
	bot.add_cog(Information(bot))
