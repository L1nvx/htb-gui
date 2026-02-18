"""
Connection/VPN models for HTB Client.
"""

from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List


@dataclass
class VPNServer:
    """VPN server information."""
    
    id: int
    friendly_name: str
    full: bool
    current_clients: int
    location: str
    
    @classmethod
    def from_api(cls, data: dict) -> "VPNServer":
        """Create VPNServer from API response."""
        return cls(
            id=data.get("id", 0),
            friendly_name=data.get("friendly_name", ""),
            full=data.get("full", False),
            current_clients=data.get("current_clients", 0),
            location=data.get("location", "")
        )
    
    @property
    def status_icon(self) -> str:
        """Get status icon based on server load."""
        if self.full:
            return "🔴"
        elif self.current_clients > 200:
            return "🟡"
        return "🟢"
    
    @property
    def display_name(self) -> str:
        """Get formatted display name."""
        return f"{self.status_icon} {self.friendly_name} ({self.current_clients} clients)"


@dataclass
class Connection:
    """Active VPN connection information."""
    
    type: str
    connection_type: str
    location_type_friendly: str
    server_id: int
    server_hostname: str
    server_friendly_name: str
    username: str
    through_pwnbox: bool
    ip4: str
    ip6: str
    down: int
    up: int
    
    @classmethod
    def from_api(cls, data: dict) -> "Connection":
        """Create Connection from API response."""
        server = data.get("server", {})
        connection = data.get("connection", {})
        
        return cls(
            type=data.get("type", ""),
            connection_type=data.get("connection_type", ""),
            location_type_friendly=data.get("location_type_friendly", ""),
            server_id=server.get("id", 0),
            server_hostname=server.get("hostname", ""),
            server_friendly_name=server.get("friendly_name", ""),
            username=connection.get("name", ""),
            through_pwnbox=connection.get("through_pwnbox", False),
            ip4=connection.get("ip4", ""),
            ip6=connection.get("ip6", ""),
            down=connection.get("down", 0),
            up=connection.get("up", 0)
        )
    
    @property
    def status_display(self) -> str:
        """Get formatted connection status."""
        return f"🟢 Connected to {self.server_friendly_name}"
    
    @property
    def ip_display(self) -> str:
        """Get formatted IP addresses."""
        parts = []
        if self.ip4:
            parts.append(f"IPv4: {self.ip4}")
        if self.ip6:
            parts.append(f"IPv6: {self.ip6}")
        return " | ".join(parts) if parts else "No IP assigned"


@dataclass
class ActiveMachine:
    """Currently active/spawned machine."""
    
    id: int
    name: str
    avatar: str
    type: str
    expires_at: str
    is_spawning: bool
    lab_server: str
    vpn_server_id: int
    ip: str
    
    @classmethod
    def from_api(cls, data: dict) -> Optional["ActiveMachine"]:
        """Create ActiveMachine from API response."""
        info = data.get("info")
        if not info:
            return None
        
        avatar = info.get("avatar", "")
        if avatar and not avatar.startswith("http"):
            avatar = f"https://htb-mp-prod-public-storage.s3.eu-central-1.amazonaws.com{avatar}"
        
        return cls(
            id=info.get("id", 0),
            name=info.get("name", ""),
            avatar=avatar,
            type=info.get("type", ""),
            expires_at=info.get("expires_at", ""),
            is_spawning=info.get("isSpawning", False),
            lab_server=info.get("lab_server", ""),
            vpn_server_id=info.get("vpn_server_id", 0),
            ip=info.get("ip", "")
        )
    
    @property
    def status_text(self) -> str:
        """Get status text."""
        if self.is_spawning:
            return "🔄 Spawning..."
        elif self.ip:
            return f"🟢 Running ({self.ip})"
        return "⚪ Unknown"
