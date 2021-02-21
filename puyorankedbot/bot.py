from discord.ext import commands

from puyorankedbot import config
from puyorankedbot.logger import log_info

config.create_config()

token = config.get_config("token")
bot = commands.Bot(command_prefix=',')

extensions = ["cogs.registration", "cogs.information", "cogs.matches"]

# Here, we're loading all of the extensions listed above.
if __name__ == "__main__":
	for extension in extensions:
		bot.load_extension(extension)


@bot.event
async def on_ready():
	log_info("Logged in as {}#{}".format(bot.user.name, bot.user.discriminator))
	print("Logged in as {}#{}".format(bot.user.name, bot.user.discriminator))


# Logging in.
bot.run(token, bot=True, reconnect=True)
