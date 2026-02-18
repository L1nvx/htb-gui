"""
HTB API Endpoints
All API endpoint wrappers with proper typing and debug logging.
"""

from typing import Any, List, Optional, Tuple
from .client import client
from utils.debug import debug_log


class HTBApi:
    """
    HackTheBox API wrapper.
    All methods return Tuple[bool, data/error].
    """
    
    # ==================== USER ====================
    
    @staticmethod
    def get_user_info() -> Tuple[bool, Any]:
        """Get current user information."""
        debug_log("API", "Fetching user info...")
        return client.get("/user/info")
    
    # ==================== SEASONS ====================
    
    @staticmethod
    def get_seasons() -> Tuple[bool, Any]:
        """Get list of all seasons."""
        debug_log("API", "Fetching seasons list...")
        return client.get("/season/list")
    
    @staticmethod
    def get_season_machines(season_id: int) -> Tuple[bool, Any]:
        """Get machines for a specific season."""
        debug_log("API", f"Fetching machines for season {season_id}...")
        return client.get(f"/season/machines/{season_id}")
    
    @staticmethod
    def get_active_season_machine() -> Tuple[bool, Any]:
        """Get the active seasonal machine."""
        debug_log("API", "Fetching active season machine...")
        return client.get("/season/machine/active")
    
    @staticmethod
    def get_season_leaderboard(season_id: int, per_page: int = 15) -> Tuple[bool, Any]:
        """Get season leaderboard."""
        debug_log("API", f"Fetching leaderboard for season {season_id}...")
        return client.get(
            "/season/players/leaderboard",
            params={"per_page": per_page, "season": season_id}
        )
    
    # ==================== MACHINES ====================
    
    @staticmethod
    def get_machines(per_page: int = 100) -> Tuple[bool, Any]:
        """Get list of machines."""
        debug_log("API", f"Fetching machines (per_page={per_page})...")
        return client.get(
            "/machines",
            params={"per_page": per_page},
            version="v5"
        )
    
    @staticmethod
    def get_machine_profile(name: str) -> Tuple[bool, Any]:
        """Get detailed profile of a machine by name."""
        debug_log("API", f"Fetching machine profile: {name}...")
        return client.get(f"/machine/profile/{name}")
    
    @staticmethod
    def get_active_machine() -> Tuple[bool, Any]:
        """Get user's currently active machine."""
        debug_log("API", "Fetching active machine...")
        return client.get("/machine/active")
    
    @staticmethod
    def get_machine_activity(machine_id: int) -> Tuple[bool, Any]:
        """Get activity log for a machine."""
        debug_log("API", f"Fetching activity for machine {machine_id}...")
        return client.get(f"/machine/activity/{machine_id}")
    
    # ==================== MACHINE ACTIONS ====================
    
    @staticmethod
    def spawn_machine(machine_id: int) -> Tuple[bool, Any]:
        """Spawn/start a machine."""
        debug_log("API", f"Spawning machine {machine_id}...")
        return client.post("/vm/spawn", {"machine_id": machine_id})
    
    @staticmethod
    def reset_machine(machine_id: int) -> Tuple[bool, Any]:
        """Reset a machine."""
        debug_log("API", f"Resetting machine {machine_id}...")
        return client.post("/vm/reset", {"machine_id": machine_id})
    
    @staticmethod
    def terminate_machine(machine_id: int) -> Tuple[bool, Any]:
        """Terminate/stop a machine."""
        debug_log("API", f"Terminating machine {machine_id}...")
        return client.post("/vm/terminate", {"machine_id": machine_id})
    
    @staticmethod
    def submit_flag(machine_id: int, flag: str) -> Tuple[bool, Any]:
        """Submit a flag for a machine."""
        debug_log("API", f"Submitting flag for machine {machine_id}...")
        return client.post(
            "/machine/own",
            {"id": machine_id, "flag": flag},
            version="v5"
        )
    
    # ==================== VPN/CONNECTION ====================
    
    @staticmethod
    def get_connection_status() -> Tuple[bool, Any]:
        """Get current VPN connection status."""
        debug_log("API", "Fetching connection status...")
        return client.get("/connection/status")
    
    @staticmethod
    def get_vpn_servers(product: str = "competitive") -> Tuple[bool, Any]:
        """Get available VPN servers."""
        debug_log("API", f"Fetching VPN servers for {product}...")
        return client.get(
            "/connections/servers",
            params={"product": product}
        )
    
    @staticmethod
    def switch_server(server_id: int) -> Tuple[bool, Any]:
        """
        Switch to a VPN server.
        
        This MUST be called before downloading a VPN file to ensure
        the user is assigned to the correct server. Without this,
        machines will be on a different IP and unreachable, and
        flags will be considered invalid.
        
        Args:
            server_id: VPN server ID to switch to
        
        Returns:
            Tuple of (success, response/error)
        """
        debug_log("API", f"Switching to VPN server {server_id}...")
        return client.post(f"/connections/servers/switch/{server_id}")
    
    @staticmethod
    def download_vpn_file(server_id: int, file_type: int = 0, 
                          tcp: int = 1) -> Tuple[bool, Any]:
        """
        Download VPN configuration file.
        
        Args:
            server_id: VPN server ID
            file_type: 0 for standard
            tcp: 1 for TCP, 0 for UDP
        
        Returns:
            Tuple of (success, file_content/error)
        """
        debug_log("API", f"Downloading VPN file for server {server_id}...")
        return client.get(f"/access/ovpnfile/{server_id}/{file_type}/{tcp}")
