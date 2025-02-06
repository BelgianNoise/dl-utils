import traceback
from loguru import logger
import time

from .models.dl_request_status import DLRequestStatus
from .models.dl_request import DLRequest
from .utils.download_dl_request import download_dl_request
from .utils.validate_server_structure import validate_server_structure

def start_server():
  ''' Start the server '''

  logger.info('Starting server...')
  from dotenv import load_dotenv
  load_dotenv()
  logger.info('Loaded environment variables')

  validate_server_structure()

  from .utils.setup_db_pool import setup_db_pool
  db = setup_db_pool()
  logger.info('Database connection successful')

  while True:
    # Check database for pending download request
    db_conn = db.getconn()
    cursor = db_conn.cursor()
    cursor.execute(
      '''
      SELECT * FROM dl.dl_request
      WHERE status = %s
      ORDER BY created ASC
      LIMIT 1
      ''',
      (DLRequestStatus.PENDING.value,),
    )
    pending_request = cursor.fetchone()
    cursor.close()
    db.putconn(db_conn)

    if pending_request:

      # Create a DLRequest object from the database row
      dl_request = DLRequest.from_db_row(pending_request)
      dl_request.update_status(DLRequestStatus.IN_PROGRESS, db)

      try:
        download_dl_request(dl_request)
        dl_request.update_status(DLRequestStatus.COMPLETED, db)

      except Exception as e:
        dl_request.update_status(DLRequestStatus.FAILED, db)
        # log error and its stacktrace
        logger.error(f'An error occurred: {e}')
        logger.error(traceback.format_exc())


    else:
      logger.info('No pending requests found! Sleeping for 1 minute ...')
      # Sleep for 1 minute
      time.sleep(60)
