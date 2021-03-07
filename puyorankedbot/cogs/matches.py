import discord
from discord.ext import commands

from core import spreadsheets, utils
from core.match import Match
from core.player import get_player


class Matches(commands.Cog):
	"""
	Cog for adding, removing, and fixing matches in the system. Calculates rating.
	"""

	def __init__(self, bot):
		self.bot = bot

	@commands.group(
		name="match",
		help="Match related commands."
	)
	async def match(self, ctx):
		if ctx.invoked_subcommand is None:
			await ctx.send("Usage: ,match report <opponent> <your score> <opponent score>")

	@match.error
	async def match_OnError(cog, ctx, error):
		await utils.handle_command_error(ctx, error)

	@classmethod
	def add_report_field(cls, embed, old_mu, player, score):
		d = player.rating.mu - old_mu
		embed.add_field(
			name = player.display_name,
			value = f"**{score}**\n{int(player.rating.mu)} \u00B1 {int(player.rating.phi)}\n" +
				('+' if d >= 0 else '\u2013') +	f" {int(abs(d))}"
		)

	@match.command(
		name="report",
		usage="<opponent> <your score> <opponent score>",
		help="Report a match to the system."
	)
	async def match_report(self, ctx, user: discord.User, score1s, score2s):
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
		old_mu1 = player1.rating.mu
		old_mu2 = player2.rating.mu
		try:
			score1 = utils.parse_integer(score1s, True)
			score2 = utils.parse_integer(score2s, True)
		except Exception as e:
			await ctx.send(str(e))
			return

		match = Match(player1, player2, score1, score2)
		spreadsheets.new(match)

		embed = discord.Embed(
			type = "rich",
			title = "Match recorded",
			color = 0xFFBE37
		)
		self.add_report_field(embed, old_mu1, player1, score1)
		self.add_report_field(embed, old_mu2, player2, score2)
		await ctx.send(embed=embed)

	@match_report.error
	async def match_report_OnError(cog, ctx, error):
		if (isinstance(error, commands.MissingRequiredArgument)):
			await ctx.send("Usage: ,match report <opponent> <your score> <opponent score>")
			return
		if (isinstance(error, commands.errors.UserNotFound)):
			await ctx.send(f"Failed to find Discord user based on input `{error.argument}`.");
			return
		await utils.handle_command_error(ctx, error)


def setup(bot):
	bot.add_cog(Matches(bot))
