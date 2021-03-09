from discord.ext import commands

from core import utils
from core.database import database


class Update(commands.Cog):
	"""
	Commands for updating player info.
	"""

	def __init__(self, bot):
		self.bot = bot

	@commands.group(name="update", help="Update your information.")
	async def update(self, ctx):
		if ctx.invoked_subcommand is None:
			await ctx.send(f"Usage: {self.bot.command_prefix}update (displayname | username) ...")

	@update.error
	async def update_OnError(self, ctx, error):
		await utils.handle_command_error(ctx, error)

	@update.command(
		name="displayname",
		usage="[display name]",
		help="Set, change or clear your display name."
	)
	async def update_displayname(self, ctx, *name):
		name = " ".join(name).strip()
		if database.execute(
				"SELECT EXISTS (SELECT 1 FROM players WHERE id = ? AND platforms <> '')",
				(ctx.author.id,)
		).fetchone()[0] == 0:
			await ctx.send("You are not registered yet.")
			return
		if name == "":
			database.execute("UPDATE players SET display_name = NULL WHERE id = ?", (ctx.author.id,))
			database.commit()
			await ctx.send("Cleared display name.")
		else:
			if database.execute(
					"SELECT EXISTS (SELECT 1 FROM players WHERE display_name = ?)",
					(name,)
			).fetchone()[0] == 1:
				await ctx.send(
					f"The display name \"{utils.escape_markdown(name)}\" is already in use by another player.")
				return
			database.execute("UPDATE players SET display_name = ? WHERE id = ?", (name, ctx.author.id))
			database.commit()
			await ctx.send(f"Display name set to \"{utils.escape_markdown(name)}\".")

	@update.command(
		name="username",
		usage="<platform> [username]",
		help="Set, change or clear your username on a platform."
	)
	async def update_username(self, ctx, platform, *name):
		platform = platform.casefold()
		if not platform in utils.platform_name_mapping:
			await ctx.send(
				"You need to provide a valid platform that is one of the following: "
				+ ", ".join(utils.platform_names)
			)
			return
		name = " ".join(name).strip()
		player = database.execute(
			"SELECT platforms FROM players WHERE id = ? AND platforms <> ''",
			(ctx.author.id,)
		).fetchone()
		if player is None:
			await ctx.send("You are not registered yet.")
			return
		if platform not in player[0].split():
			await ctx.send(f"You are not signed up for {utils.format_platform_name(platform)}.")
			return
		if name == "":
			database.execute(f"UPDATE players SET username_{platform} = NULL WHERE id = ?", (ctx.author.id,))
			database.commit()
			await ctx.send("Cleared username for {utils.format_platform_name(platform)}.")
		else:
			if database.execute(
					f"SELECT EXISTS (SELECT 1 FROM players WHERE username_{platform} = ?)",
					(name,)
			).fetchone()[0] == 1:
				await ctx.send(
					f"The username \"{utils.escape_markdown(name)}\" on "
					f"{utils.format_platform_name(platform)} is already in use by another player."
				)
				return
			database.execute(f"UPDATE players SET username_{platform} = ? WHERE id = ?", (name, ctx.author.id))
			database.commit()
			await ctx.send(
				f"Username on {utils.format_platform_name(platform)} set to "
				f"\"{utils.escape_markdown(name)}\"."
			)

	@update_username.error
	async def update_username_OnError(self, ctx, error):
		if isinstance(error, commands.MissingRequiredArgument):
			await ctx.send(f"Usage: {self.bot.command_prefix}update username <platform> [username]")
			return
		await utils.handle_command_error(ctx, error)


def setup(bot):
	bot.add_cog(Update(bot))
