import discord
from discord.ext import commands
from datetime import datetime

from core import utils
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
		if isinstance(error, commands.CheckFailure):
			return
		await utils.handle_command_error(ctx, error)

	@match.command(
		name="report",
		usage="<your score> <opponent score>",
		help="Report your current match's result to the system."
	)
	async def match_report(self, ctx, score1s, score2s):
		if ctx.author.id not in match_manager.player_map:
			await ctx.send("You do not have a match pending.")
			return

		try:
			score1 = utils.parse_integer(score1s, True)
			score2 = utils.parse_integer(score2s, True)
		except Exception as e:
			await ctx.send(str(e))
			return
		if score1 == score2:
			await ctx.send("The scores are equal. There's gotta be a winner.")

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

		if (match.player1_score, match.player2_score) == (score1, score2):
			new_status = match.confirm_status | (1 if data[1] else 2)
			if new_status == match.confirm_status:
				await ctx.send("Nothing changed, the scores are still the same.")
				return
			else:
				match.confirm_status == new_status
				if new_status == 3:
					await match_manager.process_match_complete(match)
					match_manager.confirming_matches.remove(match)
		else:
			match.player1_score = score1
			match.player2_score = score2

			if match.confirming_timestamp is None:
				match_manager.pending_matches.remove(match)
			else:
				match_manager.confirming_matches.remove(match)
			match_manager.confirming_matches.append(match)
			match.confirming_timestamp = datetime.now().timestamp()
			match.confirm_status = 1 if data[1] else 2

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
				"within 3 minutes. "
				f"<@!{match.player1 if data[1] else match.player2}> "
				"can submit the same score to immediately confirm the match.",
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
	
	@match.command(
		name="cancel",
		help="Request cancelling the current match."
	)
	async def match_cancel(self, ctx):
		if ctx.author.id not in match_manager.player_map:
			await ctx.send("You do not have a match pending.")
			return
		data = match_manager.player_map[ctx.author.id]
		match = data[0]
		if match.confirming_timestamp is not None:
			await ctx.send("Cannot cancel the match since scores are already submitted.")
			return
		new_status = match.cancel_status | (1 if data[1] else 2)
		if new_status == match.cancel_status:
			await ctx.send("You have already requested cancelling the current match.")
			return
		else:
			if new_status == 3:
				await match_manager.cleanup_for_match(match)
				match_manager.pending_matches.remove(match)
				await ctx.send("The match has been cancelled.")
			else:
				match.cancel_status = new_status
				await ctx.send(
					f"<@!{ctx.author.id}> is requesting the match be cancelled. "
					f"<@!{match.player1 if data[1] else match.player2}> can use "
					f"`{utils.bot.command_prefix}match cancel` to confirm."
				)

	@match_cancel.error
	async def match_cancel_OnError(self, ctx, error):
		await utils.handle_command_error(ctx, error)


def setup(bot):
	bot.add_cog(Matches(bot))
