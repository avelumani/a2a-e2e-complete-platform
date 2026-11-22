import os
from dotenv import load_dotenv

load_dotenv()

PORT = int(os.getenv("PORT", "8000"))
PUBLIC_URL = os.getenv("PUBLIC_URL", f"http://localhost:{PORT}")
TRIAGE_AGENT_URL = os.getenv("TRIAGE_AGENT_URL", "http://localhost:8001")
SQUAD_NAME = os.getenv("SQUAD_NAME", "Order-to-Cash Platform Squad")
USE_MOCK_LLM = os.getenv("USE_MOCK_LLM", "true").lower() in ("1", "true", "yes") or not os.getenv("OPENAI_API_KEY")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
