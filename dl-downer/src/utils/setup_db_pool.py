import psycopg2.pool 
import os
from loguru import logger

def setup_db_pool() -> psycopg2.pool.SimpleConnectionPool:
  ''' Set up a connection pool for the database '''

  # Make sure all env variables are set
  assert os.getenv('POSTGRES_USERNAME') is not None
  assert os.getenv('POSTGRES_PASSWORD') is not None
  assert os.getenv('POSTGRES_HOST') is not None
  assert os.getenv('POSTGRES_PORT') is not None
  assert os.getenv('POSTGRES_DATABASE') is not None

  # Create a connection pool with a minimum of 2 connections and 
  #a maximum of 3 connections 
  pool = psycopg2.pool.SimpleConnectionPool(0, 2,
    user=os.getenv('POSTGRES_USERNAME'),
    password=os.getenv('POSTGRES_PASSWORD'), 
    host=os.getenv('POSTGRES_HOST'),
    port=os.getenv('POSTGRES_PORT'),
    database=os.getenv('POSTGRES_DATABASE')
  )

  # Test the connection pool
  conn = pool.getconn()
  cur = conn.cursor()
  cur.execute('SELECT id FROM dl.dl_request LIMIT 1')
  cur.fetchall()
  cur.close()
  pool.putconn(conn)

  logger.info('Database connection pool created')
  
  return pool
  