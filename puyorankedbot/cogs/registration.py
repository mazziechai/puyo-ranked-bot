import os
import traceback

from discord.ext import commands
from discord.ext.commands import Cog

from puyorankedbot import logger
from puyorankedbot.core import spreadsheets
from puyorankedbot.core.player import get_player, Player, update_player


class Registration(commands.Cog):
	"""
	Cog for registering and unregistering.
	"""

	def __init__(self, bot):
		self.bot = bot

	@commands.command(name="register")
	async def register(self, ctx, platform: str, *, display_name: str):
		"""
		Registers a new Player into the system.
		:param ctx: Context, comes with every command
		:param platform: "switch", "pc", or "ps4".
		:param display_name: The name the user wishes to sign up with.
		:return: None
		"""
		platforms = ["switch", "pc", "ps4"]

		if not platform.casefold() in platforms:
			raise commands.UserInputError("You need to provide a valid platform."
										  "The options are:\nSwitch, PC, PS4.")

		logger.log_info("Received valid registration command!")
		if os.path.exists(os.path.join(os.path.dirname(__file__), "../players/{}".format(str(ctx.author.id)))):
			logger.log_info("Found player file. Modifying it.")
			player_file = get_player(str(ctx.author.id))
			if platform.casefold() in player_file.platform:
				raise commands.UserInputError("You're already signed up for this platform.")
			else:
				player_file.platform.append(platform.casefold())
				update_player(player_file)
				spreadsheets.update(player_file)
				await ctx.send("Signed up for {0} too.".format(platform.capitalize()))
		else:
			logger.log_info("Could not find player file, creating a new one.")
			player = Player(ctx.author, display_name, platform)
			update_player(player)
			spreadsheets.new(player)
			if platform.casefold() == "switch":
				await ctx.send("Signed up for {0}.".format(platform.capitalize()))
			else:
				await ctx.send("Signed up for {0}.".format(platform.upper()))

	@register.error
	async def register_error(self, ctx, error):
		if isinstance(error, NotImplementedError):
			await ctx.send("You're attempting to access a command that isn't ready yet.")

		elif isinstance(error, commands.BadArgument):
			await ctx.send(error)

		else:
			await ctx.send(error)
			traceback.print_exc()

	@commands.command(name="unregister")
	async def unregister(self, ctx, platform):
		"""
		Unregisters a player by removing the requested platform from their file.
		:param ctx: Context, comes with every command
		:param platform: "switch", "pc", "ps4".
		:return: None
		"""
		platforms = ["switch", "pc", "ps4"]

		if not platform.casefold() in platforms:
			raise commands.UserInputError("You need to provide a valid platform."
										  "The options are:\nSwitch, PC, PS4.")

		if os.path.exists("players/" + str(ctx.message.author.id)):
			logger.log_info("Found player file, modifying it")
			player_file = get_player(ctx.message.author.id)
			player_file.platform.remove(platform.casefold())
			update_player(player_file)
			spreadsheets.update(player_file)
			if platform.casefold() == "switch":
				await ctx.send("Unregistered for {0}.".format(platform.capitalize()))
			else:
				await ctx.send("Unregistered for {0}.".format(platform.upper()))
		else:
			await ctx.send("It doesn't look like you've registered before!")


def setup(bot):
	bot.add_cog(Registration(bot))
