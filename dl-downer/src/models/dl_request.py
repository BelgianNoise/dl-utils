from datetime import datetime

from ..models.dl_request_status import DLRequestStatus

class DLRequest:
  ''' Represents a download request '''

  def __init__(
    self,
    id,
    status,
    platform,
    video_page_or_manifest_url,
    created,
    updated,
    output_filename,
    preferred_quality_matcher):
    self.id = id
    self.status = status
    self.platform = platform
    self.video_page_or_manifest_url = video_page_or_manifest_url
    self.created = created
    self.updated = updated
    self.output_filename = output_filename
    self.preferred_quality_matcher = preferred_quality_matcher

  def __repr__(self):
    return f'<DLRequest {self.id} {self.platform} {self.video_page_or_manifest_url}>'
  
  @classmethod
  def from_db_row(cls, row):
    ''' Create a DLRequest object from a database row '''
    return cls(
      id=row[0],
      status=row[1],
      platform=row[2],
      video_page_or_manifest_url=row[3],
      created=row[4],
      updated=row[5],
      output_filename=row[6],
      preferred_quality_matcher=row[7],
    )
  
  def to_dict(self):
    ''' Convert DLRequest object to dictionary '''
    return {
      'id': self.id,
      'status': self.status,
      'platform': self.platform,
      'video_page_or_manifest_url': self.video_page_or_manifest_url,
      'created': self.created,
      'updated': self.updated,
      'output_filename': self.output_filename,
      'preferred_quality_matcher': self.preferred_quality_matcher,
    }
  
  def to_db_row(self):
    ''' Convert DLRequest object to database row '''
    return (
      self.id,
      self.status,
      self.platform,
      self.video_page_or_manifest_url,
      self.created,
      self.updated,
      self.output_filename,
      self.preferred_quality_matcher,
    )
  
  def update_status(self, new_status: DLRequestStatus, db):
    ''' Update the status of the DLRequest in the database '''
    db_conn = db.getconn()
    cursor = db_conn.cursor()
    cursor.execute(
      '''
      UPDATE dl.dl_request
      SET status = %s, updated = NOW()
      WHERE id = %s
      ''',
      (new_status.value, self.id),
    )
    db_conn.commit()
    cursor.close()
    db.putconn(db_conn)
    self.status = new_status
    self.updated = datetime.now()
