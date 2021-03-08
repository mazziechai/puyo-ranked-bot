import discord
from discord.ext import commands
from discord.ext.commands import UserNotFound

from core import spreadsheets, utils
from core.player import get_player, PlayerNotFoundError


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
		:param player: The player object.
		:param user: The Discord user object.
		"""
		embed = discord.Embed(
			type="rich",
			title="_Puyo training grounds_ player info",
			description=f"{player.get_username()}\nID {player.id}",
			colour=0x22FF7D  # TODO Maybe change this color depending on the rating.
		)
		embed.set_author(name=player.display_name)
		if user is not None:
			embed.set_thumbnail(url=str(user.avatar_url))
		embed.set_footer(text="Registration date")
		embed.timestamp = player.time_of_registration
		embed.add_field(
			name="Platforms",
			value=", ".join([utils.format_platform_name(platform) for platform in player.platform])
		)
		embed.add_field(name="Rating", value=f"{int(player.rating.mu)} \u00B1 {int(player.rating.phi)}")
		embed.add_field(name="Matches", value=player.match_count)
		await ctx.send(embed=embed)

	# Groupings, these don't do anything on their own.
	@commands.group(name="info", help="Retrieve information about players and matches.")
	async def info(self, ctx):
		if ctx.invoked_subcommand is None:
			await ctx.send("Usage: ,info (player | match) ...")

	@info.error
	async def info_on_error(self, ctx, error):
		await utils.handle_command_error(ctx, error)

	@info.group(name="player", help="Retrieve information about a Puyo player.")
	async def info_player(self, ctx):
		if ctx.invoked_subcommand is None:
			await ctx.send("Usage: ,info player (user | name) <user or name>")

	@info_player.command(
		name="user",
		usage="<mention or ID>",
		help="Retrieve information about a Puyo player using their Discord user."
	)
	async def info_player_user(self, ctx, user: discord.User):
		"""
		Gets a Player's information from a discord.User. This is done by getting the ID of the User and passing it to
		get_player().
		:param ctx: Context, comes with every command
		:param user: A user, which could be a mention, an ID, or anything else Discord can translate into a user.
		"""

		try:
			player = get_player(user.id)
		except PlayerNotFoundError:
			await ctx.send(f"The user \"{user.display_name}\" isn't registered.")
			return
		await self.send_player_info(ctx, player, user)

	@info_player_user.error
	async def info_player_user_on_error(self, ctx, error):
		if isinstance(error, commands.MissingRequiredArgument):
			await ctx.send("Usage: ,info player user <mention or ID>")
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
	async def info_player_name(self, ctx, *, name):
		"""
		Gets a Player's information from a string. This is done by passing the name to spreadsheets.find_player_id(name)
		:param ctx: Context, comes with every command
		:param name: String
		"""

		player_id = spreadsheets.find_player_id(name)
		if player_id is not None:
			player = get_player(player_id)
			user = None
			try:
				user = await self.bot.fetch_user(player_id)
			except UserNotFound:
				pass
			await self.send_player_info(ctx, player, user)
		else:
			await ctx.send(f"There is no registered player with the display name \"{name}\".")

	@info_player_name.error
	async def info_player_name_on_error(self, ctx, error):
		if isinstance(error, commands.MissingRequiredArgument):
			await ctx.send("Usage: ,info player name <display name>")
			return
		await utils.handle_command_error(ctx, error)


def setup(bot):
	bot.add_cog(Information(bot))
