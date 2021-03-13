# This module handles finding matches based on a queue players can join.

import asyncio
from config import get_config
from core.database import database
from core import utils

class Player:
	"""
	A handle for a player containing additional variables.
	"""
	extend_intervals = 5
	extend_amount = 1

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
		self.resolved = False
		self.platform_count = 0
		self.intervals = 0

	def get_nodes(self):
		return (self.low, self.high)

	def trigger_resolve(self):
		self.matchfinder.mark_player_done(self.player_id)
		self.resolved = True

	def extend(self):
		self.intervals = (self.intervals + 1) % self.extend_intervals
		if self.intervals != 0: return
		self.low.value -= self.extend_amount
		self.high.value += self.extend_amount

	def update_rating(self, mu, phi):
		self.mu = mu
		self.phi = phi
		self.low.value = mu - 2*phi
		self.high.value = mu + 2*phi

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
		return (self.start and not that.start) \
			if self.value == that.value \
			else self.value < that.value

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
		self.matchfinding_interval = get_config("matchmaking_interval")
		Player.extend_intervals = get_config("matchmaking_extend_intervals")
		Player.extend_amount = get_config("matchmaking_extend_amount")
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
		asyncio.create_task(self.find_matches())

	async def on_reaction(self, data):
		if data.user_id == self.bot_id:
			return
		if data.message_id != self.matchfinding_message.id:
			return
		if data.emoji.id not in self.emoji_mapping:
			return
		platform_data = self.emoji_mapping[data.emoji.id]
		if data.event_type == "REACTION_ADD":
			if data.user_id in self.player_map:
				player = self.player_map[data.user_id]
			else:
				player_data = database.execute(
					"SELECT id, platforms, rating_mu, rating_phi FROM players "
					"WHERE id = ? AND platforms <> ''",
					(data.user_id,)
				).fetchone()
				if player_data is None:
					await self.matchfinding_message.remove_reaction(
						data.emoji,
						await utils.get_member(data.user_id)
					)
					return
				player = Player(player_data, self)
			if platform_data[0] not in player.platforms:
				await self.matchfinding_message.remove_reaction(
					data.emoji,
					await utils.get_member(data.user_id)
				)
				return
			self.player_map[player.player_id] = player
			self.pools[platform_data[1]].add(player)
			player.platform_count += 1
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
					matches.append((
						current_player, node.player,
						utils.platform_names[pool]
					))
					current_player = None
			else:
				current_player = None
		return matches

	async def cleanup_players(self):
		for player_id in self.done_players:
			if player_id in self.player_map:
				player = self.player_map[player_id]
				member = utils.get_member(player_id)
				for i in range(3):
					pool = self.pools[i]
					if player in pool:
						await self.matchfinding_message.remove_reaction(
							self.platforms[i][3],
							member
						)
						pool.discard(player)
				self.player_map.pop(player_id)
		self.done_players.clear()

	async def find_matches(self):
		while True:
			for player in self.player_map.values():
				player.extend()
			matches = []
			for i in range(3):
				self.populate_matches(matches, i)
			if len(matches) != 0:
				await self.announcement_channel.send('\n'.join(
					f"<@!{match[0].player_id}> vs. <@!{match[1].player_id}> | {match[2]} | "
					f"First to **{utils.get_match_goal(match[0].mu, match[1].mu)}**"
					for match in matches
				))
			await self.cleanup_players()
			await asyncio.sleep(self.matchfinding_interval)

matchfinder = Matchfinder()
