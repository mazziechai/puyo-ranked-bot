# This module handles finding matches based on a queue players can join.

import discord
import asyncio
from datetime import datetime
from config import get_config
from core.database import database
from core import utils
from core.glicko2 import glicko2
from core import match_message_helper

TICK_MARK = '\u2705'

class Player:
	"""
	A handle for a player containing additional variables.
	"""
	def __init__(self, data, matchfinder):
		"""
		:param data: The database information of the player.
		:param matchfinder: The Matchfinder object.
		"""
		self.matchfinder = matchfinder
		self.player_id = data["id"]
		self.mu = data["rating_mu"]
		self.phi = data["rating_phi"]
		self.low = Node(True, self, self.mu - 2*self.phi)
		self.high = Node(False, self, self.mu + 2*self.phi)
		self.platforms = set(data["platforms"].split())
		self.usernames = [
			data["username_pc"],
			data["username_switch"],
			data["username_ps4"]
		]
		self.resolved = False
		self.platform_count = 0
		self.intervals = 0

	def get_nodes(self):
		return (self.low, self.high)

	def get_ping(self, pool):
		username = self.usernames[pool]
		return (
			f"<@!{self.player_id}>" +
			("" if username is None else f" ({utils.escape_markdown(username)})")
		)

	def trigger_resolve(self):
		if self.resolved: return
		self.matchfinder.mark_player_done(self.player_id)
		self.resolved = True

class Node:
	def __init__(self, start, player, value):
		"""
		:param start: True if self is a starting node, False if ending node.
		:param player: The Player object.
		:param value: The position of the node on the ribbon.
		"""
		self.start = start
		self.player = player
		self.value = value

	def __lt__(self, that):
		return (
			self.value < that.value or
			(self.value == that.value and self.start and not that.start)
		)

class Matchfinder:
	def __init__(self):
		self.player_map = {}
		self.done_players = []
		self.pools = [set() for _ in range(3)]
		self.current_task = None
		self.current_task_should_wait = False
		self.new_task_waiting = False
		self.running = False

	async def setup(self):
		if self.running: return
		self.running = True
		self.bot_id = utils.bot.user.id

		emoji_mapping = {
			emoji.id: emoji
			for emoji in utils.guild.emojis
		}
		self.emoji_mapping = {}
		self.platforms = get_config("matchmaking_platforms")
		for platform in self.platforms:
			platform.append(emoji_mapping[platform[2]])
			self.emoji_mapping[platform[2]] = (platform[0], platform[1])
		self.matchfinding_message = await (
			utils.bot
			.get_channel(get_config("matchmaking_message_channel"))
			.fetch_message(get_config("matchmaking_message_id"))
		)
		self.announcement_channel = utils.bot.get_channel(
			get_config("matchmaking_announcement_channel")
		)

		await self.matchfinding_message.clear_reactions()
		for emoji_id in self.emoji_mapping:
			await self.matchfinding_message.add_reaction(emoji_mapping[emoji_id])
		utils.bot.add_listener(self.on_reaction, "on_raw_reaction_add")
		utils.bot.add_listener(self.on_reaction, "on_raw_reaction_remove")

	async def on_reaction(self, data):
		if data.user_id == self.bot_id:
			return
		if data.message_id != self.matchfinding_message.id:
			return
		if data.emoji.id not in self.emoji_mapping:
			return
		platform_data = self.emoji_mapping[data.emoji.id]
		if data.event_type == "REACTION_ADD":
			if data.user_id in match_manager.player_map:
				await remove_reaction(
					self.matchfinding_message,
					data.emoji,
					await utils.get_member(data.user_id)
				)
				return
			if data.user_id in self.player_map:
				player = self.player_map[data.user_id]
			else:
				player_data = database.execute(
					"SELECT * FROM players WHERE id = ? AND platforms <> ''",
					(data.user_id,)
				).fetchone()
				if player_data is None:
					await remove_reaction(
						self.matchfinding_message,
						data.emoji,
						await utils.get_member(data.user_id)
					)
					return
				player = Player(player_data, self)
			if platform_data[0] not in player.platforms:
				await remove_reaction(
					self.matchfinding_message,
					data.emoji,
					await utils.get_member(data.user_id)
				)
				return
			self.player_map[player.player_id] = player
			self.pools[platform_data[1]].add(player)
			player.platform_count += 1
			await self.find_matches()
		else:
			if data.user_id not in self.player_map:
				return
			player = self.player_map[data.user_id]
			pool = self.pools[platform_data[1]]
			if player in pool:
				pool.discard(player)
				player.platform_count -= 1
				if player.platform_count < 1:
					self.player_map.pop(player.player_id)

	def mark_player_done(self, player_id):
		self.done_players.append(player_id)

	def populate_matches(self, matches, pool):
		ribbon = []
		for player in self.pools[pool]:
			ribbon.extend(player.get_nodes())
		ribbon.sort()
		current_player = None
		for node in ribbon:
			if node.player.resolved:
				continue
			if node.start:
				if current_player is None:
					current_player = node.player
				else:
					current_player.trigger_resolve()
					node.player.trigger_resolve()
					matches.append((current_player, node.player, pool))
					current_player = None
			else:
				current_player = None
		return matches

	async def cleanup_players(self):
		for player_id in self.done_players:
			if player_id in self.player_map:
				player = self.player_map.pop(player_id)
				member = await utils.get_member(player_id)
				for i in range(3):
					pool = self.pools[i]
					if player in pool:
						await remove_reaction(
							self.matchfinding_message,
							self.platforms[i][3],
							member
						)
						pool.discard(player)
		self.done_players.clear()

	async def find_matches(self):
		matches = []
		for i in range(3):
			self.populate_matches(matches, i)
		for match_data in matches:
			message = await self.announcement_channel.send(
				f"{match_data[0].get_ping(match_data[2])} vs. "
				f"{match_data[1].get_ping(match_data[2])} | "
				f"{utils.platform_names[match_data[2]]} | First to **" +
				f"{utils.get_match_goal(match_data[0].mu, match_data[1].mu)}"
				"**"
			)
			match = PendingMatch(
				message_id=message.id,
				player1=match_data[0].player_id,
				player2=match_data[1].player_id,
				time=datetime.now()
			)
			match.save()
			match_manager.add_match(match)
			await message.add_reaction(TICK_MARK)
		await self.cleanup_players()

class PendingMatch:
	def __init__(self, **args):
		self.message_id = args["message_id"]
		self.player1 = args["player1"]
		self.player2 = args["player2"]
		self.player1_data = match_message_helper.get_player_by_ID(self.player1)
		self.player2_data = match_message_helper.get_player_by_ID(self.player2)
		self.goal = utils.get_match_goal(
			self.player1_data["rating_mu"], self.player2_data["rating_mu"]
		)
		self.time = args["time"]
		self.timestamp = self.time.timestamp()
		self.player1_score = None
		self.player2_score = None
		self.confirming_timestamp = None
		self.confirm_status = 0
		self.cancel_status = 0
	
	def save(self):
		database.execute(
			"INSERT INTO pending_matches "
			"(message_id, player1, player2, time) "
			"VALUES (?, ?, ?, ?)",
			(self.message_id, self.player1, self.player2, self.time)
		)
		database.commit()

class MatchManager:	
	"""
	Manages arranged matches and result reporting.
	"""
	clear_interval = 60

	def __init__(self):
		self.player_map = {}
		self.message_map = {}
		self.pending_matches = []
		self.confirming_matches = []
		self.running = False

	def setup(self):
		if self.running: return
		self.running = True
		self.bot_id = utils.bot.user.id
		self.announcement_channel = utils.bot.get_channel(
			get_config("matchmaking_announcement_channel")
		)
		self.announcement_channel_id = self.announcement_channel.id
		self.output_channel = utils.bot.get_channel(
			get_config("command_channel")
		)
		for row in (
			database.execute("SELECT rowid, * FROM pending_matches")
			.fetchall()
		):
			self.add_match(PendingMatch(**row.dict))

		self.match_lifetime = get_config("pending_match_lifetime")
		asyncio.create_task(self.clear_matches())
		utils.bot.add_listener(self.on_reaction, "on_raw_reaction_add")
	
	async def on_reaction(self, data):
		if data.user_id == self.bot_id:
			return
		if data.channel_id != self.announcement_channel_id:
			return
		if data.message_id not in self.message_map:
			return
		match = self.message_map[data.message_id]
		if data.user_id != match.player1 and data.user_id != match.player2:
			await remove_reaction(
				await self.announcement_channel.fetch_message(data.message_id),
				data.emoji,
				await utils.get_member(data.user_id)
			)
	
	def add_match(self, match):
		self.pending_matches.append(match)
		self.player_map[match.player1] = (match, False)
		self.player_map[match.player2] = (match, True)
		self.message_map[match.message_id] = match
	
	async def cleanup_for_match(self, match):
		await (
			await self.announcement_channel.fetch_message(match.message_id)
		).clear_reactions()
		self.message_map.pop(match.message_id)
		self.player_map.pop(match.player1)
		self.player_map.pop(match.player2)
		database.execute(
			"DELETE FROM pending_matches WHERE message_id = ?",
			(match.message_id,)
		)
		database.commit()

	async def get_confirmation_sides(self, message_id, player1, player2):
		result = 0
		reaction = None
		for message_reaction in (
			(await self.announcement_channel.fetch_message(message_id))
			.reactions
		):
			if message_reaction.emoji == TICK_MARK:
				reaction = message_reaction
				break
		if reaction is not None:
			async for user in reaction.users():
				if user.id == player1: result |= 2
				elif user.id == player2: result |= 1
		return result
	
	async def process_match_complete(self, match):
		player1 = match.player1_data
		old_rating1 = glicko2.Rating(
			player1["rating_mu"], player1["rating_phi"], player1["rating_sigma"]
		)
		player2 = match.player2_data
		old_rating2 = glicko2.Rating(
			player2["rating_mu"], player2["rating_phi"], player2["rating_sigma"]
		)

		if match.player1_score > match.player2_score:
			new_rating1, new_rating2 = (
				glicko2.Glicko2().rate_1vs1(old_rating1, old_rating2)
			)
		else:
			new_rating2, new_rating1 = (
				glicko2.Glicko2().rate_1vs1(old_rating2, old_rating1)
			)

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
			player1["id"], player2["id"],
			match.player1_score, match.player2_score,
			old_rating1.mu, old_rating1.phi, old_rating1.sigma,
			new_rating1.mu, new_rating1.phi, new_rating1.sigma,
			old_rating2.mu, old_rating2.phi, old_rating2.sigma,
			new_rating2.mu, new_rating2.phi, new_rating2.sigma
		))
		database.commit()

		embed = discord.Embed(
			type="rich",
			title="Match recorded",
			color=0x00E323
		)
		await match_message_helper.add_report_field(
			embed, player1, match.player1_score,
			old_rating1.mu, old_rating1.phi,
			new_rating1.mu, new_rating1.phi
		)
		await match_message_helper.add_report_field(
			embed, player2, match.player2_score,
			old_rating2.mu, old_rating2.phi,
			new_rating2.mu, new_rating2.phi
		)
		embed.set_footer(text=f"Match ID: {cursor.lastrowid}")
		await self.output_channel.send(embed=embed)
		await self.cleanup_for_match(match)

	async def process_player(self, player, flag, embed):
		old_rating = glicko2.Rating(
			player["rating_mu"], player["rating_phi"], player["rating_sigma"]
		)
		new_rating = old_rating if flag != 0 else \
			glicko2.Glicko2().rate_1vs1(old_rating, old_rating)[1]
		database.execute(
			"UPDATE players "
			"SET rating_mu = ?, rating_phi = ?, rating_sigma = ? "
			"WHERE id = ?",
			(new_rating.mu, new_rating.phi, new_rating.sigma, player["id"])
		)
		database.commit()
		await match_message_helper.add_report_field(
			embed, player, None,
			old_rating.mu, old_rating.phi,
			new_rating.mu, new_rating.phi
		)
	
	match_timeout_messages = [
		"Both <@!%(player1)s> and <@!%(player2)s> "
		"did not confirm nor play the match.",
		"<@!%(player2)s> could play but "
		"<@!%(player1)s> did not respond.",
		"<@!%(player1)s> could play but "
		"<@!%(player2)s> did not respond.",
		"Both <@!%(player1)s> and <@!%(player2)s> "
		"confirmed to play the match but did not actually play."
	]

	async def process_match_timeout(self, match):
		sides = await self.get_confirmation_sides(
			match.message_id, match.player1, match.player2
		)
		embed = discord.Embed(
			type="rich",
			title="Match timeout",
			color=0xFF0000
		)
		if sides == 0:
			sides = 3
		await self.process_player(match.player1_data, sides & 2, embed)
		await self.process_player(match.player2_data, sides & 1, embed)
		await self.output_channel.send(
			content=self.match_timeout_messages[sides] % {
				"player1": match.player1,
				"player2": match.player2
			},
			embed=embed
		)
		await self.cleanup_for_match(match)

	async def clear_matches(self):
		while True:
			time = datetime.now().timestamp()
			while len(self.pending_matches) != 0:
				match = self.pending_matches[0]
				if time - match.timestamp >= self.match_lifetime:
					await self.process_match_timeout(match)
					self.pending_matches.pop(0)
				else:
					break
			while len(self.confirming_matches) != 0:
				match = self.confirming_matches[0]
				if time - match.confirming_timestamp >= 180:
					await self.process_match_complete(match)
					self.confirming_matches.pop(0)
				else:
					break
			await asyncio.sleep(self.clear_interval)

async def remove_reaction(message, emoji, user):
	"""
	This swallows edge cases where removing a reaction might fail.
	"""
	try:
		await message.remove_reaction(emoji, user)
	except:
		pass

matchfinder = Matchfinder()
match_manager = MatchManager()
