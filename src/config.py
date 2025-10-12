import os
from dotenv import load_dotenv

load_dotenv()

# Configuração do modelo de IA a ser usado
AI_MODEL = os.getenv("AI_MODEL", "gemini").lower().strip()

# Configurações do Gemini
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")

# Configurações do OpenAI GPT
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
GPT_MODEL = os.getenv("GPT_MODEL", "gpt-4o-mini")

# Configurações do DeepSeek
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")
DEEPSEEK_MODEL = os.getenv("DEEPSEEK_MODEL", "deepseek-chat")

# Outras configurações
INPUT_DIR_DEFAULT = os.getenv("INPUT_DIR", "lerpdf")
OUTPUT_DIR_DEFAULT = os.getenv("OUTPUT_DIR", "out")
MAX_QUEST_PER_BLOCK = int(os.getenv("MAX_QUEST_PER_BLOCK", "30"))
RATE_LIMIT_PER_MINUTE = int(os.getenv("RATE_LIMIT_PER_MINUTE", "30"))

# Configurações de processamento paralelo
MAX_PARALLEL_WORKERS = int(os.getenv("MAX_PARALLEL_WORKERS", "4"))  # Máximo de threads paralelas
ENABLE_DESKTOP_COPY = os.getenv("ENABLE_DESKTOP_COPY", "true").lower() == "true"  # Copiar para área de trabalho
