"""Utility to truncate all tables in the configured database."""
import mysql.connector as m
from config import settings as s

def main() -> None:
    conn = m.connect(
        host=s.DB_HOST,
        user=s.DB_USER,
        password=s.DB_PASSWORD,
        database=s.DB_NAME,
        port=s.DB_PORT,
    )
    cur = conn.cursor()
    cur.execute("SET FOREIGN_KEY_CHECKS=0")
    cur.execute(
        "SELECT table_name FROM information_schema.tables WHERE table_schema=%s",
        (s.DB_NAME,),
    )
    tables = [r[0] for r in cur.fetchall()]
    for table in tables:
        cur.execute(f"TRUNCATE TABLE `{s.DB_NAME}`.`{table}`")
    conn.commit()
    cur.execute("SET FOREIGN_KEY_CHECKS=1")
    cur.close()
    conn.close()
    print(f"OK: {len(tables)} tables vidées dans {s.DB_NAME}.")


if __name__ == "__main__":
    main()
