"""
Season model for HTB Client.
"""

from dataclasses import dataclass, field
from typing import Optional, List
from datetime import datetime


@dataclass
class Season:
    """HackTheBox season information."""
    
    id: int
    name: str
    subtitle: str
    start_date: str
    end_date: str
    state: str
    is_visible: bool
    active: bool
    weeks: int
    current_week: Optional[int]
    players: int
    
    # Images
    background_image: str = ""
    new_background_image: str = ""
    logo: str = ""
    trailer: Optional[str] = None
    
    @classmethod
    def from_api(cls, data: dict) -> "Season":
        """Create Season from API response."""
        return cls(
            id=data.get("id", 0),
            name=data.get("name", ""),
            subtitle=data.get("subtitle", ""),
            start_date=data.get("start_date", ""),
            end_date=data.get("end_date", ""),
            state=data.get("state", ""),
            is_visible=data.get("is_visible", True),
            active=data.get("active", False),
            weeks=data.get("weeks", 0),
            current_week=data.get("current_week"),
            players=data.get("players", 0),
            background_image=data.get("background_image", ""),
            new_background_image=data.get("new_background_image", ""),
            logo=data.get("logo", ""),
            trailer=data.get("trailer")
        )
    
    @property
    def status_display(self) -> str:
        """Get display-friendly status."""
        if self.active:
            return "🟢 Active"
        elif self.state == "ended":
            return "🔴 Ended"
        elif self.state == "upcoming":
            return "🟡 Upcoming"
        return self.state.capitalize()
    
    @property
    def date_range(self) -> str:
        """Get formatted date range."""
        try:
            start = datetime.fromisoformat(self.start_date.replace("Z", "+00:00"))
            end = datetime.fromisoformat(self.end_date.replace("Z", "+00:00"))
            return f"{start.strftime('%b %d, %Y')} - {end.strftime('%b %d, %Y')}"
        except:
            return f"{self.start_date} - {self.end_date}"


@dataclass
class LeaderboardEntry:
    """Leaderboard entry for a season."""
    
    resource_id: int
    rank: int
    league_rank: str
    name: str
    country: str
    country_name: str
    avatar_thumb: str
    points: int
    user_owns: int
    root_owns: int
    user_bloods: int
    root_bloods: int
    last_own: str
    positive_trend: bool = True
    rank_trend: int = 0
    
    @classmethod
    def from_api(cls, data: dict) -> "LeaderboardEntry":
        """Create LeaderboardEntry from API response."""
        return cls(
            resource_id=data.get("resource_id", 0),
            rank=data.get("rank", 0),
            league_rank=data.get("league_rank", ""),
            name=data.get("name", ""),
            country=data.get("country", ""),
            country_name=data.get("country_name", ""),
            avatar_thumb=data.get("avatar_thumb", ""),
            points=data.get("points", 0),
            user_owns=data.get("user_owns", 0),
            root_owns=data.get("root_owns", 0),
            user_bloods=data.get("user_bloods", 0),
            root_bloods=data.get("root_bloods", 0),
            last_own=data.get("last_own", ""),
            positive_trend=data.get("positive_trend", True),
            rank_trend=data.get("rank_trend", 0)
        )
    
    @property
    def league_color(self) -> str:
        """Get color for league rank."""
        colors = {
            "Bronze": "#cd7f32",
            "Silver": "#c0c0c0",
            "Gold": "#ffd700",
            "Platinum": "#e5e4e2",
            "Diamond": "#b9f2ff",
        }
        return colors.get(self.league_rank, "#ffffff")
