from sqlalchemy import create_engine

engine = create_engine("mysql://localhost/mysql")
conn = engine.connect()
conn.execute("COMMIT")
conn.execute("CREATE DATABASE shopprdata")
conn.close()
