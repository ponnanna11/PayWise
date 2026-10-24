"""
Application configuration settings for PayWise.
Loads environment variables for database, currency, and AI runtime integration.
"""
from pathlib import Path
import os
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent.parent

# Database configuration
DB_PATH = os.getenv("PAYWISE_DB_PATH", str(BASE_DIR / "data" / "paywise_sim.db"))
DEFAULT_CURRENCY = os.getenv("PAYWISE_DEFAULT_CURRENCY", "INR")

# AI Integration Configuration
# Check GEMINI_API_KEY, GOOGLE_API_KEY, or PAYWISE_AI_API_KEY
GEMINI_API_KEY = (
    os.getenv("GEMINI_API_KEY")
    or os.getenv("GOOGLE_API_KEY")
    or os.getenv("PAYWISE_AI_API_KEY")
    or ""
)

AI_PROVIDER = os.getenv("PAYWISE_AI_PROVIDER", "gemini" if GEMINI_API_KEY else "fallback")
AI_MODEL = os.getenv("PAYWISE_AI_MODEL", "gemini-2.5-flash")

# Currency symbols
CURRENCY_SYMBOLS = {
    "INR": "₹",
    "USD": "$",
    "EUR": "€",
    "GBP": "£",
}
