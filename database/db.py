import os
import psycopg2
import psycopg2.pool
import psycopg2.extras
from config import Config

_pool = None


def init_pool():
    global _pool
    url = Config.DATABASE_URL
    if not url:
        raise RuntimeError(
            "DATABASE_URL is not set. "
            "Add it to Railway Variables or your .env file.\n"
            "Format: postgresql://user:password@host:port/dbname"
        )
    # Mask password in log
    safe_url = url.split("@")[-1] if "@" in url else url
    print(f"=== Connecting to PostgreSQL: {safe_url} ===")
    try:
        _pool = psycopg2.pool.ThreadedConnectionPool(
            minconn=1,
            maxconn=5,
            dsn=url,
            connect_timeout=10,
        )
        print("PostgreSQL connection pool created.")
        run_migrations()
    except Exception as e:
        print(f"Failed to connect to PostgreSQL: {e}")
        import traceback
        traceback.print_exc()
        raise


def run_migrations():
    import os as _os
    schema_path = _os.path.join(_os.path.dirname(__file__), "schema.sql")
    if not _os.path.exists(schema_path):
        print("  No schema.sql found - skipping migrations.")
        return
    with open(schema_path, "r", encoding="utf-8") as f:
        sql = f.read()

    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute(sql)
        conn.commit()
        print("Migrations applied successfully.")
    except Exception as e:
        conn.rollback()
        print(f"Migration warning: {e}")
    finally:
        cur.close()
        release_connection(conn)


def get_connection():
    global _pool
    if _pool is None:
        init_pool()
    return _pool.getconn()


def release_connection(conn):
    global _pool
    if _pool and conn:
        _pool.putconn(conn)


def execute_query(query, params=None, fetch_one=False, fetch_all=False, commit=False):
    conn = get_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    try:
        exec_query = query.strip()

        # PostgreSQL needs RETURNING id to get the last inserted row id
        is_insert = exec_query.upper().startswith("INSERT")
        if commit and is_insert and "RETURNING" not in exec_query.upper():
            exec_query = exec_query.rstrip(";") + " RETURNING id"

        cur.execute(exec_query, params or ())

        if commit:
            conn.commit()
            if is_insert:
                row = cur.fetchone()
                return row["id"] if row else None
            return None
        if fetch_one:
            return cur.fetchone()
        if fetch_all:
            return cur.fetchall()
    except Exception as e:
        if commit:
            conn.rollback()
        raise e
    finally:
        cur.close()
        release_connection(conn)


def execute_transaction(queries_and_params):
    conn = get_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    try:
        for query, params in queries_and_params:
            cur.execute(query, params or ())
        conn.commit()
        return True
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        cur.close()
        release_connection(conn)
