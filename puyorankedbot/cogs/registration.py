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

	"""
	Registration command.
	Takes a name and platform, and then creates a Player if there isn't already a registered Player
	that corresponds with the invoker. If there is, it will update the player with new information.
	"""

	@commands.command(name="register")
	async def register(self, ctx, platform, *, display_name):
		platforms = ["switch", "pc", "ps4"]

		if not platform.casefold() in platforms:
			logger.log_error("")
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
		if isinstance(error, commands.UserInputError):
			await ctx.send(error)

		if isinstance(error, commands.UserInputError):
			await ctx.send(error)

		elif isinstance(error, NotImplementedError):
			await ctx.send("You're attempting to access a command that isn't ready yet.")

		elif isinstance(error, commands.BadArgument):
			await ctx.send(error)

		else:
			await ctx.send(error)
			traceback.print_exc()


def setup(bot):
	bot.add_cog(Registration(bot))
