"""
Application configuration settings for PayWise.
Loads environment variables for database, currency, and AI runtime integration.
"""
from pathlib import Path
import os
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent.parent

def _get_setting(key: str, default: str = "") -> str:
    """Retrieve setting from Streamlit secrets (cloud) or environment variables (local)."""
    try:
        import streamlit as st
        if hasattr(st, "secrets") and key in st.secrets:
            return str(st.secrets[key])
    except Exception:
        pass
    return os.getenv(key, default)


# Database configuration
DB_PATH = _get_setting("PAYWISE_DB_PATH", str(BASE_DIR / "data" / "paywise_sim.db"))
DEFAULT_CURRENCY = _get_setting("PAYWISE_DEFAULT_CURRENCY", "INR")

# AI Integration Configuration
# Check GEMINI_API_KEY, GOOGLE_API_KEY, or PAYWISE_AI_API_KEY
GEMINI_API_KEY = (
    _get_setting("GEMINI_API_KEY")
    or _get_setting("GOOGLE_API_KEY")
    or _get_setting("PAYWISE_AI_API_KEY")
    or ""
)

AI_PROVIDER = _get_setting("PAYWISE_AI_PROVIDER", "gemini" if GEMINI_API_KEY else "fallback")
AI_MODEL = _get_setting("PAYWISE_AI_MODEL", "gemini-2.5-flash")

# Currency symbols
CURRENCY_SYMBOLS = {
    "INR": "₹",
    "USD": "$",
    "EUR": "€",
    "GBP": "£",
}
