# This module handles the automatic update of player ratings
# when a rating period passes.

import asyncio
import json
import os
from datetime import datetime
from logger import logger
from config import get_config
from core.database import database
from core import utils

running = False

def setup():
	global running
	if running: return
	asyncio.create_task(update_loop())
	running = True

async def update_ratings(c):
	feed_in = database.execute("SELECT rowid, id, platforms, rating_mu, rating_phi FROM players")
	feed_out = database.cursor()
	while True:
		batch = feed_in.fetchmany(1024)
		if len(batch) == 0: break
		data_load = []
		for player in batch:
			mu = player[3]
			old_phi = player[4]
			new_phi = min(350, (old_phi**2 + c)**0.5)
			if player[2] != "":
				await utils.update_role(player[1], mu, old_phi, mu, new_phi)
			data_load.append((new_phi, player[0]))
		feed_out.executemany(
			"UPDATE players SET rating_phi = ? WHERE rowid = ?",
			data_load
		)
	database.commit()

file_name = "../rating_period_info.json"

def save_period_info(period_info):
	with open(file_name, "w") as f: json.dump(period_info, f)

async def update_loop():
	start = get_config("rating_period_start")
	length = get_config("rating_period_length")
	c = get_config("rating_phi_increase_rate")
	period = (int(datetime.now().timestamp()) - start) // length

	if os.path.exists(file_name):
		with open(file_name) as f: period_info = json.load(f)
		if period_info["start"] != start or period_info["length"] != length:
			logger.warning("Rating period parameters changed. The current period will be skipped (no updates).")
			period_info["start"] = start
			period_info["length"] = length
			period_info["period"] = period
			save_period_info(period_info)
		elif period_info["period"] != period:
			await update_ratings((period - period_info["period"]) * c)
			period_info["period"] = period
			save_period_info(period_info)
	else:
		logger.info("Rating period information file not found, assuming initial setup.")
		period_info = {
			"start": start,
			"length": length,
			"period": period
		}
		save_period_info(period_info)

	next_update = start + (period+1)*length
	while True:
		try:
			await asyncio.sleep(next_update - int(datetime.now().timestamp()))
			await update_ratings(c)
			period += 1
			period_info["period"] = period
			save_period_info(period_info)
			next_update += length
		except Exception as e:
			utils.log_error(e)
