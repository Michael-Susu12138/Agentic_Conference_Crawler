"""
Configuration settings for the Conference Monitor Agent
"""
import os
from pathlib import Path

# API Keys (load from environment variables for security)
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")
SEMANTIC_SCHOLAR_API_KEY = os.environ.get("SEMANTIC_SCHOLAR_API_KEY", "")

# File paths
ROOT_DIR = Path(__file__).parent.parent
DATA_DIR = ROOT_DIR / "data"
os.makedirs(DATA_DIR, exist_ok=True)

# Conference search settings
DEFAULT_CONFERENCE_SOURCES = [
    "https://www.ieee.org/conferences/index.html",
    "https://www.acm.org/conferences",
    "https://aclweb.org/conference",
    "https://www.neurips.cc/",
]

# Default research areas to track
DEFAULT_RESEARCH_AREAS = [
    "artificial intelligence",
    "machine learning",
    "natural language processing",
    "computer vision",
]

# User settings
DEFAULT_REFRESH_INTERVAL_DAYS = 7  # How often to check for updates
MAX_PAPERS_PER_QUERY = 50
MAX_CONFERENCES_TO_TRACK = 20

# LLM Settings
DEFAULT_LLM_MODEL = "gpt-4" 
DEFAULT_EMBEDDING_MODEL = "text-embedding-3-small" 