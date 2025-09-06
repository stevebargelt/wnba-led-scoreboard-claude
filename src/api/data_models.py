#!/usr/bin/env python3

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any, Tuple
from enum import Enum

# Re-export the main game models from wnba_api
from .wnba_api import GameTeam, GameStatus, GameClock, WNBAGame


class DisplayState(Enum):
    """Possible display states for the scoreboard."""
    IDLE = "idle"           # No games to show
    PREGAME = "pregame"     # Show countdown to game
    LIVE = "live"           # Show live game scoreboard
    FINAL = "final"         # Show final score
    ERROR = "error"         # Show error message


class Priority(Enum):
    """Priority levels for game selection."""
    HIGH = 1     # Favorite team game
    MEDIUM = 2   # Live game
    LOW = 3      # Upcoming game


@dataclass
class DisplayGame:
    """A game selected for display with priority information."""
    game: WNBAGame
    priority: Priority
    priority_score: int  # Lower is higher priority
    reason: str  # Why this game was selected
    
    def __lt__(self, other):
        """Compare games for sorting by priority."""
        if not isinstance(other, DisplayGame):
            return NotImplemented
        return self.priority_score < other.priority_score


@dataclass
class ScoreboardData:
    """Data structure for scoreboard display."""
    away_team: str
    away_score: int
    home_team: str
    home_score: int
    period: int
    time_remaining: str
    away_color: Tuple[int, int, int]
    home_color: Tuple[int, int, int]
    status_text: str = ""
    
    @property
    def is_tied(self) -> bool:
        """Check if the game is tied."""
        return self.away_score == self.home_score
    
    @property
    def leader(self) -> Optional[str]:
        """Get the team that's leading."""
        if self.away_score > self.home_score:
            return self.away_team
        elif self.home_score > self.away_score:
            return self.home_team
        return None
    
    @property
    def lead_amount(self) -> int:
        """Get the amount by which the leader is ahead."""
        return abs(self.away_score - self.home_score)


@dataclass
class CountdownData:
    """Data structure for pregame countdown display."""
    away_team: str
    home_team: str
    game_time: datetime
    time_until: timedelta
    away_color: Tuple[int, int, int]
    home_color: Tuple[int, int, int]
    
    @property
    def hours_until(self) -> int:
        """Hours until game starts."""
        return int(self.time_until.total_seconds() // 3600)
    
    @property
    def minutes_until(self) -> int:
        """Minutes until game starts (excluding hours)."""
        remaining_seconds = int(self.time_until.total_seconds() % 3600)
        return remaining_seconds // 60
    
    @property
    def total_minutes_until(self) -> int:
        """Total minutes until game starts."""
        return int(self.time_until.total_seconds() // 60)
    
    @property
    def countdown_text(self) -> str:
        """Formatted countdown text."""
        if self.hours_until > 0:
            return f"{self.hours_until}H {self.minutes_until}M"
        else:
            return f"{self.minutes_until}M"


@dataclass
class IdleData:
    """Data structure for idle state display."""
    message: str = "No games today"
    show_clock: bool = True
    current_time: Optional[datetime] = None


@dataclass
class ErrorData:
    """Data structure for error state display."""
    error_message: str
    error_code: str = "UNKNOWN"
    retry_in: Optional[int] = None  # seconds until retry


@dataclass
class DisplayContext:
    """Complete context for what to display on the scoreboard."""
    state: DisplayState
    scoreboard: Optional[ScoreboardData] = None
    countdown: Optional[CountdownData] = None
    idle: Optional[IdleData] = None
    error: Optional[ErrorData] = None
    last_updated: datetime = field(default_factory=datetime.now)
    
    def __post_init__(self):
        """Validate that the appropriate data is set for the state."""
        if self.state == DisplayState.LIVE and self.scoreboard is None:
            raise ValueError("Scoreboard data required for LIVE state")
        elif self.state == DisplayState.PREGAME and self.countdown is None:
            raise ValueError("Countdown data required for PREGAME state")
        elif self.state == DisplayState.IDLE and self.idle is None:
            self.idle = IdleData()
        elif self.state == DisplayState.ERROR and self.error is None:
            raise ValueError("Error data required for ERROR state")


@dataclass
class GameStats:
    """Extended game statistics for display."""
    game_id: str
    quarter_scores: List[Tuple[int, int]]  # List of (away, home) scores per quarter
    total_fouls: Tuple[int, int] = (0, 0)  # (away, home) fouls
    timeouts_left: Tuple[int, int] = (7, 7)  # (away, home) timeouts remaining
    possession: Optional[str] = None  # Team with possession
    last_play: str = ""
    
    @property
    def quarter_count(self) -> int:
        """Number of quarters played/being played."""
        return len(self.quarter_scores)


@dataclass
class TeamRecord:
    """Team season record information."""
    wins: int
    losses: int
    streak: str = ""  # e.g., "W3" or "L2"
    
    @property
    def winning_percentage(self) -> float:
        """Calculate winning percentage."""
        total_games = self.wins + self.losses
        if total_games == 0:
            return 0.0
        return self.wins / total_games
    
    @property
    def record_text(self) -> str:
        """Formatted record text."""
        return f"{self.wins}-{self.losses}"