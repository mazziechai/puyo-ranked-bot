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
			token = input("Bot token: ")
			bot_prefix = input("Bot prefix: ")
			data = {
				"token": token,
				"bot_prefix": bot_prefix
			}
			json.dump(data, file_obj)
