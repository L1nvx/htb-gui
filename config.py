"""
HTB Client Configuration
Manages API tokens, base URLs, and application settings.
"""

import os
import json
from pathlib import Path
from dotenv import load_dotenv

# Load .env file from the same directory as this module
ENV_FILE = Path(__file__).parent / ".env"
load_dotenv(ENV_FILE)

# Base configuration
BASE_URL = "https://labs.hackthebox.com"
API_V4 = f"{BASE_URL}/api/v4"
API_V5 = f"{BASE_URL}/api/v5"

# Config file location
CONFIG_DIR = Path.home() / ".htb_client"
CONFIG_FILE = CONFIG_DIR / "config.json"

# Debug mode from env or default
DEBUG = os.getenv("HTB_DEBUG", "true").lower() == "true"


class Config:
    """Configuration manager for HTB Client."""
    
    _instance = None
    _api_token: str = ""
    _debug: bool = DEBUG
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._load_config()
        return cls._instance
    
    def _load_config(self):
        """Load configuration from .env file first, then JSON config."""
        # First try to load from .env
        env_token = os.getenv("HTB_API_TOKEN", "")
        if env_token and env_token != "your_token_here":
            self._api_token = env_token
            if self._debug:
                print(f"[DEBUG] Token loaded from .env file")
            return
        
        # Fall back to JSON config
        if CONFIG_FILE.exists():
            try:
                with open(CONFIG_FILE, 'r') as f:
                    data = json.load(f)
                    self._api_token = data.get('api_token', '')
                    self._debug = data.get('debug', DEBUG)
                    if self._debug:
                        print(f"[DEBUG] Config loaded from {CONFIG_FILE}")
            except Exception as e:
                print(f"[ERROR] Failed to load config: {e}")
    
    def _save_config(self):
        """Save configuration to file."""
        try:
            CONFIG_DIR.mkdir(parents=True, exist_ok=True)
            with open(CONFIG_FILE, 'w') as f:
                json.dump({
                    'api_token': self._api_token,
                    'debug': self._debug
                }, f, indent=2)
            if self._debug:
                print(f"[DEBUG] Config saved to {CONFIG_FILE}")
        except Exception as e:
            print(f"[ERROR] Failed to save config: {e}")
    
    @property
    def api_token(self) -> str:
        return self._api_token
    
    @api_token.setter
    def api_token(self, value: str):
        self._api_token = value
        self._save_config()
        if self._debug:
            print(f"[DEBUG] API token updated (length: {len(value)})")
    
    @property
    def debug(self) -> bool:
        return self._debug
    
    @debug.setter
    def debug(self, value: bool):
        self._debug = value
        self._save_config()
        print(f"[DEBUG] Debug mode: {value}")
    
    def is_configured(self) -> bool:
        """Check if API token is configured."""
        return bool(self._api_token)


# Global config instance
config = Config()
