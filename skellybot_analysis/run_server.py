import logging
import multiprocessing
import time

import skellybot_analysis
from skellybot_analysis.api.server.server_singleton import create_server_manager
from skellybot_analysis.skellybot_analysis_app.skellybot_analysis_app_state import create_skellybot_analysis_app_state
from skellybot_analysis.system.logging_configuration.configure_logging import configure_logging
from skellybot_analysis.system.logging_configuration.log_test_messages import print_log_level_messages
from skellybot_analysis.system.logging_configuration.logger_builder import LogLevels

logger = logging.getLogger(__name__)
configure_logging(LogLevels.TRACE)

if multiprocessing.current_process().name == "mainprocess":
    print_log_level_messages(logger)
logger.debug(f"Running {skellybot_analysis.__package_name__} package, version: {skellybot_analysis.__version__}, from file: {__file__}")



def run_skellybot_analysis_server(global_kill_flag: multiprocessing.Value):
    server_manager = create_server_manager(global_kill_flag=global_kill_flag)
    server_manager.start_server()
    while server_manager.is_running:
        time.sleep(1)
        if global_kill_flag.value:
            server_manager.shutdown_server()
            break

    logger.info("Server main process ended")


if __name__ == "__main__":

    multiprocessing.freeze_support()
    outer_global_kill_flag = multiprocessing.Value("b", False)
    create_skellybot_analysis_app_state(global_kill_flag=outer_global_kill_flag)
    run_skellybot_analysis_server(outer_global_kill_flag)
    outer_global_kill_flag.value = True
    print("Done!")
