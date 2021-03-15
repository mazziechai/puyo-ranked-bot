import discord
from logger import logger
import traceback
import re
from bisect import bisect
import config

bot = None
guild = None

async def get_member(member_id):
	try:
		return await guild.fetch_member(member_id)
	except discord.NotFound:
		return None

def parse_integer(s, mustNotBeNegative=False):
	try:
		n = int(s)
		if mustNotBeNegative and n < 0:
			raise Exception()
		return n
	except Exception:
		raise Exception(f"`{s}` is not a natural number.")


async def handle_command_error(ctx, error):
	await ctx.send("An error occured while executing the command.")
	logger.error(''.join(traceback.format_exception(None, error, error.__traceback__)))


platform_names = ["PC", "Switch", "PS4"]
platform_name_mapping = {
	"pc": "PC",
	"switch": "Switch",
	"ps4": "PlayStation 4"
}


def format_platform_name(platform):
	try:
		return platform_name_mapping[platform]
	except KeyError:
		return "Unknown"


class Rank:
	def __init__(self, name, color, value):
		self.name = name
		self.color = color
		self.value = value
		self.role_id = config.get_config("rank_roles")[name.lower()]

ranks = [
	Rank("Bronze", 0xE7A264, 0),
	Rank("Silver", 0xE4E4E4, 1),
	Rank("Gold", 0xDDDA4C, 2),
	Rank("Platinum", 0xD6EEF3, 3),
	Rank("Diamond", 0x7EDEF3, 4),
	Rank("Legend", 0xFF6060, 5)
]
rank_null = Rank("Placements", 0x9D9D9D, -1)
rank_threshold_mapping = [500, 1000, 1500, 2000, 2500]
match_goals = [5, 7, 9, 11, 13, 15]

def get_rank(mu, phi=0):
	return (
		None if mu is None else
		ranks[bisect(rank_threshold_mapping, mu)] if phi < 150 else rank_null
	)

# Convenience function to directly get the rank value without going through the rank object.
def get_rank_value(mu, phi=0):
	return bisect(rank_threshold_mapping, mu) if phi < 150 else -1

def get_match_goal(mu1, mu2):
	return match_goals[get_rank_value(mu1)+get_rank_value(mu2)+1 >> 1]

def get_rank_with_comparison(old_mu, old_phi, new_mu, new_phi):
	old_rank = get_rank(old_mu, old_phi)
	new_rank = get_rank(new_mu, new_phi)
	if old_rank == new_rank:
		return old_rank.name
	else:
		if old_rank == rank_null:
			return f"**Placed into {new_rank.name}**"
		elif new_rank == rank_null:
			return f"**Rank lost, back to placement**"
		else:
			return f"**{'Promoted' if new_mu > old_mu else 'Demoted'} to {new_rank.name}**"

async def update_role(member_id, old_mu, old_phi, new_mu, new_phi):
	if member is None: return
	old_rank = get_rank(old_mu, old_phi)
	new_rank = get_rank(new_mu, new_phi)
	if old_rank == new_rank: return
	member = await get_member(member_id)
	if old_mu is not None:
		await member.remove_roles(discord.Object(old_rank.role_id))
	if new_mu is not None:
		await member.add_roles(discord.Object(new_rank.role_id))


def escape_markdown(s):
	return re.sub(
		r"\\\\([_*\[\]()~`>\#\+\-=|\.!])",
		r"\1",
		re.sub(r"([_*\[\]()~`>\#\+\-=|\.!])", r"\\\1", s)
	)
