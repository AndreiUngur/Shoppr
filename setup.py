from sqlalchemy import create_engine, exc
import tables
from utils import db

engine = create_engine("mysql://localhost/mysql")

conn = engine.connect()
conn.execute("COMMIT")
try:
    conn.execute("CREATE DATABASE shopprdata")
except exc.ProgrammingError:
    print("exists")
conn.close()

db.create_all()
