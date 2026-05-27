import os
import mysql.connector
from mysql.connector import pooling, Error

connection_pool = None


def _parse_mysql_url(url):
    """Parse a mysql://user:pass@host:port/dbname URL into a dict."""
    try:
        from urllib.parse import urlparse
        p = urlparse(url)
        return {
            "host": p.hostname,
            "user": p.username,
            "password": p.password or "",
            "database": p.path.lstrip("/"),
            "port": p.port or 3306,
        }
    except Exception as ex:
        print(f"  Warning: could not parse MySQL URL: {ex}")
        return None


def _get_db_config():
    """
    Resolve database connection config with this priority:
    1. MYSQL_PRIVATE_URL (Railway private network URL)
    2. MYSQL_URL (Railway public URL)
    3. DATABASE_URL (generic)
    4. Individual MYSQLHOST / MYSQL_HOST env vars
    5. localhost fallback (local dev only)
    """
    keys = [
        "MYSQLHOST", "MYSQLUSER", "MYSQLPASSWORD", "MYSQLPORT", "MYSQLDATABASE",
        "MYSQL_HOST", "MYSQL_USER", "MYSQL_PASSWORD", "MYSQL_PORT", "MYSQL_DATABASE",
        "MYSQL_PRIVATE_URL", "MYSQL_PUBLIC_URL", "MYSQL_URL", "DATABASE_URL",
        "RAILWAY_ENVIRONMENT", "RAILWAY_PROJECT_ID", "PORT", "RENDER",
    ]
    print("=== DB ENV DIAGNOSTICS ===")
    for k in keys:
        val = os.getenv(k)
        if val:
            masked = val if "PASS" not in k else "***"
            print(f"  {k}={masked}")
        else:
            print(f"  {k}=(not set)")

    # 1. Prefer Railway private URL (no egress fees)
    for url_key in ("MYSQL_PRIVATE_URL", "MYSQL_URL", "DATABASE_URL"):
        raw_url = os.getenv(url_key, "")
        if raw_url and ("mysql" in raw_url or "mariadb" in raw_url):
            cfg = _parse_mysql_url(raw_url)
            if cfg:
                print(f"  [Using URL from {url_key}] host={cfg['host']} db={cfg['database']}")
                return cfg

    # 2. Individual env vars (Railway reference variables like ${{MySQL.MYSQLHOST}})
    host = (os.getenv("MYSQLHOST") or os.getenv("MYSQL_HOST") or
            os.getenv("DB_HOST") or "localhost")
    user = (os.getenv("MYSQLUSER") or os.getenv("MYSQL_USER") or
            os.getenv("DB_USER") or "root")
    password = (os.getenv("MYSQLPASSWORD") or os.getenv("MYSQL_PASSWORD") or
                os.getenv("DB_PASSWORD") or "")
    database = (os.getenv("MYSQLDATABASE") or os.getenv("MYSQL_DATABASE") or
                os.getenv("DB_NAME") or "railway")
    port = int(os.getenv("MYSQLPORT") or os.getenv("MYSQL_PORT") or
               os.getenv("DB_PORT") or 3306)

    cfg = {"host": host, "user": user, "password": password,
           "database": database, "port": port}
    print(f"  [Using individual vars] host={host} port={port} user={user} db={database}")
    return cfg


def init_pool():
    global connection_pool
    cfg = _get_db_config()
    print(f"=== CONNECTING: host={cfg['host']} port={cfg['port']} user={cfg['user']} db={cfg['database']} ===")
    try:
        connection_pool = pooling.MySQLConnectionPool(
            pool_name="bank_pool",
            pool_size=3,
            pool_reset_session=True,
            host=cfg["host"],
            user=cfg["user"],
            password=cfg["password"],
            database=cfg["database"],
            port=cfg["port"],
        )
        print("✓ Database connection pool created successfully.")
        run_migrations()
    except Error as e:
        print(f"✗ Error creating connection pool: {e}")
        import traceback
        traceback.print_exc()
        raise


def run_migrations():
    import os
    schema_path = os.path.join(os.path.dirname(__file__), "schema.sql")
    if not os.path.exists(schema_path):
        return
    with open(schema_path, "r", encoding="utf-8") as f:
        sql = f.read()

    queries = sql.split(";")
    conn = get_connection()
    cursor = conn.cursor()
    try:
        for query in queries:
            clean_query = query.strip()
            if clean_query:
                # Skip administrative database creation/selection commands on hosted platforms
                if clean_query.upper().startswith("CREATE DATABASE") or clean_query.upper().startswith("USE "):
                    continue

                # Replace password placeholder with a real hashed admin password if needed
                if "$2b$12$placeholder" in clean_query:
                    import bcrypt
                    admin_hash = bcrypt.hashpw(b"admin123", bcrypt.gensalt()).decode()
                    clean_query = clean_query.replace("$2b$12$placeholder", admin_hash)
                
                try:
                    cursor.execute(clean_query)
                except Error as e:
                    print(f"Migration Query Warning: {e} for query: {clean_query[:50]}")
                    pass
        conn.commit()
    except Error as e:
        print(f"Warning: Migration execution error: {e}")
    finally:
        cursor.close()
        conn.close()



def get_connection():
    global connection_pool
    if connection_pool is None:
        init_pool()
    return connection_pool.get_connection()


def execute_query(query, params=None, fetch_one=False, fetch_all=False, commit=False):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute(query, params or ())
        if commit:
            conn.commit()
            return cursor.lastrowid
        if fetch_one:
            return cursor.fetchone()
        if fetch_all:
            return cursor.fetchall()
    except Error as e:
        if commit:
            conn.rollback()
        raise e
    finally:
        cursor.close()
        conn.close()


def execute_transaction(queries_and_params):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        for query, params in queries_and_params:
            cursor.execute(query, params or ())
        conn.commit()
        return True
    except Error as e:
        conn.rollback()
        raise e
    finally:
        cursor.close()
        conn.close()
