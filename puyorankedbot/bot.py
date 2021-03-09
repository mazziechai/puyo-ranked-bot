import os
import sqlite3

from discord.ext import commands

import config
from logger import log_info

if not os.path.exists("../data.db3"):
	log_info("Database file not found, initializing a new one.")
	db = sqlite3.connect("../data.db3")
	db.executescript(open("../database_schema.sql", "r").read())
	db.close()
	log_info("The database has been set up.")

config.create_config()

token = config.get_config("token")
bot = commands.Bot(command_prefix=config.get_config("bot_prefix"))

# Load command cogs.
if __name__ == "__main__":
	for file_name in os.listdir("cogs"):
		if file_name.endswith(".py"):
			bot.load_extension("cogs." + file_name[:-3])


@bot.event
async def on_ready():
	log_info("Logged in as {}#{}".format(bot.user.name, bot.user.discriminator))

@bot.event
async def on_command_error(ctx, error):
	# Silent command not found errors, other errors should be handled through each command.
	pass

# Logging in.
bot.run(token, bot=True, reconnect=True)
