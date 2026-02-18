"""
User model for HTB Client.
"""

from dataclasses import dataclass, field
from typing import Optional, Any


@dataclass
class User:
    """HackTheBox user information."""
    
    id: int
    name: str
    email: str
    timezone: str
    is_vip: bool
    is_moderator: bool
    subscription_type: str
    can_access_vip: bool
    server_id: int
    avatar: Optional[str]
    rank_id: int
    verified: bool
    identifier: str
    team: Optional[str]
    university: Optional[str]
    
    @classmethod
    def from_api(cls, data: dict) -> "User":
        """Create User from API response."""
        info = data.get("info", data)
        
        return cls(
            id=info.get("id", 0),
            name=info.get("name", ""),
            email=info.get("email", ""),
            timezone=info.get("timezone", ""),
            is_vip=info.get("isVip", False),
            is_moderator=info.get("isModerator", False),
            subscription_type=info.get("subscriptionType", "free"),
            can_access_vip=info.get("canAccessVIP", False),
            server_id=info.get("server_id", 0),
            avatar=info.get("avatar"),
            rank_id=info.get("rank_id", 1),
            verified=info.get("verified", False),
            identifier=info.get("identifier", ""),
            team=info.get("team"),
            university=info.get("university")
        )
    
    @property
    def avatar_url(self) -> str:
        """Get full avatar URL or default."""
        if self.avatar:
            if self.avatar.startswith("http"):
                return self.avatar
            return f"https://labs.hackthebox.com{self.avatar}"
        return ""
    
    @property
    def subscription_display(self) -> str:
        """Get display-friendly subscription type."""
        mapping = {
            "free": "Free",
            "vip": "VIP",
            "vip+": "VIP+",
        }
        return mapping.get(self.subscription_type, self.subscription_type.upper())
