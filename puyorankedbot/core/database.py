import sqlite3, datetime

sqlite3.register_converter(
	"DATETIME",
	lambda s: datetime.datetime.strptime(s.decode("ascii"), "%Y-%m-%d %H:%M:%S")
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
