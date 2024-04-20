from enum import Enum

class DLRequestStatus(Enum):
  PENDING = 'PENDING'
  IN_PROGRESS = 'IN_PROGRESS'
  COMPLETED = 'COMPLETED'
  FAILED = 'FAILED'
