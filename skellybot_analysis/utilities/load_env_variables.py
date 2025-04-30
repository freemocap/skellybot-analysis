import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

DISCORD_DEV_BOT_TOKEN = os.getenv('DISCORD_DEV_BOT_TOKEN')
DISCORD_DEV_BOT_ID = int(os.getenv('DISCORD_DEV_BOT_ID'))
DISCORD_BOT_ID = int(os.getenv('DISCORD_BOT_ID'))
PROF_USER_ID = int(os.getenv('PROF_USER_ID'))
TARGET_SERVER_ID = int(os.getenv('TARGET_SERVER_ID'))
OUTPUT_DIRECTORY = os.getenv('OUTPUT_DIRECTORY')
STUDENT_IDENTIFIERS_CSV_PATH = os.getenv('STUDENT_IDENTIFIERS_CSV_PATH')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

OUTPUT_DIRECTORY = OUTPUT_DIRECTORY.replace("~", str(Path.home()))

# Ensure the environment variables are set
if not DISCORD_DEV_BOT_TOKEN:
    raise ValueError("Please set DISCORD_DEV_BOT_TOKEN in your .env file")
if not DISCORD_DEV_BOT_ID:
    raise ValueError("Please set DISCORD_DEV_BOT_ID in your .env file")
if not DISCORD_BOT_ID:
    raise ValueError("Please set DISCORD_BOT_ID in your .env file")
if not PROF_USER_ID:
    raise ValueError("Please set PROF_USER_ID in your .env file")
if not TARGET_SERVER_ID:
    raise ValueError("Please set TARGET_SERVER_ID in your .env file")
if not OUTPUT_DIRECTORY:
    raise ValueError("Please set OUTPUT_DIRECTORY in your .env file")
if not STUDENT_IDENTIFIERS_CSV_PATH:
    raise ValueError("Please set STUDENT_IDENTIFIERS_CSV_PATH in your .env file")
if not OPENAI_API_KEY:
    raise ValueError("Please set OPENAI_API_KEY in your .env file")
