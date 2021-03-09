from discord.ext import commands

from core import utils
from core.database import database


class Registration(commands.Cog):
	"""
	Cog for registering and unregistering.
	"""

	def __init__(self, bot):
		self.bot = bot

	@commands.command(
		name="register",
		usage="<platform>",
		help="Register yourself into the system."
	)
	async def register(self, ctx, platform: str):
		"""
		Registers a new Player into the system.
		:param ctx: Context, comes with every command
		:param platform: "switch", "pc", or "ps4".
		:return: None
		"""
		platform = platform.casefold()
		if not platform in utils.platform_name_mapping:
			await ctx.send("You need to provide a valid platform that is one of the following: "
						   + ", ".join(utils.platform_names)
						   )
			return
		player = database.execute("SELECT platforms FROM players WHERE id = ?", (ctx.author.id,)).fetchone()
		if player is None:
			# First time registering.
			database.execute(
				"INSERT INTO players (id, platforms) VALUES (?, ?)",
				(ctx.author.id, platform)
			)
			database.commit()
			await ctx.send(f"Signed up for {utils.format_platform_name(platform)}.")
		else:
			# Already registered.
			platforms = player["platforms"].split()
			if platform in platforms:
				await ctx.send("You're already signed up for {utils.format_platform_name(platform)}.")
				return
			else:
				platforms.append(platform)
				database.execute(
					"UPDATE players SET platforms = ? WHERE id = ?",
					(" ".join(platforms), ctx.author.id)
				)
				database.commit()
				await ctx.send(f"Signed up for {utils.format_platform_name(platform)}.")

	@register.error
	async def register_OnError(self, ctx, error):
		if isinstance(error, commands.MissingRequiredArgument):
			await ctx.send(f"Usage: {self.bot.command_prefix}register <platform>")
		elif isinstance(error, NotImplementedError):
			await ctx.send("You're attempting to access a command that isn't ready yet.")
		else:
			await utils.handle_command_error(ctx, error)

	@commands.command(
		name="unregister",
		usage="<platform>",
		help="Unregister yourself from the system."
	)
	async def unregister(self, ctx, platform):
		"""
		Unregisters a player by removing the requested platform from their record.
		:param ctx: Context, comes with every command
		:param platform: "switch", "pc", "ps4".
		:return: None
		"""
		platform = platform.casefold()
		if not platform.casefold() in utils.platform_name_mapping:
			await ctx.send("You need to provide a valid platform that is one of the following: "
						   + ", ".join(utils.platform_names)
						   )
			return
		player = database.execute(
			"SELECT platforms FROM players WHERE id = ? AND platforms <> ''",
			(ctx.author.id,)
		).fetchone()
		if player is None:
			await ctx.send(f"You are not signed up here, no worries.")
		else:
			platforms = player["platforms"].split()
			if platform in platforms:
				platforms.remove(platform)
				database.execute(
					"""
					UPDATE players SET
						platforms = "",
						display_name = NULL,
						username_pc = NULL,
						username_switch = NULL,
						username_ps4 = NULL
					WHERE id = :id
					"""
					if len(platforms) == 0 else
					"UPDATE players SET platforms = :platforms WHERE id = :id",
					{"platforms": " ".join(platforms), "id": ctx.author.id}
				)
				database.commit()
				await ctx.send(
					f"Unregistered from {utils.format_platform_name(platform)}." +
					(" __You are no longer in the system.__" if len(platforms) == 0 else "")
				)
			else:
				await ctx.send(f"You are not signed up for {utils.format_platform_name(platform)}.")

	@unregister.error
	async def unregister_OnError(self, ctx, error):
		if isinstance(error, commands.MissingRequiredArgument):
			await ctx.send(f"Usage: {self.bot.command_prefix}unregister <platforms>")
			return
		await utils.handle_command_error(ctx, error)


def setup(bot):
	bot.add_cog(Registration(bot))
