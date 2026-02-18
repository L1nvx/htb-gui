"""
Image Cache Module
Caches downloaded images to /tmp for faster loading.
"""

import os
import hashlib
from pathlib import Path
from typing import Optional
from PySide6.QtGui import QPixmap
from PySide6.QtCore import QByteArray

CACHE_DIR = Path("/tmp/htb_client_cache/images")


def _ensure_cache_dir():
    """Create cache directory if it doesn't exist."""
    CACHE_DIR.mkdir(parents=True, exist_ok=True)


def _get_cache_path(url: str) -> Path:
    """Get cache file path for a URL."""
    url_hash = hashlib.md5(url.encode()).hexdigest()
    return CACHE_DIR / f"{url_hash}.png"


def get_cached_image(url: str) -> Optional[QPixmap]:
    """
    Get image from cache if it exists.
    
    Args:
        url: The image URL
        
    Returns:
        QPixmap if cached, None otherwise
    """
    cache_path = _get_cache_path(url)
    if cache_path.exists():
        pixmap = QPixmap()
        if pixmap.load(str(cache_path)):
            return pixmap
    return None


def save_to_cache(url: str, data: QByteArray) -> Optional[QPixmap]:
    """
    Save image data to cache and return pixmap.
    
    Args:
        url: The image URL
        data: Raw image data from network reply
        
    Returns:
        QPixmap if successful, None otherwise
    """
    _ensure_cache_dir()
    pixmap = QPixmap()
    if pixmap.loadFromData(data):
        cache_path = _get_cache_path(url)
        try:
            pixmap.save(str(cache_path), "PNG")
        except Exception:
            pass  # Silently fail on cache save errors
        return pixmap
    return None


def clear_cache():
    """Clear all cached images."""
    if CACHE_DIR.exists():
        for f in CACHE_DIR.iterdir():
            try:
                f.unlink()
            except Exception:
                pass
