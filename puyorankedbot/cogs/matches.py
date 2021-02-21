import discord
from discord.ext import commands

from puyorankedbot.core import spreadsheets
from puyorankedbot.core.match import Match
from puyorankedbot.core.player import get_player


class Matches(commands.Cog):
	"""
	Cog for adding, removing, and fixing matches in the system. Calculates rating.
	"""

	def __init__(self, bot):
		self.bot = bot

	@commands.group(name="match")
	async def match(self, ctx):
		if ctx.invoked_subcommand is None:
			await ctx.send("**Help for Match command:**\n"
						   "`,match report` Reports a match between the author and the tagged user with a score.\n"
						   "Example: `,match report @Juice 17 20`\n")

	@match.command(name="report")
	async def report(self, ctx, user: discord.User, score1: int, score2: int):
		"""
		Reports a match to the system, calculates the ratings, and sends them as a message.
		:param ctx: Context, comes with every command
		:param user: A user, which could be a mention, an ID, or anything else Discord can translate into a user.
		:param score1: int
		:param score2: int
		:return:
		"""
		player1 = get_player(ctx.author.id)
		player2 = get_player(user.id)

		match = Match(player1, player2, score1, score2)
		spreadsheets.new(match)
		await ctx.send("Match reported! New ratings: {0}, {1}".format(round(player1.rating.mu),
																	  round(player2.rating.mu)))


def setup(bot):
	bot.add_cog(Matches(bot))
