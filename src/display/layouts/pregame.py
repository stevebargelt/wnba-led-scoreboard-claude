#!/usr/bin/env python3

import logging
from datetime import datetime
from typing import Tuple

from display.renderer import MatrixRenderer, Color
from display.graphics import get_logo_manager
from api.data_models import CountdownData

logger = logging.getLogger(__name__)


class PregameLayout:
    """Layout manager for pregame countdown display."""
    
    def __init__(self, renderer: MatrixRenderer):
        """
        Initialize pregame layout.
        
        Args:
            renderer: Matrix renderer instance
        """
        self.renderer = renderer
        self.rows = renderer.rows
        self.cols = renderer.cols
        self.logo_manager = get_logo_manager()
        
    def _draw_team_vs_team(self, countdown: CountdownData, y_pos: int):
        """Draw team matchup (e.g., 'NY @ SEA')."""
        matchup_text = f"{countdown.away_team} @ {countdown.home_team}"
        
        # Calculate centered position
        text_width = len(matchup_text) * 4  # Rough estimate
        x_start = max(0, (self.cols - text_width) // 2)
        
        self.renderer.draw_text(x_start, y_pos, matchup_text, *Color.WHITE)
    
    def _draw_team_vs_team_compact(self, text: str, y_pos: int):
        """Draw compact team info and countdown."""
        # Calculate centered position
        text_width = len(text) * 4  # Rough estimate
        x_start = max(0, (self.cols - text_width) // 2)
        
        self.renderer.draw_text(x_start, y_pos, text, *Color.YELLOW)
    
    def _draw_countdown_large(self, countdown: CountdownData, y_pos: int):
        """Draw large countdown timer."""
        countdown_text = countdown.countdown_text
        
        # Use larger spacing for countdown
        text_width = len(countdown_text) * 6  # Wider spacing for time
        x_start = max(0, (self.cols - text_width) // 2)
        
        # Draw countdown in bright color
        self.renderer.draw_text(x_start, y_pos, countdown_text, *Color.YELLOW)
    
    def _draw_countdown_compact(self, countdown: CountdownData, y_pos: int):
        """Draw compact countdown for smaller displays."""
        if countdown.hours_until > 0:
            time_text = f"{countdown.hours_until}H{countdown.minutes_until}M"
        else:
            time_text = f"{countdown.minutes_until}M"
        
        text_width = len(time_text) * 4
        x_start = max(0, (self.cols - text_width) // 2)
        
        self.renderer.draw_text(x_start, y_pos, time_text, *Color.CYAN)
    
    def _draw_game_time(self, countdown: CountdownData, y_pos: int):
        """Draw the actual game start time."""
        # Format game time (e.g., "10:00 PM")
        game_time_local = countdown.game_time.astimezone()  # Convert to local timezone
        time_str = game_time_local.strftime("%I:%M %p")
        
        text_width = len(time_str) * 4
        x_start = max(0, (self.cols - text_width) // 2)
        
        self.renderer.draw_text(x_start, y_pos, time_str, *Color.WHITE)
    
    def _draw_team_colors_bars(self, countdown: CountdownData):
        """Draw colored bars representing each team."""
        # Draw away team color bar on left
        bar_width = 3
        self.renderer.fill_rectangle(0, 0, bar_width, self.rows, *countdown.away_color)
        
        # Draw home team color bar on right
        self.renderer.fill_rectangle(self.cols - bar_width, 0, bar_width, self.rows, *countdown.home_color)
    
    def _draw_animated_dots(self, frame_count: int):
        """Draw animated dots to show the display is active."""
        # Simple animation with 3 dots
        dots_to_show = (frame_count // 30) % 4  # Change every ~1 second at 30fps
        
        dot_y = self.rows - 3
        dot_spacing = 2
        total_width = dots_to_show * dot_spacing
        start_x = (self.cols - total_width) // 2
        
        for i in range(dots_to_show):
            x = start_x + (i * dot_spacing)
            if 0 <= x < self.cols:
                self.renderer.set_pixel(x, dot_y, *Color.GREEN)
    
    def render_64x32(self, countdown: CountdownData, frame_count: int = 0):
        """Render pregame layout for 64x32 display."""
        self.renderer.clear()
        
        # Draw team color bars
        self._draw_team_colors_bars(countdown)
        
        # Layout for 64x32 with large logos:
        # Row 2:  Away logo (16x16)    Home logo (16x16)
        # Row 20: Team names and countdown
        # Row 28: Game time
        
        # Away team logo (left) - 16x16 pixels
        away_logo_x = 6
        self.logo_manager.draw_logo(self.renderer, countdown.away_team, away_logo_x, 2, 16, 16)
        
        # Home team logo (right) - 16x16 pixels  
        home_logo_x = self.cols - 22  # 16 for logo + 6 margin
        self.logo_manager.draw_logo(self.renderer, countdown.home_team, home_logo_x, 2, 16, 16)
        
        # Team matchup and countdown on same line
        matchup_text = f"{countdown.away_team}@{countdown.home_team} {countdown.countdown_text}"
        self._draw_team_vs_team_compact(matchup_text, 20)
        
        # Game time
        self._draw_game_time(countdown, 28)
    
    def render_32x32(self, countdown: CountdownData, frame_count: int = 0):
        """Render pregame layout for 32x32 display."""
        self.renderer.clear()
        
        # Compact layout for smaller display:
        # Row 6:  Team matchup
        # Row 15: Compact countdown
        # Row 24: Game time
        # Row 29: Animated dots
        
        self._draw_team_vs_team(countdown, 6)
        self._draw_countdown_compact(countdown, 15)
        self._draw_game_time(countdown, 24)
        self._draw_animated_dots(frame_count)
    
    def render(self, countdown: CountdownData, frame_count: int = 0):
        """
        Render the pregame countdown display.
        
        Args:
            countdown: Countdown data to display
            frame_count: Current frame for animations
        """
        if countdown is None:
            logger.warning("No countdown data provided")
            return
        
        try:
            # Choose layout based on display dimensions
            if self.cols >= 64:
                self.render_64x32(countdown, frame_count)
            else:
                self.render_32x32(countdown, frame_count)
            
            # Refresh the display
            self.renderer.refresh()
            
        except Exception as e:
            logger.error(f"Error rendering pregame layout: {e}")
            # Draw error message
            self.renderer.clear()
            self.renderer.draw_text(2, 15, "ERROR", *Color.RED)
            self.renderer.refresh()


def create_test_countdown() -> CountdownData:
    """Create test countdown data for development."""
    from datetime import timedelta
    
    return CountdownData(
        away_team="NY",
        home_team="SEA", 
        game_time=datetime.now() + timedelta(hours=1, minutes=30),
        time_until=timedelta(hours=1, minutes=30),
        away_color=(134, 206, 188),  # NY Liberty teal
        home_color=(44, 82, 52)      # Seattle Storm green
    )