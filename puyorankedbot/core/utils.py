import logger
import traceback
import datetime
import re

def parse_integer(s, mustNotBeNegative=False):
	try:
		n = int(s)
		if mustNotBeNegative and n < 0:
			raise Exception()
		return n
	except:
		raise Exception(f"`{s}` is not a natural number.")

async def handle_command_error(ctx, error):
	await ctx.send("An error has occured while executing the command.")
	logger.log_error(''.join(traceback.format_exception(None, error, error.__traceback__)))

platform_names = [ "PC", "Switch", "PS4" ]
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

def escape_markdown(s):
	return re.sub(
		r"\\\\([_*\[\]()~`>\#\+\-=|\.!])",
		r"\1",
		re.sub(r"([_*\[\]()~`>\#\+\-=|\.!])", r"\\\1", s)
	)
