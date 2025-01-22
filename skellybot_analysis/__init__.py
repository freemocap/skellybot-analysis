"""The analysis backend for Skellybot (github.com/freemocap/skellybot)."""

__author__ = """Skelly SkellybotAnalysis"""
__email__ = "info@freemocap.org"
__version__ = "v0.1.0"
__description__ = "The analysis backend for Skellybot (github.com/freemocap/skellybot)."

__package_name__ = "skellybot_analysis"
__repo_url__ = f"https://github.com/freemocap/{__package_name__}/"
__repo_issues_url__ = f"{__repo_url__}issues"

from skellybot_analysis.system.logging_configuration.configure_logging import configure_logging
from skellybot_analysis.system.logging_configuration.logger_builder import LogLevels

configure_logging(LogLevels.TRACE)