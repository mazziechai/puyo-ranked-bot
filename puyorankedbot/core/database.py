import sqlite3, datetime, asyncio
from config import get_config
from core import utils

sqlite3.register_converter(
	"DATETIME",
	lambda s: datetime.datetime.strptime(s.decode("ascii"), "%Y-%m-%d %H:%M:%S")
)

sqlite3.register_adapter(
	datetime.datetime,
	lambda d: d.strftime("%Y-%m-%d %H:%M:%S")
)

class Row:
	"""
	A converted database row for easy access of the values through different ways.
	"""
	def __init__(self, dict_in, tuple_in):
		self.dict = dict_in
		self.tuple = tuple_in
	def __getitem__(self, key):
		"""
		The handler for the subscript operator [], allows access both
		by string key and by integer index.
		"""
		return self.tuple[key] if isinstance(key, int) else self.dict[key]

def row_factory(cursor, row):
	d = {}
	for index, column in enumerate(cursor.description):
		d[column[0]] = row[index]
	return Row(d, tuple(row))

database = sqlite3.connect("../data.db3", detect_types=sqlite3.PARSE_DECLTYPES)
database.row_factory = row_factory

backup_running = False

def setup_backup():
	global backup_running
	if backup_running: return
	asyncio.create_task(backup())
	backup_running = True

async def backup():
	interval = get_config("backup_interval")
	while True:
		try:
			destination = sqlite3.connect("../data_backup.db3")
			database.backup(destination)
			destination.close()
			await asyncio.sleep(interval)
		except Exception as e:
			utils.log_error(e)
