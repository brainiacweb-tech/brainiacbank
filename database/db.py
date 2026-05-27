import mysql.connector
from mysql.connector import pooling, Error
from config import Config

connection_pool = None


def init_pool():
    global connection_pool
    try:
        connection_pool = pooling.MySQLConnectionPool(
            pool_name="bank_pool",
            pool_size=10,
            pool_reset_session=True,
            host=Config.MYSQL_HOST,
            user=Config.MYSQL_USER,
            password=Config.MYSQL_PASSWORD,
            database=Config.MYSQL_DATABASE,
            port=Config.MYSQL_PORT,
        )
        run_migrations()
    except Error as e:
        print(f"Error creating connection pool: {e}")
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
