import os

os.environ["AUTH_VRTMAX_EMAIL"] = ""
os.environ["AUTH_VRTMAX_PASSWORD"] = ""
os.environ["AUTH_GOPLAY_EMAIL"] = ""
os.environ["AUTH_GOPLAY_PASSWORD"] = ""
os.environ["AUTH_VTMGO_EMAIL"] = ""
os.environ["AUTH_VTMGO_PASSWORD"] = ""

os.environ["CDM_FILE_PATH"] = "./cdm/cdm.wvd"
os.environ["STORAGE_STATES_FOLDER"] = "./storage_states"
os.environ["DOWNLOADS_FOLDER"] = "./downloads"

# Do not touch if unsure
os.environ["DL_GOPLAY_MERGE_METHOD"] = "format"
os.environ["HEADLESS"] = "true"

from src.handle_cli import handle_cli
handle_cli()
