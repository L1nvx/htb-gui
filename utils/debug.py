"""
Debug utilities for HTB Client.
Provides logging and debugging helpers.
"""

import json
from datetime import datetime
from typing import Any, Optional

from config import config


def debug_log(category: str, message: str, data: Any = None):
    """
    Log a debug message with timestamp and category.
    
    Args:
        category: Log category (e.g., 'API', 'UI', 'CONFIG')
        message: Log message
        data: Optional data to include
    """
    if not config.debug:
        return
    
    timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
    print(f"[{timestamp}] [{category}] {message}")
    
    if data is not None:
        try:
            if isinstance(data, (dict, list)):
                formatted = json.dumps(data, indent=2, ensure_ascii=False)
                # Limit output for large responses
                if len(formatted) > 1000:
                    formatted = formatted[:1000] + "\n... (truncated)"
                print(formatted)
            else:
                print(f"  → {data}")
        except Exception as e:
            print(f"  → (could not format data: {e})")


def debug_request(method: str, url: str, data: Optional[dict] = None):
    """Log an outgoing HTTP request."""
    debug_log("API", f"→ {method} {url}")
    if data:
        debug_log("API", "Request body:", data)


def debug_response(status_code: int, url: str, data: Any = None, error: str = None):
    """Log an HTTP response."""
    if error:
        debug_log("API", f"← ERROR {status_code} {url}: {error}")
    else:
        debug_log("API", f"← {status_code} {url}")
        if data:
            debug_log("API", "Response:", data)
