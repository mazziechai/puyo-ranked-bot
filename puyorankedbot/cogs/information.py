import discord
from discord.ext import commands

from core import utils
from core.database import database


class Information(commands.Cog):
	"""
	Cog for printing information about various things, such as Players and Matches.
	"""

	def __init__(self, bot):
		self.bot = bot

	@classmethod
	async def send_player_info(cls, ctx, player, user=None):
		"""
		Constructs an embed containing the player info and then sends it as response
		to the info command.
		:param ctx: Context to send to.
		:param player: The player database row object.
		:param user: The Discord user object.
		"""

		embed = discord.Embed(
			type="rich",
			title="_Puyo training grounds_ player info",
			description=
			("" if user is None else f"{user.name}#{user.discriminator}")
			+ f"\nID {player['id']}",
			colour=0x22FF7D  # TODO Maybe change this color depending on the rating.
		)
		embed.set_author(name=player["display_name"] or ("[No name.]" if user is None else user.display_name))
		if user is not None:
			embed.set_thumbnail(url=str(user.avatar_url))
		embed.set_footer(text="Registration date")
		embed.timestamp = player["registration_date"]
		embed.add_field(
			name="Platforms",
			value="\n".join([
				utils.format_platform_name(platform) +
				(
					""
					if player["username_" + platform] is None
					else utils.escape_markdown(f" ({player['username_' + platform]})")
				)
				for platform in player["platforms"].split()
			]),
			inline=False
		)
		embed.add_field(name="Rating", value=f"{int(player['rating_mu'])} \u00B1 {int(2 * player['rating_phi'])}")
		# Why double the phi? Because phi is just half of the distance to the boundary of the 95% confidence
		# interval. Source: https://www.glicko.net/glicko/glicko2.pdf (lines 7 to 11).
		embed.add_field(
			name="Matches",
			value=database.execute(
				"SELECT COUNT(*) FROM matches WHERE player1=:id OR player2=:id",
				{"id": player["id"]}
			).fetchone()[0]
		)
		await ctx.send(embed=embed)

	# Groupings, these don't do anything on their own.
	@commands.group(name="info", help="Retrieve information about players and matches.")
	async def info(self, ctx):
		if ctx.invoked_subcommand is None:
			await ctx.send(f"Usage: {self.bot.command_prefix}info (player | match) ...")

	@info.error
	async def info_OnError(self, ctx, error):
		await utils.handle_command_error(ctx, error)

	@info.group(name="player", help="Retrieve information about a Puyo player.")
	async def info_player(self, ctx):
		if ctx.invoked_subcommand is None:
			await ctx.send(f"Usage: {self.bot.command_prefix}info player (user | name) <user or name>")

	@info_player.command(
		name="user",
		usage="<mention or ID>",
		help="Retrieve information about a Puyo player using their Discord user."
	)
	async def info_player_user(self, ctx, user: discord.User):
		"""
		Gets a Player's information from a discord.User. This is done by getting
		the ID of the User and passing it to
		get_player().
		:param ctx: Context, comes with every command
		:param user: A user, which could be a mention, an ID, or anything else Discord can translate into a user.
		"""

		player = database.execute(
			"SELECT * FROM players WHERE id=? AND platforms <> ''",
			(user.id,)
		).fetchone()
		if player is None:
			await ctx.send(f"The user \"{utils.escape_markdown(user.display_name)}\" isn't registered.")
			return
		await self.send_player_info(ctx, player, user)

	@info_player_user.error
	async def info_player_user_OnError(self, ctx, error):
		if isinstance(error, commands.MissingRequiredArgument):
			await ctx.send(f"Usage: {self.bot.command_prefix}info player user <mention or ID>")
			return
		if isinstance(error, commands.errors.UserNotFound):
			await ctx.send(f"Failed to find Discord user based on input `{error.argument}`.")
			return
		await utils.handle_command_error(ctx, error)

	@info_player.command(
		name="name",
		usage="<display name>",
		help="Retrieve information about a Puyo player based on their display name."
	)
	async def info_player_name(self, ctx, *name):
		"""
		Gets a Player's information from a string. This is done by passing the name to spreadsheets.find_player_id(name)
		:param ctx: Context, comes with every command
		:param name: String
		"""
		name = " ".join(name).strip()
		player = database.execute(
			"SELECT * FROM players WHERE display_name=? AND platforms <> ''",
			(name,)
		).fetchone()
		if player is None:
			await ctx.send(
				"There is no registered player with the display name "
				f"\"{utils.escape_markdown(name)}\"."
			)
			return
		user = None
		try:
			user = await self.bot.fetch_user(player["id"])
		except discord.NotFound:
			pass
		await self.send_player_info(ctx, player, user)

	@info_player_name.error
	async def info_player_name_OnError(self, ctx, error):
		if isinstance(error, commands.MissingRequiredArgument):
			await ctx.send(f"Usage: {self.bot.command_prefix}info player name <display name>")
			return
		await utils.handle_command_error(ctx, error)


def setup(bot):
	bot.add_cog(Information(bot))
