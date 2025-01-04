import logging
import multiprocessing
from dataclasses import dataclass


logger = logging.getLogger(__name__)


@dataclass
class SkellybotAnalysisAppState:
    global_kill_flag: multiprocessing.Value
    ipc_queue: multiprocessing.Queue

    @classmethod
    def create(cls, global_kill_flag: multiprocessing.Value):

        return cls(global_kill_flag=global_kill_flag,
                     ipc_queue=multiprocessing.Queue()
                     )


    def close(self):
        self.global_kill_flag.value = True



SKELLYBOT_ANALYSIS_APP_STATE: SkellybotAnalysisAppState | None = None


def create_skellybot_analysis_app_state(global_kill_flag: multiprocessing.Value) -> SkellybotAnalysisAppState:
    global SKELLYBOT_ANALYSIS_APP_STATE
    if SKELLYBOT_ANALYSIS_APP_STATE is None:
        SKELLYBOT_ANALYSIS_APP_STATE = SkellybotAnalysisAppState.create(global_kill_flag=global_kill_flag)
    else:
        raise ValueError("SkellyBotAnalysis already exists!")
    return SKELLYBOT_ANALYSIS_APP_STATE


def get_skellybot_analysis_app_state() -> SkellybotAnalysisAppState:
    global SKELLYBOT_ANALYSIS_APP_STATE
    if SKELLYBOT_ANALYSIS_APP_STATE is None:
        raise ValueError("SkellyBotAnalysis does not exist!")
    return SKELLYBOT_ANALYSIS_APP_STATE
