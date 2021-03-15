import json
import os


class ConfigNotFoundException(Exception):
	pass


def get_config(key):
	"""
	Gets the key in the configuration file's value.
	:param key: A valid key in the config.json.
	:return value: The value of the key.
	"""
	if os.path.exists("../config.json"):
		with open("../config.json", "r") as file_obj:
			json_obj = json.load(file_obj)
			return json_obj[key]
	else:
		raise ConfigNotFoundException("config.json is missing")


def set_config(key, value):
	"""
	Sets a key in the configuration file to the value.
	:param key: A valid key in the config.json.
	:param value: The value that is going to be set.
	:return: None
	"""
	if os.path.exists("../config.json"):
		with open("../config.json", "r") as file_obj:
			json_obj = json.load(file_obj)
		json_obj[key] = value
		with open("../config.json", "w") as file_obj:
			json.dump(json_obj, file_obj)
	else:
		raise ConfigNotFoundException("config.json is missing")

def input_integer(prompt, allow_non_positive=True):
	error_message = f"The input must be {'an' if allow_non_positive else 'a positive'} integer."
	while True:
		try:
			i = int(input(prompt))
			if allow_non_positive or i > 0:
				return i
		except ValueError:
			pass
		print(error_message)

def create_config():
	"""
	Creates a configuration file after prompting the user for the values
	if the configuration file does not exist.
	:return: None
	"""
	if os.path.exists("../config.json"):
		return
	else:
		with open("../config.json", "w") as file_obj:
			print("Configuration file not found, supply the following:")
			data = {
				"token": input("Bot token: "),
				"bot_prefix": input("Bot prefix: "),
				"guild_id": input_integer("Main server ID: ", False),
				"command_channel": input_integer("Main command channel: ", False),
				"rating_period_start": input_integer("Rating period 0 start point (POSIX timestamp, seconds): "),
				"rating_period_length": input_integer("Rating period length (seconds): ", False),
				"rating_phi_increase_rate": input_integer("Rating increase rate: ", False),
				"matchmaking_message_channel": input_integer("Matchmaking message receiving reactions's channel ID: ", False),
				"matchmaking_message_id": input_integer("Matchmaking message receiving reactions's ID: ", False),
				"matchmaking_announcement_channel": input_integer("Matchmaking announcement channel ID: ", False),
				"matchmaking_platforms": [
					["pc", 0, input_integer("PC matchmaking emoji ID: ", False)],
					["switch", 1, input_integer("Switch matchmaking emoji ID: ", False)],
					["ps4", 2, input_integer("PlayStation 4 matchmaking emoji ID: ", False)]
				],
				"pending_match_lifetime": input_integer("Time limit to finish a match (seconds): "),
				"rank_roles": [
					["Bronze", 0, input_integer("Bronze rank role ID: ", False)],
					["Silver", 1, input_integer("Silver rank role ID: ", False)],
					["Gold", 2, input_integer("Gold rank role ID: ", False)],
					["Platinum", 3, input_integer("Platinum rank role ID: ", False)],
					["Diamond", 4, input_integer("Diamond rank role ID: ", False)],
					["Legend", 4, input_integer("Legend rank role ID: ", False)],
					["[In placements.]", -1, input_integer("Placements rank role ID: ", False)]
				]
			}
			json.dump(data, file_obj, indent='\t')
