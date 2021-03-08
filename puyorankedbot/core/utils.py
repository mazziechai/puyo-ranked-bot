import logger
import traceback


def parse_integer(s, must_not_be_negative=False):
	try:
		n = int(s)
		if must_not_be_negative and n < 0:
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
