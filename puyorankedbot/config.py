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
	if os.path.exists("config.json"):
		with open("config.json", "r") as file_obj:
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
	if os.path.exists("config.json"):
		with open("config.json", "r") as file_obj:
			json_obj = json.load(file_obj)
		json_obj[key] = value
		with open("config.json", "w") as file_obj:
			json.dump(json_obj, file_obj)
	else:
		raise ConfigNotFoundException("config.json is missing")


def create_config():
	"""
	Creates a configuration file after prompting the user for the values
	if the configuration file does not exist.
	:return: None
	"""
	if os.path.exists("config.json"):
		return
	else:
		with open("config.json", "w") as file_obj:
			token = input("Please enter the token: ")
			spreadsheet_id = input("Please enter the Google spreadsheet ID: ")
			service_account_file = input("Please enter the Google service account file: ")
			data = {
				"token": token,
				"spreadsheet_id": spreadsheet_id,
				"service_account_file": service_account_file,
				"match_count": 0
			}
			json.dump(data, file_obj)
