import os
from dotenv import load_dotenv

load_dotenv()

PORT = int(os.getenv("PORT", "8001"))
PUBLIC_URL = os.getenv("PUBLIC_URL", f"http://localhost:{PORT}")
ALLOCATION_AGENT_URL = os.getenv("ALLOCATION_AGENT_URL", "http://localhost:8002")
CREDIT_AGENT_URL = os.getenv("CREDIT_AGENT_URL", "http://localhost:8003")
USE_MOCK_LLM = os.getenv("USE_MOCK_LLM", "true").lower() in ("1", "true", "yes") or not os.getenv("OPENAI_API_KEY")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
