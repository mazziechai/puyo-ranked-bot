import discord
from discord.ext import commands

from core import utils
from core.database import database
from core.glicko2 import glicko2


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
			await ctx.send(f"Usage: {self.bot.command_prefix}match report <opponent> <your score> <opponent score>")

	@match.error
	async def match_OnError(self, ctx, error):
		await utils.handle_command_error(ctx, error)

	async def get_player_name(self, player):
		if player["display_name"] is None:
			try:
				return (await self.bot.fetch_user(player["id"])).display_name
			except discord.NotFound:
				return "[No name.]"
		else:
			return player["display_name"]

	async def add_report_field(self, embed, player, score, old_mu, new_mu, new_phi):
		d = new_mu - old_mu
		embed.add_field(
			name=utils.escape_markdown(await self.get_player_name(player)),
			value=f"**{score}**\n{int(new_mu)} \u00B1 {int(2 * new_phi)}\n" +
				  ('+' if d >= 0 else '\u2013') + f" {int(abs(d))}"
		)

	@classmethod
	def get_player_by_ID(cls, id_in):
		return database.execute(
			"SELECT id, display_name, rating_mu, rating_phi, rating_sigma "
			"FROM players WHERE id=? AND platforms<>''",
			(id_in,)
		).fetchone()

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
		:param score1s: Score of player 1
		:param score2s: Score of player 2
		:return:
		"""
		if ctx.author.id == user.id:
			await ctx.send("You can't report a fight with yourself.")
			return
		player1 = self.get_player_by_ID(ctx.author.id)
		if player1 is None:
			await ctx.send("You are not registered yet.")
			return
		player2 = self.get_player_by_ID(user.id)
		if player2 is None:
			await ctx.send("The opponent user is not yet registered.")
			return

		try:
			score1 = utils.parse_integer(score1s, True)
			score2 = utils.parse_integer(score2s, True)
		except Exception as e:
			await ctx.send(str(e))
			return
		if score1 == score2:
			await ctx.send("The scores are equal. There gotta be a winner.")

		old_rating1 = glicko2.Rating(player1["rating_mu"], player1["rating_phi"], player1["rating_sigma"])
		old_rating2 = glicko2.Rating(player2["rating_mu"], player2["rating_phi"], player2["rating_sigma"])
		if score1 > score2:
			new_rating1, new_rating2 = glicko2.Glicko2().rate_1vs1(old_rating1, old_rating2)
		else:
			new_rating2, new_rating1 = glicko2.Glicko2().rate_1vs1(old_rating2, old_rating1)

		cursor = database.execute("""
			INSERT INTO matches (
				player1, player2, player1_score, player2_score,
				player1_old_mu, player1_old_phi, player1_old_sigma,
				player1_new_mu, player1_new_phi, player1_new_sigma,
				player2_old_mu, player2_old_phi, player2_old_sigma,
				player2_new_mu, player2_new_phi, player2_new_sigma
			) VALUES (
				?, ?, ?, ?,
				?, ?, ?,
				?, ?, ?,
				?, ?, ?,
				?, ?, ?
			)
		""", (
			player1["id"], player2["id"], score1, score2,
			old_rating1.mu, old_rating1.phi, old_rating1.sigma,
			new_rating1.mu, new_rating1.phi, new_rating1.sigma,
			old_rating2.mu, old_rating2.phi, old_rating2.sigma,
			new_rating2.mu, new_rating2.phi, new_rating2.sigma
		))
		database.commit()

		embed = discord.Embed(
			type="rich",
			title="Match recorded",
			color=0xFFBE37
		)
		await self.add_report_field(embed, player1, score1, old_rating1.mu, new_rating1.mu, new_rating1.phi)
		await self.add_report_field(embed, player2, score2, old_rating2.mu, new_rating2.mu, new_rating2.phi)
		embed.set_footer(text=f"Match ID: {cursor.lastrowid}")
		await ctx.send(embed=embed)

	@match_report.error
	async def match_report_OnError(self, ctx, error):
		if isinstance(error, commands.MissingRequiredArgument):
			await ctx.send(f"Usage: {self.bot.command_prefix}match report <opponent> <your score> <opponent score>")
			return
		if isinstance(error, commands.errors.UserNotFound):
			await ctx.send(f"Failed to find Discord user based on input `{error.argument}`.")
			return
		await utils.handle_command_error(ctx, error)


def setup(bot):
	bot.add_cog(Matches(bot))
