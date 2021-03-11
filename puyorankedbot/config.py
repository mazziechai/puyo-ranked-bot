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
	while True:
		try:
			s = input(prompt)
			i = int(s)
			if allow_non_positive or i > 0:
				return i
		except ValueError:
			pass
		print("The input must be a positive integer.")

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
				"rating_period_start": input_integer("Rating period 0 start point (POSIX timestamp, seconds): "),
				"rating_period_length": input_integer("Rating period length (seconds): ", False),
				"rating_phi_increase_rate": input_integer("Rating increase rate: ", False)
			}
			json.dump(data, file_obj, indent='\t')
