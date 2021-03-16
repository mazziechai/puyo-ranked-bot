import os
import sqlite3
from logger import logger
import config

if not os.path.exists("../data.db3"):
	logger.info("Database file not found, initializing a new one.")
	db = sqlite3.connect("../data.db3")
	db.executescript(open("../database_schema.sql", "r").read())
	db.close()
	logger.info("The database has been set up.")

config.create_config()

import discord
from discord.ext import commands
from core import scheduled_rating_update
from core import utils
from core.match_manager import matchfinder, match_manager
from core import database

token = config.get_config("token")
bot = commands.Bot(command_prefix=config.get_config("bot_prefix"))
bot.help_command = commands.DefaultHelpCommand(width=256)

utils.bot = bot
command_channel_id = config.get_config("command_channel")

# Load command cogs.
if __name__ == "__main__":
	for file_name in os.listdir("cogs"):
		if file_name.endswith(".py"):
			bot.load_extension("cogs." + file_name[:-3])


@bot.event
async def on_ready():
	logger.info("Logged in as {}#{}".format(bot.user.name, bot.user.discriminator))
	utils.guild = await bot.fetch_guild(config.get_config("guild_id"))
	scheduled_rating_update.setup()
	await matchfinder.setup()
	match_manager.setup()
	database.setup_backup()

@bot.check
async def command_check(ctx):
	return ctx.channel.id == command_channel_id

@bot.event
async def on_command_error(ctx, error):
	# Silent command not found errors, other errors should be handled through each command.
	pass

# Logging in.
bot.run(token, bot=True, reconnect=True)
