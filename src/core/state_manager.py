#!/usr/bin/env python3

import logging
from datetime import datetime, timedelta, timezone
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field

from api.wnba_api import ESPNWNBAClient, WNBAGame
from api.data_models import (
    DisplayState, DisplayContext, DisplayGame, Priority,
    ScoreboardData, CountdownData, IdleData, ErrorData
)
from core.config import get_config

logger = logging.getLogger(__name__)


@dataclass
class GameStateHistory:
    """Track the history of a game's state."""
    game_id: str
    previous_state: str = ""
    current_state: str = ""
    last_updated: datetime = field(default_factory=datetime.now)
    score_changes: List[Dict[str, Any]] = field(default_factory=list)


class WNBAStateManager:
    """Manages the state and game selection for the WNBA scoreboard."""
    
    def __init__(self, api_client: Optional[ESPNWNBAClient] = None):
        """
        Initialize the state manager.
        
        Args:
            api_client: WNBA API client instance. If None, creates a new one.
        """
        self.config = get_config()
        self.api_client = api_client or ESPNWNBAClient(timeout=self.config.api.timeout)
        
        # Current state tracking
        self.current_game: Optional[WNBAGame] = None
        self.current_display_state: DisplayState = DisplayState.IDLE
        self.last_update: datetime = datetime.now()
        self.error_count: int = 0
        self.next_refresh: datetime = datetime.now()
        
        # Game history tracking
        self.game_history: Dict[str, GameStateHistory] = {}
        
        # Cache for favorite teams
        self.favorite_teams = self.config.favorite_teams
        
        logger.info(f"State manager initialized with {len(self.favorite_teams)} favorite teams")
    
    def _get_team_color(self, abbreviation: str) -> tuple[int, int, int]:
        """Get team primary color as RGB tuple."""
        team = self.config.get_team(abbreviation)
        if team:
            try:
                from display.renderer import Color
                return Color.from_hex(team.primary_color)
            except Exception:
                logger.warning(f"Could not parse color for team {abbreviation}")
        
        # Default colors if team not found
        default_colors = {
            'LAS': (0, 0, 0),     # Black
            'SEA': (44, 82, 52),  # Green
            'NY': (134, 206, 188), # Teal
            'ATL': (200, 16, 46),  # Red
            'CHI': (65, 143, 222), # Blue
            'IND': (253, 187, 48), # Yellow
            'PHX': (203, 96, 21),  # Orange
            'MIN': (35, 97, 146),  # Blue
            'WAS': (200, 16, 46),  # Red
            'DAL': (0, 83, 188),   # Blue
            'CONN': (224, 58, 62), # Red
        }
        
        return default_colors.get(abbreviation, (255, 255, 255))  # White default
    
    def _prioritize_games(self, games: List[WNBAGame]) -> List[DisplayGame]:
        """
        Prioritize games for display based on user preferences and game state.
        
        Args:
            games: List of available games
            
        Returns:
            Sorted list of games with priority information
        """
        display_games = []
        
        for game in games:
            # Check if this is a favorite team game
            is_favorite = (
                game.home_team.abbreviation in self.favorite_teams or 
                game.away_team.abbreviation in self.favorite_teams
            )
            
            # Calculate priority score (lower = higher priority)
            priority_score = 100  # Base score
            reason_parts = []
            
            if is_favorite:
                favorite_priority = min(
                    self.config.get_favorite_team_priority(game.home_team.abbreviation),
                    self.config.get_favorite_team_priority(game.away_team.abbreviation)
                )
                priority_score -= 50  # High priority bonus for favorite teams
                priority_score += favorite_priority  # Add specific team priority
                reason_parts.append("favorite team")
                priority = Priority.HIGH
            else:
                priority = Priority.MEDIUM
            
            # Game state bonuses/penalties
            if game.is_live:
                priority_score -= 20  # Live games are important
                reason_parts.append("live")
                if priority != Priority.HIGH:
                    priority = Priority.MEDIUM
            elif game.is_pregame:
                # Upcoming games get priority based on how soon they start
                time_until = game.date - datetime.now(timezone.utc)
                hours_until = time_until.total_seconds() / 3600
                
                if hours_until <= self.config.api.pregame_hours:
                    priority_score -= 10  # Upcoming games within window
                    reason_parts.append(f"starts in {hours_until:.1f}h")
                    if priority == Priority.MEDIUM:
                        priority = Priority.MEDIUM
                else:
                    priority_score += 10  # Future games are lower priority
                    if priority != Priority.HIGH:
                        priority = Priority.LOW
            elif game.is_final:
                priority_score += 30  # Completed games are lower priority
                reason_parts.append("final")
                if priority != Priority.HIGH:
                    priority = Priority.LOW
            
            reason = ", ".join(reason_parts) if reason_parts else "available game"
            
            display_games.append(DisplayGame(
                game=game,
                priority=priority,
                priority_score=priority_score,
                reason=reason
            ))
        
        # Sort by priority score (ascending = higher priority first)
        display_games.sort()
        
        if display_games:
            logger.debug(f"Game priorities: {[(dg.game.away_team.abbreviation + '@' + dg.game.home_team.abbreviation, dg.priority_score, dg.reason) for dg in display_games[:3]]}")
        
        return display_games
    
    def _update_game_history(self, game: WNBAGame):
        """Update the history tracking for a game."""
        if game.id not in self.game_history:
            self.game_history[game.id] = GameStateHistory(game_id=game.id)
        
        history = self.game_history[game.id]
        history.previous_state = history.current_state
        history.current_state = game.status.state
        history.last_updated = datetime.now()
        
        # Track score changes for live games
        if game.is_live and self.current_game and self.current_game.id == game.id:
            if (game.home_team.score != self.current_game.home_team.score or 
                game.away_team.score != self.current_game.away_team.score):
                
                score_change = {
                    'timestamp': datetime.now(),
                    'away_score': game.away_team.score,
                    'home_score': game.home_team.score,
                    'period': game.clock.period,
                    'time': game.clock.display_clock
                }
                history.score_changes.append(score_change)
                logger.info(f"Score update: {game.away_team.abbreviation} {game.away_team.score} - {game.home_team.abbreviation} {game.home_team.score}")
    
    def _create_scoreboard_data(self, game: WNBAGame) -> ScoreboardData:
        """Create scoreboard data from a game."""
        return ScoreboardData(
            away_team=game.away_team.abbreviation,
            away_score=game.away_team.score,
            home_team=game.home_team.abbreviation,
            home_score=game.home_team.score,
            period=game.clock.period,
            time_remaining=game.clock.display_clock,
            away_color=self._get_team_color(game.away_team.abbreviation),
            home_color=self._get_team_color(game.home_team.abbreviation),
            status_text=game.status.short_detail
        )
    
    def _create_countdown_data(self, game: WNBAGame) -> CountdownData:
        """Create countdown data from a pregame."""
        now = datetime.now(timezone.utc)
        game_time = game.date
        if game_time.tzinfo is None:
            game_time = game_time.replace(tzinfo=timezone.utc)
        
        time_until = game_time - now
        
        return CountdownData(
            away_team=game.away_team.abbreviation,
            home_team=game.home_team.abbreviation,
            game_time=game_time,
            time_until=time_until,
            away_color=self._get_team_color(game.away_team.abbreviation),
            home_color=self._get_team_color(game.home_team.abbreviation)
        )
    
    def get_current_display_context(self) -> DisplayContext:
        """
        Get the current display context based on available games and priorities.
        
        Returns:
            DisplayContext with appropriate state and data
        """
        try:
            # Get games for today and tomorrow
            today = datetime.now()
            today_games = self.api_client.get_scoreboard(today)
            
            tomorrow = today + timedelta(days=1)
            tomorrow_games = self.api_client.get_scoreboard(tomorrow)
            
            all_games = today_games + tomorrow_games
            
            # Filter for favorite team games or get all games
            favorite_games = []
            other_games = []
            
            for game in all_games:
                if (game.home_team.abbreviation in self.favorite_teams or 
                    game.away_team.abbreviation in self.favorite_teams):
                    favorite_games.append(game)
                else:
                    other_games.append(game)
            
            # Prioritize all games
            games_to_consider = favorite_games if favorite_games else other_games
            if not games_to_consider:
                games_to_consider = all_games
            
            prioritized_games = self._prioritize_games(games_to_consider)
            
            if not prioritized_games:
                # No games available
                return DisplayContext(
                    state=DisplayState.IDLE,
                    idle=IdleData(message="No games today", current_time=datetime.now())
                )
            
            # Select the highest priority game
            selected_display_game = prioritized_games[0]
            game = selected_display_game.game
            
            # Update tracking
            self._update_game_history(game)
            self.current_game = game
            self.last_update = datetime.now()
            self.error_count = 0
            
            # Determine display state and create appropriate context
            if game.is_live:
                self.current_display_state = DisplayState.LIVE
                return DisplayContext(
                    state=DisplayState.LIVE,
                    scoreboard=self._create_scoreboard_data(game)
                )
            
            elif game.is_pregame:
                # Check if game is within the pregame window
                now = datetime.now(timezone.utc)
                game_time = game.date
                if game_time.tzinfo is None:
                    game_time = game_time.replace(tzinfo=timezone.utc)
                
                time_until = game_time - now
                hours_until = time_until.total_seconds() / 3600
                
                if hours_until <= self.config.api.pregame_hours:
                    self.current_display_state = DisplayState.PREGAME
                    return DisplayContext(
                        state=DisplayState.PREGAME,
                        countdown=self._create_countdown_data(game)
                    )
                else:
                    # Game is too far in the future
                    return DisplayContext(
                        state=DisplayState.IDLE,
                        idle=IdleData(
                            message=f"Next game in {int(hours_until)}h",
                            current_time=datetime.now()
                        )
                    )
            
            elif game.is_final:
                self.current_display_state = DisplayState.FINAL
                return DisplayContext(
                    state=DisplayState.FINAL,
                    scoreboard=self._create_scoreboard_data(game)
                )
            
            # Fallback to idle
            return DisplayContext(
                state=DisplayState.IDLE,
                idle=IdleData(message="No active games", current_time=datetime.now())
            )
            
        except Exception as e:
            logger.error(f"Error getting display context: {e}")
            self.error_count += 1
            
            return DisplayContext(
                state=DisplayState.ERROR,
                error=ErrorData(
                    error_message=f"API Error: {str(e)[:50]}",
                    error_code="API_FAILED",
                    retry_in=min(60 * self.error_count, 300)  # Exponential backoff up to 5 min
                )
            )
    
    def should_refresh(self) -> bool:
        """Check if it's time to refresh the data."""
        return datetime.now() >= self.next_refresh
    
    def schedule_next_refresh(self, context: DisplayContext):
        """Schedule the next refresh based on the current state."""
        now = datetime.now()
        
        if context.state == DisplayState.LIVE:
            # Refresh live games more frequently
            self.next_refresh = now + timedelta(seconds=self.config.api.update_interval)
        elif context.state == DisplayState.PREGAME:
            # Refresh pregame less frequently, but more often as game approaches
            if context.countdown and context.countdown.total_minutes_until <= 60:
                self.next_refresh = now + timedelta(seconds=30)  # Every 30 seconds in final hour
            else:
                self.next_refresh = now + timedelta(minutes=5)   # Every 5 minutes otherwise
        elif context.state == DisplayState.ERROR:
            # Retry based on error data
            retry_seconds = context.error.retry_in if context.error else 60
            self.next_refresh = now + timedelta(seconds=retry_seconds)
        else:
            # Idle or final states - refresh less frequently
            self.next_refresh = now + timedelta(minutes=15)
    
    def get_status_summary(self) -> Dict[str, Any]:
        """Get a summary of the current state for debugging/monitoring."""
        return {
            'current_state': self.current_display_state.value if self.current_display_state else None,
            'current_game': f"{self.current_game.away_team.abbreviation}@{self.current_game.home_team.abbreviation}" if self.current_game else None,
            'last_update': self.last_update.isoformat() if self.last_update else None,
            'next_refresh': self.next_refresh.isoformat(),
            'error_count': self.error_count,
            'favorite_teams': self.favorite_teams,
            'games_tracked': len(self.game_history)
        }