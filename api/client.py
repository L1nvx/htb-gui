"""
HTB API Client
Base HTTP client with debug logging and TLS verification disabled.
"""

import requests
import urllib3
from typing import Any, Optional, Tuple

import time

from config import config, API_V4, API_V5
from utils.debug import debug_request, debug_response, debug_log

# Disable SSL warnings (as requested)
#urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class HTBClient:
    """
    Base HTTP client for HackTheBox API.
    Handles authentication, requests, and debug logging.
    """
    
    def __init__(self):
        self.session = requests.Session()
        #self.session.verify = False  # Disable TLS verification as requested
        debug_log("CLIENT", "HTBClient initialized")
    
    def _get_headers(self) -> dict:
        """Get request headers with authorization."""
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": "HTB-Desktop-Client/1.0"
        }
        
        if config.api_token:
            headers["Authorization"] = f"Bearer {config.api_token}"
        
        return headers
    
    def _request_with_retry(self, method: str, endpoint: str, 
                          params: Optional[dict] = None, 
                          data: Optional[dict] = None,
                          version: str = "v4") -> Tuple[bool, Any]:
        """
        Internal method to handle requests with retry logic.
        Retries on connection errors, timeouts, and server errors (5xx/429).
        Waits 10 seconds between retries.
        """
        base = API_V4 if version == "v4" else API_V5
        url = f"{base}{endpoint}"
        
        while True:
            debug_request(method, url, data if method == "POST" else params)
            
            try:
                if method == "GET":
                    response = self.session.get(
                        url, headers=self._get_headers(), params=params, timeout=30
                    )
                else:
                    response = self.session.post(
                        url, headers=self._get_headers(), json=data, timeout=30
                    )
                
                # Check for blocking status codes
                if response.status_code >= 500 or response.status_code == 429:
                    error_msg = f"HTTP {response.status_code} - Server Error/Rate Limit"
                    debug_response(response.status_code, url, error_msg)
                    debug_log("CLIENT", f"API Issue ({response.status_code}). Retrying in 10s...")
                    time.sleep(10)
                    continue
                
                # Check for API errors (4xx)
                if response.status_code >= 400:
                    try:
                        resp_data = response.json()
                        error_msg = resp_data.get('message', resp_data.get('error', f'HTTP {response.status_code}'))
                    except:
                        error_msg = f"HTTP {response.status_code}"
                    
                    debug_response(response.status_code, url, error_msg)
                    return False, error_msg
                
                # Success
                content_type = response.headers.get('Content-Type', '')
                if 'application/json' in content_type:
                    try:
                        resp_data = response.json()
                        # If data is None or empty, maybe retry? 
                        # User said "no retorna datos". 
                        # But some APIs return empty 200 OK. 
                        # We'll assume strict JSON parsing error or actual connection fail covers "active/down".
                        debug_response(response.status_code, url, resp_data)
                        return True, resp_data
                    except ValueError:
                        debug_log("CLIENT", "Invalid JSON response. Retrying in 10s...")
                        time.sleep(10)
                        continue
                else:
                    debug_response(response.status_code, url, f"Binary/Other ({len(response.content)} bytes)")
                    return True, response.content

            except (requests.exceptions.ConnectionError, requests.exceptions.Timeout) as e:
                debug_response(0, url, error=str(e))
                debug_log("CLIENT", f"Connection failed: {e}. Retrying in 10s...")
                time.sleep(10)
                continue
                
            except Exception as e:
                debug_response(0, url, error=str(e))
                return False, f"Unexpected error: {str(e)}"

    def get(self, endpoint: str, params: Optional[dict] = None, 
            version: str = "v4") -> Tuple[bool, Any]:
        """Make a GET request with retry."""
        return self._request_with_retry("GET", endpoint, params=params, version=version)
    
    def post(self, endpoint: str, data: Optional[dict] = None,
             version: str = "v4") -> Tuple[bool, Any]:
        """Make a POST request with retry."""
        return self._request_with_retry("POST", endpoint, data=data, version=version)


# Global client instance
client = HTBClient()
