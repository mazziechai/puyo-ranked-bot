from discord.ext import commands

import config
from logger import log_info
from core import utils
import sqlite3, os

if not os.path.exists("../data.db3"):
	log_info("Database file not found, initializing a new one.")
	db = sqlite3.connect("../data.db3")
	db.executescript(open("../database_schema.sql", "r").read())
	db.close()
	log_info("The database has been set up.")

config.create_config()

token = config.get_config("token")
bot = commands.Bot(command_prefix=config.get_config("bot_prefix"))

extensions = [
	"cogs.information",
	"cogs.matches",
	"cogs.registration",
	"cogs.update"
]

# Here, we're loading all of the extensions listed above.
if __name__ == "__main__":
	for extension in extensions:
		bot.load_extension(extension)


@bot.event
async def on_ready():
	log_info("Logged in as {}#{}".format(bot.user.name, bot.user.discriminator))


# Logging in.
bot.run(token, bot=True, reconnect=True)
