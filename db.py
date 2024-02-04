import psycopg2
import time
from logger import logger
from dotenv import load_dotenv
import os

load_dotenv()

DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")


def get_connection():
    """
    Returns a connection to the database.

    If the connection fails, it will retry 5 times before exiting.
    """
    # Retry 5 times
    for _ in range(5):
        try:
            conn = psycopg2.connect(
                host=DB_HOST,
                port=DB_PORT,
                dbname=DB_NAME,
                user=DB_USER,
                password=DB_PASSWORD,
            )
            return conn
        except Exception as e:
            logger.warning(f"Failed to connect to database: {e}, retrying...")
            time.sleep(1)
    raise Exception("Failed to connect to database")


def close_connection():
    conn.close()


def query_db(query, params=None, commit=False, fetchall=False):
    """
    Executes a query. Commits the transaction if commit=True.
    """
    conn = get_connection()
    with conn.cursor() as cursor:
        cursor.execute(query, params)
        if commit:
            conn.commit()
        if fetchall:
            return cursor.fetchall()


try:
    conn = get_connection()
except Exception as e:
    logger.fatal(f"Failed to connect to database: {e}")
    exit(1)
