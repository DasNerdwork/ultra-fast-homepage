import os
from pathlib import Path
from contextlib import contextmanager
from dotenv import load_dotenv
from psycopg2.pool import ThreadedConnectionPool

load_dotenv(Path(__file__).resolve().parent.parent / ".env")

DB_URL = (
    f"postgresql://{os.getenv('PSQL_USER')}:{os.getenv('PSQL_PASS')}"
    f"@{os.getenv('PSQL_HOST')}:{os.getenv('PSQL_PORT')}/{os.getenv('PSQL_DB')}"
)

pool = ThreadedConnectionPool(minconn=1, maxconn=5, dsn=DB_URL)

@contextmanager
def get_cursor():
    conn = pool.getconn()
    try:
        with conn.cursor() as cur:
            yield cur
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        pool.putconn(conn)