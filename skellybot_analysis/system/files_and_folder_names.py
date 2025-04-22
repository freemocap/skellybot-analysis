from datetime import datetime
from pathlib import Path
from time import time


def get_skellybot_analysis_data_folder_path() -> str:
    path  =  Path().home() / "Sync" / "skellybot-data" / "skellybot-analysis"
    path.mkdir(parents=True, exist_ok=True)
    return str(path)

def get_gmt_offset_string():
    # from - https://stackoverflow.com/a/53860920/14662833
    gmt_offset_int = int(time.localtime().tm_gmtoff / 60 / 60)
    return f"{gmt_offset_int:+}"


def create_log_file_name():
    return "skellybot_analysis_" + time.strftime("%Y-%m-%d_%H_%M_%S") + ".log"

def get_log_file_path():
    log_folder_path = Path(get_skellybot_analysis_data_folder_path()) / 'logs'
    log_folder_path.mkdir(exist_ok=True, parents=True)
    log_file_path = log_folder_path / create_log_file_name()
    return str(log_file_path)