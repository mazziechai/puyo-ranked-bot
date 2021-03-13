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
		rank = utils.get_rank(player["rating_mu"], player["rating_phi"])

		embed = discord.Embed(
			type="rich",
			title="_Puyo training grounds_ player info",
			description=
			("" if user is None else f"{user.name}#{user.discriminator}")
			+ f"\nID {player['id']}",
			colour=rank.color
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
		embed.add_field(name="Rank", value=rank.name)
		embed.add_field(
			name="Matches",
			value=database.execute(
				"SELECT COUNT(*) FROM matches WHERE player1=:id OR player2=:id",
				{"id": player["id"]}
			).fetchone()[0]
		)
		if ctx.author.id != player["id"]:
			command_user_row = database.execute(
				"SELECT rating_mu FROM players WHERE id=? AND platforms <> ''",
				(ctx.author.id,)
			).fetchone()
			if command_user_row is not None:
				match_goal = utils.get_match_goal(player["rating_mu"], command_user_row[0]) 
				embed.add_field(
					name="If you battle",
					value=f"First to **{match_goal}**"
				)
		await ctx.send(embed=embed)

	# Groupings, these don't do anything on their own.
	@commands.group(name="info", help="Retrieve information about players and matches.")
	async def info(self, ctx):
		if ctx.invoked_subcommand is None:
			await ctx.send_help(self.info)

	@info.error
	async def info_OnError(self, ctx, error):
		await utils.handle_command_error(ctx, error)

	# info player
	@info.group(name="player", help="Retrieve information about a Puyo player.")
	async def info_player(self, ctx):
		if ctx.invoked_subcommand is None:
			await ctx.send_help(self.info_player)

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
		await self.send_player_info(ctx, player, await utils.get_member(user.id))

	@info_player_user.error
	async def info_player_user_OnError(self, ctx, error):
		if isinstance(error, commands.MissingRequiredArgument):
			await ctx.send_help(self.info_player_user)
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
		if name == "":
			await ctx.send_help(self.info_player_name)
			return

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
		await self.send_player_info(ctx, player, await utils.get_member(player["id"]))

	@info_player_name.error
	async def info_player_name_OnError(self, ctx, error):
		if isinstance(error, commands.MissingRequiredArgument):
			await ctx.send_help(self.info_player_name)
			return
		await utils.handle_command_error(ctx, error)

	@info_player.command(
		name="username",
		usage="<platform> <username>",
		help="Retrieve information about a Puyo player based on their username on a platform."
	)
	async def info_player_username(self, ctx, platform, *username):
		username = " ".join(username).strip()
		if username == "":
			await ctx.send_help(self.info_player_username)
			return

		platform = platform.casefold()
		if not platform in utils.platform_name_mapping:
			await ctx.send(
				"You need to provide a valid platform that is one of the following: "
				+ ", ".join(utils.platform_names)
			)
			return

		player = database.execute(
			f"SELECT * FROM players WHERE username_{platform}=?",
			(username,)
		).fetchone()
		if player is None:
			await ctx.send(
				"There is no registered player with the username "
				f"\"{utils.escape_markdown(username)}\" on {utils.format_platform_name(platform)}."
			)
			return
		await self.send_player_info(ctx, player, await utils.get_member(player["id"]))

	@info_player_username.error
	async def info_player_username_OnError(self, ctx, error):
		if isinstance(error, commands.MissingRequiredArgument):
			await ctx.send_help(self.info_player_username)
			return
		await utils.handle_command_error(ctx, error)

	# info match
	async def add_match_embed_player(self, embed, match, player):
		player = "player" + player
		player_row = database.execute(
			"SELECT display_name FROM players WHERE id = ?",
			(match[player],)
		).fetchone()
		name = player_row["display_name"]
		if name is None:
			user = await utils.get_member(match[player])
			name = "[No name.]" if user is None else user.display_name
		rating_change = match[player + "_rating_change"]
		rating_change_sign = '+' if rating_change >= 0 else '\u2013'
		embed.add_field(
			name=utils.escape_markdown(name),
			value=(
				f"**{match[player + '_score']}**\n"
				f"{int(match[player + '_old_mu'])} \u00B1 {int(2 * match[player + '_old_phi'])} \u2192 "
				f"{int(match[player + '_new_mu'])} \u00B1 {int(2 * match[player + '_new_phi'])}\n"
				f"{rating_change_sign} {abs(rating_change)}\n" +
				utils.get_rank_with_comparison(
					match[player + '_old_mu'], match[player + '_old_phi'],
					match[player + '_new_mu'], match[player + '_new_phi']
				)
			)
		)

	@info.command(
		name="match",
		usage="<ID>",
		help="Retrieve information about a match."
	)
	async def info_match(self, ctx, ids):
		try:
			match_id = int(ids)
		except ValueError:
			match_id = 0
		if match_id < 1:
			await ctx.send(f"`{ids}` is not a positive integer.")
			return

		match = database.execute("SELECT * FROM matches WHERE id = ?", (match_id,)).fetchone()
		if match is None:
			await ctx.send(f"There is not yet a match with ID {match_id}.")
			return

		embed = discord.Embed(
			type="rich",
			title="Match information",
			color=0xFF8337
		)
		await self.add_match_embed_player(embed, match, "1")
		await self.add_match_embed_player(embed, match, "2")
		embed.set_footer(text=f"Match ID: {match_id}")
		embed.timestamp = match["date"]
		
		await ctx.send(embed=embed)

	@info_match.error
	async def info_match_OnError(self, ctx, error):
		if isinstance(error, commands.MissingRequiredArgument):
			await ctx.send_help(self.info_match)
			return
		await utils.handle_command_error(ctx, error)

def setup(bot):
	bot.add_cog(Information(bot))
