from enum import Enum


class DLRequestPlatform(Enum):
    VRTMAX = "VRTMAX"
    VTMGO = "VTMGO"
    STREAMZ = "STREAMZ"
    GOPLAY = "GOPLAY"
    YOUTUBE = "YOUTUBE"
    GENERIC_MANIFEST = "GENERIC_MANIFEST"
    UNKNOWN = "UNKNOWN"
