from openai import AsyncOpenAI

from skellybot_analysis.utilities.load_env_variables import OPENAI_API_KEY

OPENAI_CLIENT = AsyncOpenAI(api_key=OPENAI_API_KEY)
DEFAULT_LLM = "gpt-4o-mini"
MAX_TOKEN_LENGTH = int(128_000 * .9)
