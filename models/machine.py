"""
Machine model for HTB Client.
"""

from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List
from datetime import datetime


@dataclass
class MachineFeedback:
    """Machine difficulty feedback chart."""
    cake: int = 0
    very_easy: int = 0
    easy: int = 0
    too_easy: int = 0
    medium: int = 0
    bit_hard: int = 0
    hard: int = 0
    too_hard: int = 0
    ex_hard: int = 0
    brain_fuck: int = 0
    
    @classmethod
    def from_api(cls, data: dict) -> "MachineFeedback":
        if not data:
            return cls()
        return cls(
            cake=data.get("counterCake", 0),
            very_easy=data.get("counterVeryEasy", 0),
            easy=data.get("counterEasy", 0),
            too_easy=data.get("counterTooEasy", 0),
            medium=data.get("counterMedium", 0),
            bit_hard=data.get("counterBitHard", 0),
            hard=data.get("counterHard", 0),
            too_hard=data.get("counterTooHard", 0),
            ex_hard=data.get("counterExHard", 0),
            brain_fuck=data.get("counterBrainFuck", 0)
        )


@dataclass
class MachinePlayInfo:
    """Machine play state information."""
    is_spawned: bool = False
    is_spawning: bool = False
    is_active: bool = False
    active_player_count: int = 0
    expires_at: Optional[str] = None
    
    @classmethod
    def from_api(cls, data: dict) -> "MachinePlayInfo":
        if not data:
            return cls()
        return cls(
            is_spawned=data.get("isSpawned") or data.get("is_spawned") or False,
            is_spawning=data.get("isSpawning") or data.get("is_spawning") or False,
            is_active=data.get("isActive") or data.get("is_active") or False,
            active_player_count=data.get("active_player_count", 0) or 0,
            expires_at=data.get("expires_at")
        )


@dataclass
class MachineCreator:
    """Machine creator information."""
    id: int
    name: str
    avatar: str
    is_respected: bool = False
    profile_url: str = ""
    
    @classmethod
    def from_api(cls, data: dict) -> "MachineCreator":
        if not data:
            return cls(id=0, name="Unknown", avatar="")
        return cls(
            id=data.get("id", 0),
            name=data.get("name", "Unknown"),
            avatar=data.get("avatar", ""),
            is_respected=data.get("isRespected", False),
            profile_url=data.get("profile_url", "")
        )


@dataclass
class Machine:
    """HackTheBox machine information."""
    
    id: int
    name: str
    os: str
    difficulty_text: str
    difficulty: int
    points: int
    rating: float
    rating_count: int
    avatar: str
    ip: Optional[str]
    
    # State
    active: bool
    retired: bool
    free: bool
    todo: bool
    
    # User progress
    user_owns_count: int
    root_owns_count: int
    auth_user_in_user_owns: bool
    auth_user_in_root_owns: bool
    
    # Dates
    release_date: Optional[str]
    retired_date: Optional[str]
    
    # Additional info
    play_info: MachinePlayInfo = field(default_factory=MachinePlayInfo)
    feedback: MachineFeedback = field(default_factory=MachineFeedback)
    creator: Optional[MachineCreator] = None
    labels: List[dict] = field(default_factory=list)
    
    # Season specific
    season_id: Optional[int] = None
    user_points: int = 0
    root_points: int = 0
    
    @classmethod
    def from_api(cls, data: dict) -> "Machine":
        """Create Machine from API response."""
        # Handle both direct data and nested "info" format
        info = data.get("info", data)
        
        # Parse avatar URL
        avatar = info.get("avatar", "")
        if avatar and not avatar.startswith("http"):
            avatar = f"https://htb-mp-prod-public-storage.s3.eu-central-1.amazonaws.com{avatar}"
        
        # Parse creator
        creator_data = info.get("maker") or info.get("firstCreator")
        creator = MachineCreator.from_api(creator_data) if creator_data else None
        
        return cls(
            id=info.get("id", 0),
            name=info.get("name", ""),
            os=info.get("os", ""),
            difficulty_text=info.get("difficultyText") or info.get("difficulty_text", "Unknown"),
            difficulty=info.get("difficulty", 0),
            points=info.get("points") or info.get("static_points", 0),
            rating=info.get("rating") or info.get("stars", 0.0),
            rating_count=info.get("ratingCount") or info.get("reviews_count", 0),
            avatar=avatar,
            ip=info.get("ip"),
            active=info.get("active", False),
            retired=info.get("retired", False),
            free=info.get("free", False),
            todo=info.get("todo") or info.get("isTodo", False),
            user_owns_count=info.get("userOwnsCount") or info.get("user_owns_count", 0),
            root_owns_count=info.get("rootOwnsCount") or info.get("root_owns_count", 0),
            auth_user_in_user_owns=info.get("authUserInUserOwns") or info.get("is_owned_user", False),
            auth_user_in_root_owns=info.get("authUserInRootOwns") or info.get("is_owned_root", False),
            release_date=info.get("releaseDate") or info.get("release") or info.get("release_time"),
            retired_date=info.get("retiredDate"),
            play_info=MachinePlayInfo.from_api(info.get("playInfo") or info.get("play_info", {})),
            feedback=MachineFeedback.from_api(info.get("feedbackForChart", {})),
            creator=creator,
            labels=info.get("labels", []),
            season_id=info.get("season_id"),
            user_points=info.get("user_points", 0),
            root_points=info.get("root_points", 0)
        )
    
    @property
    def os_icon(self) -> str:
        """Get icon name for OS."""
        os_lower = self.os.lower()
        if "linux" in os_lower:
            return "🐧"
        elif "windows" in os_lower:
            return "🪟"
        elif "freebsd" in os_lower or "bsd" in os_lower:
            return "😈"
        elif "android" in os_lower:
            return "🤖"
        return "💻"
    
    @property
    def difficulty_color(self) -> str:
        """Get color for difficulty level."""
        diff = self.difficulty_text.lower()
        colors = {
            "easy": "#9fef00",      # Green
            "medium": "#ffaf00",    # Orange
            "hard": "#ff3e3e",      # Red
            "insane": "#7d3c98",    # Purple
        }
        return colors.get(diff, "#ffffff")
    
    @property
    def status_text(self) -> str:
        """Get human-readable status."""
        if self.play_info.is_spawning:
            return "Spawning..."
        elif self.play_info.is_spawned or self.ip:
            return f"Active ({self.ip})"
        elif self.active:
            return "Available"
        elif self.retired:
            return "Retired"
        return "Unknown"
    
    @property
    def progress_status(self) -> str:
        """Get user's progress on this machine."""
        if self.auth_user_in_root_owns:
            return "🏆 Owned"
        elif self.auth_user_in_user_owns:
            return "👤 User owned"
        return "❌ Not owned"
