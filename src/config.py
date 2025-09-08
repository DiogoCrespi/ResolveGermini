import os
from dotenv import load_dotenv

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")
INPUT_DIR_DEFAULT = os.getenv("INPUT_DIR", "lerpdf")
OUTPUT_DIR_DEFAULT = os.getenv("OUTPUT_DIR", "out")
MAX_QUEST_PER_BLOCK = int(os.getenv("MAX_QUEST_PER_BLOCK", "30"))
RATE_LIMIT_PER_MINUTE = int(os.getenv("RATE_LIMIT_PER_MINUTE", "30"))
