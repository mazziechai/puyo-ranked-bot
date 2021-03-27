import discord
from discord.ext import commands

class CustomHelpCommand(commands.HelpCommand):
	async def send_bot_help(self, mapping):
		await self.get_destination().send(
			"**Puyo Training Grounds ranked system**\n"
			"This is the server's own system for ranking Puyo players.\n\n"
			"_Getting started_\n"
			"`{0}register <platforms>` to add yourself to the system. Each "
			"platform should be PC, Switch or PS4, separated by spaces.\n"
			"Then you can join the #matchmaking-portal to find players to "
			"play with. Further instructions are provided there.\n\n"
			"For more information about commands you can use, type "
			"`{0}help (Information | Leaderboard | Matches | Registration | "
			"Update)`."
			.format(self.clean_prefix)
		)

	async def send_cog_help(self, cog):
		await self.get_destination().send(cog.help.format(self.clean_prefix))

	async def send_group_help(self, group):
		await self.get_destination().send(group.help.format(self.clean_prefix))

	async def send_command_help(self, command):
		await self.get_destination().send(command.help.format(self.clean_prefix))
