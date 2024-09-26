from config.config import DB_URL
from database.db_interface import DBInterface, ConfigInterface

db = DBInterface(DB_URL)
dbconf = ConfigInterface(DB_URL)