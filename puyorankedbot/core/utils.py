import logger
import traceback
import re


def parse_integer(s, mustNotBeNegative=False):
	try:
		n = int(s)
		if mustNotBeNegative and n < 0:
			raise Exception()
		return n
	except Exception:
		raise Exception(f"`{s}` is not a natural number.")


async def handle_command_error(ctx, error):
	await ctx.send("An error has occured while executing the command.")
	logger.log_error(''.join(traceback.format_exception(None, error, error.__traceback__)))


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


def get_rank(mu):
	if 999 >= mu:
		return "Bronze"
	if 1000 <= mu <= 1249:
		return "Silver"
	if 1250 <= mu <= 1499:
		return "Gold"
	if 1500 <= mu <= 1749:
		return "Platinum"
	if 1750 <= mu <= 1999:
		return "Diamond"
	if 2000 <= mu:
		return "Legend"


def escape_markdown(s):
	return re.sub(
		r"\\\\([_*\[\]()~`>\#\+\-=|\.!])",
		r"\1",
		re.sub(r"([_*\[\]()~`>\#\+\-=|\.!])", r"\\\1", s)
	)
