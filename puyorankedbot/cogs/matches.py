import discord
from discord.ext import commands
from datetime import datetime

from core import utils
from core.database import database
from core.glicko2 import glicko2
from core import match_message_helper
from core.match_manager import match_manager


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
			await ctx.send_help(self.match)

	@match.error
	async def match_OnError(self, ctx, error):
		await utils.handle_command_error(ctx, error)

	@match.command(
		name="report",
		usage="<your score> <opponent score>",
		help="Report your current match's result to the system."
	)
	async def match_report(self, ctx, score1s, score2s):
		if ctx.author.id not in match_manager.player_map:
			await ctx.send("You are not having a match pending.")
			return

		try:
			score1 = utils.parse_integer(score1s, True)
			score2 = utils.parse_integer(score2s, True)
		except Exception as e:
			await ctx.send(str(e))
			return
		if score1 == score2:
			await ctx.send("The scores are equal. There gotta be a winner.")

		data = match_manager.player_map[ctx.author.id]
		match = data[0]
		if data[1]:
			score1, score2 = score2, score1

		if max(score1, score2) != match.goal:
			await ctx.send(
				f"The match should be first to **{match.goal}** "
				"according to the current ratings of you and your opponent."
			)
			return

		match.player1_score = score1
		match.player2_score = score2

		if match.confirming_timestamp is None:
			match_manager.pending_matches.remove(match)
		else:
			match_manager.confirming_matches.remove(match)
		match_manager.confirming_matches.append(match)
		match.confirming_timestamp = datetime.now().timestamp()

		embed = discord.Embed(
			type="rich",
			title="Match waiting confirmation",
			color=0xE39A00
		)
		embed.add_field(
			name=await match_message_helper.get_player_name(match.player1_data),
			value=match.player1_score
		)
		embed.add_field(
			name=await match_message_helper.get_player_name(match.player2_data),
			value=match.player2_score
		)
		await ctx.send(
			"If the following scores don't look right, "
			f"<@!{match.player1}> and <@!{match.player2}> can resubmit "
			"within 3 minutes.",
			embed=embed
		)

	@match_report.error
	async def match_report_OnError(self, ctx, error):
		if isinstance(error, commands.MissingRequiredArgument):
			await ctx.send_help(self.match_report)
			return
		if isinstance(error, commands.errors.UserNotFound):
			await ctx.send(f"Failed to find Discord user based on input `{error.argument}`.")
			return
		await utils.handle_command_error(ctx, error)


def setup(bot):
	bot.add_cog(Matches(bot))
