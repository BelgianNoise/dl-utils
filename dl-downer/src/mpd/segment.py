
class Segment:
  def __init__(self, start: int, duration: int):
    self.start = start
    self.duration = duration
  def __str__(self):
    return f'<Segment(start={self.start}, duration={self.duration})>'
  def __repr__(self):
    return self.__str__()
