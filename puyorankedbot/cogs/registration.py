from discord.ext import commands

from core import utils
from core.database import database
from core.match_manager import matchfinder, match_manager


class Registration(commands.Cog):
	"""
	Cog for registering and unregistering.
	"""

	def __init__(self, bot):
		self.bot = bot

	@classmethod
	def sanitize_platforms(cls, platforms_raw):
		platforms = []
		for name in platforms_raw:
			name = name.casefold()
			if name in utils.platform_name_mapping and name not in platforms:
				platforms.append(name)
		return platforms

	@commands.command(
		name="register",
		usage="<platforms>",
		help="Register yourself into the system."
	)
	async def register(self, ctx, *platforms_raw):
		platforms = self.sanitize_platforms(platforms_raw)
		if len(platforms) == 0:
			await ctx.send(
				"You need to provide a valid platform that is one of the following: "
				+ ", ".join(utils.platform_names)
			)
			return

		platform_names = ", ".join(utils.format_platform_name(platform) for platform in platforms)
			
		player = database.execute(
			"SELECT platforms, rating_mu, rating_phi FROM players WHERE id = ?",
			(ctx.author.id,)
		).fetchone()
		if player is None:
			# First time registering.
			database.execute(
				"INSERT INTO players (id, platforms) VALUES (?, ?)",
				(ctx.author.id, " ".join(platforms))
			)
			database.commit()
			await utils.update_role(ctx.author.id, None, None, 1500, 350)
			await ctx.send(f"Signed up for {platform_names}.")
		else:
			# Already registered.
			no_new_entries = True
			player_platforms = player["platforms"].split()
			for platform in platforms:
				if platform not in player_platforms:
					player_platforms.append(platform)
					no_new_entries = False
			if no_new_entries:
				await ctx.send(f"You're already signed up for {platform_names}.")
				return
			else:
				database.execute(
					"UPDATE players SET platforms = ? WHERE id = ?",
					(" ".join(player_platforms), ctx.author.id)
				)
				database.commit()
				await utils.update_role(ctx.author.id, None, None, player["rating_mu"], player["rating_phi"])
				await ctx.send(f"Signed up for {platform_names}.")

	@register.error
	async def register_OnError(self, ctx, error):
		if isinstance(error, commands.CheckFailure):
			return
		if isinstance(error, commands.MissingRequiredArgument):
			await ctx.send_help(self.register)
		else:
			await utils.handle_command_error(ctx, error)

	@commands.command(
		name="unregister",
		usage="<platforms>",
		help="Unregister yourself from the system."
	)
	async def unregister(self, ctx, *platforms_raw):
		if ctx.author.id in matchfinder.player_map:
			await ctx.send("You are currently in the matckmaking queue. Leave the queue before unregistering.")
			return
		if ctx.author.id in match_manager.player_map:
			await ctx.send("You have a match pending. Complete the match before unregistering.")
			return

		nuke = len(platforms_raw) != 0 and platforms_raw[0].casefold() == "all"
		platforms = self.sanitize_platforms(platforms_raw)
		if not nuke and len(platforms) == 0:
			await ctx.send(
				"You need to provide a valid platform that is one of the following: "
				+ ", ".join(utils.platform_names)
			)
			return
		platform_names = ", ".join(utils.format_platform_name(platform) for platform in platforms)

		player = database.execute(
			"SELECT platforms, rating_mu, rating_phi FROM players WHERE id = ? AND platforms <> ''",
			(ctx.author.id,)
		).fetchone()
		if player is None:
			await ctx.send(f"You are not signed up here, no worries.")
		else:
			old_player_platforms = player["platforms"].split()
			new_player_platforms = (
				[] if nuke else
				[platform for platform in old_player_platforms if platform not in platforms]
			)
			if len(new_player_platforms) != len(old_player_platforms):
				platform_nullify = ", ".join(f"username_{platform} = NULL" for platform in platforms)
				zenkeshita = nuke or len(new_player_platforms) == 0
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
					if zenkeshita else
					f"UPDATE players SET platforms = :platforms, {platform_nullify} WHERE id = :id",
					{"platforms": " ".join(new_player_platforms), "id": ctx.author.id}
				)
				database.commit()
				await ctx.send(
					"Unregistered from __all__ platforms. You are no longer in the system."
					if nuke else
					f"Unregistered from {platform_names}." +
					(" __You are no longer in the system.__" if len(new_player_platforms) == 0 else "")
				)
				if zenkeshita:
					await utils.update_role(ctx.author.id, player["rating_mu"], player["rating_phi"], None, None)
			else:
				await ctx.send(f"You are not signed up for {platform_names}.")

	@unregister.error
	async def unregister_OnError(self, ctx, error):
		if isinstance(error, commands.MissingRequiredArgument):
			await ctx.send_help(self.unregister)
			return
		await utils.handle_command_error(ctx, error)


def setup(bot):
	bot.add_cog(Registration(bot))
