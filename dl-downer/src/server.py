from loguru import logger
import time

from .models.dl_request_platform import DLRequestPlatform
from .models.dl_request_status import DLRequestStatus
from .models.dl_request import DLRequest

def start_server():
  ''' Start the server '''

  logger.info('Starting server...')
  from dotenv import load_dotenv
  load_dotenv()
  logger.info('Loaded environment variables')

  logger.info('Validating server structure...')
  from .utils.validate_server_structure import validate_server_structure
  validate_server_structure()
  logger.info('Server structure validated')

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
      logger.info(f'Downloading {dl_request.video_page_or_manifest_url} from {dl_request.platform} ...')

      try:
        if dl_request.platform == DLRequestPlatform.VRTMAX.value:
          from .downloaders.VRTMAX import VRTMAX_DL
          VRTMAX_DL(dl_request)

        elif dl_request.platform == DLRequestPlatform.GOPLAY.value:
          from .downloaders.GOPLAY import GOPLAY_DL
          GOPLAY_DL(dl_request)
        else:
          logger.error(f'Unsupported platform: {dl_request.platform}')
          # throw error for now
          raise Exception('Unsupported platform')
      
        dl_request.update_status(DLRequestStatus.COMPLETED, db)
        logger.info(f'Downloaded {dl_request.video_page_or_manifest_url} from {dl_request.platform} successfully!')

      except Exception as e:
        dl_request.update_status(DLRequestStatus.FAILED, db)
        logger.error('An error occurred')
        logger.error(e)


    else:
      logger.info('No pending requests found! Sleeping for 1 minute ...')
      # Sleep for 1 minute
      time.sleep(60)
