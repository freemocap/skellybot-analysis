import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

DISCORD_DEV_BOT_TOKEN = os.getenv('DISCORD_DEV_BOT_TOKEN')
DISCORD_DEV_BOT_ID = os.getenv('DISCORD_DEV_BOT_ID')
DISCORD_BOT_ID = os.getenv('DISCORD_BOT_ID')
TARGET_SERVER_ID = os.getenv('TARGET_SERVER_ID')
OUTPUT_DIRECTORY = os.getenv('OUTPUT_DIRECTORY')
STUDENT_IDENTIFIERS_CSV_PATH = os.getenv('STUDENT_IDENTIFIERS_CSV_PATH')

OUTPUT_DIRECTORY = OUTPUT_DIRECTORY.replace("~", str(Path.home()))

# Ensure the environment variables are set
if not DISCORD_DEV_BOT_TOKEN:
    raise ValueError("Please set DISCORD_DEV_BOT_TOKEN in your .env file")
if not DISCORD_DEV_BOT_ID:
    raise ValueError("Please set DISCORD_DEV_BOT_ID in your .env file")
if not TARGET_SERVER_ID:
    raise ValueError("Please set TARGET_SERVER_ID in your .env file")
if not OUTPUT_DIRECTORY:
    raise ValueError("Please set OUTPUT_DIRECTORY in your .env file")
if not STUDENT_IDENTIFIERS_CSV_PATH:
    raise ValueError("Please set STUDENT_IDENTIFIERS_CSV_PATH in your .env file")

