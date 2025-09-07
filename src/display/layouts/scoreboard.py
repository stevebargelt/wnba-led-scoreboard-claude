#!/usr/bin/env python3

import logging
from datetime import datetime
from typing import Tuple

from display.renderer import MatrixRenderer, Color
from display.graphics import get_logo_manager
from api.data_models import ScoreboardData

logger = logging.getLogger(__name__)


class ScoreboardLayout:
    """Layout manager for live game scoreboard display."""
    
    def __init__(self, renderer: MatrixRenderer):
        """
        Initialize scoreboard layout.
        
        Args:
            renderer: Matrix renderer instance
        """
        self.renderer = renderer
        self.rows = renderer.rows
        self.cols = renderer.cols
        self.logo_manager = get_logo_manager()
        
    def _draw_team_score(self, team: str, score: int, x: int, y: int, color: Tuple[int, int, int]):
        """Draw team abbreviation and score."""
        # Draw team name
        self.renderer.draw_text(x, y, team, *color)
        
        # Draw score below team name
        score_text = str(score)
        self.renderer.draw_text(x, y + 8, score_text, *color)
    
    def _draw_period_and_time(self, scoreboard: ScoreboardData, x: int, y: int):
        """Draw period and time remaining."""
        # Draw period (e.g., "Q2")
        period_text = f"Q{scoreboard.period}" if scoreboard.period <= 4 else f"OT{scoreboard.period - 4}"
        self.renderer.draw_text(x, y, period_text, *Color.WHITE)
        
        # Draw time
        time_text = scoreboard.time_remaining
        # Truncate if too long
        if len(time_text) > 6:
            time_text = time_text[:6]
        
        self.renderer.draw_text(x, y + 8, time_text, *Color.CYAN)
    
    def _draw_score_separator(self, x: int, y: int, leading_team: str = None):
        """Draw separator between scores (e.g., '-' or highlighted for leader)."""
        separator_color = Color.YELLOW if leading_team else Color.WHITE
        self.renderer.draw_text(x, y, "-", *separator_color)
    
    def _draw_team_color_indicators(self, scoreboard: ScoreboardData):
        """Draw team color indicators on the edges."""
        indicator_width = 2
        
        # Away team indicator on left
        self.renderer.fill_rectangle(0, 0, indicator_width, self.rows, *scoreboard.away_color)
        
        # Home team indicator on right
        self.renderer.fill_rectangle(self.cols - indicator_width, 0, indicator_width, self.rows, *scoreboard.home_color)
    
    
    def _draw_status_text(self, status: str, y: int):
        """Draw game status text if it fits."""
        if len(status) * 4 <= self.cols - 4:
            x_center = (self.cols - len(status) * 4) // 2
            self.renderer.draw_text(x_center, y, status, *Color.ORANGE)
    
    def render_64x32(self, scoreboard: ScoreboardData, frame_count: int = 0):
        """Render scoreboard layout for 64x32 display."""
        self.renderer.clear()
        
        # Draw team color indicators
        self._draw_team_color_indicators(scoreboard)
        
        # Layout for 64x32 with large 20x20 logos:
        # Row 2:  Away logo (20x20) starts at col 4
        # Row 2:  Home logo (20x20) at same position on right
        # Row 10: Quarter/Time centered between logos
        # Row 24: Scores below logos
        
        # Away team logo (left side) - 20x20 pixels starting at column 4, row 2
        away_logo_x = 4
        away_logo_y = 2
        self.logo_manager.draw_logo(self.renderer, scoreboard.away_team, away_logo_x, away_logo_y, 20, 20)
        
        # Home team logo (right side) - 20x20 pixels, same relative position
        home_logo_x = self.cols - 24  # 20 for logo + 4 margin (mirrors left side)
        home_logo_y = 2
        self.logo_manager.draw_logo(self.renderer, scoreboard.home_team, home_logo_x, home_logo_y, 20, 20)
        
        # Period and time centered between logos
        center_x = (self.cols - 12) // 2  # Center of 64-pixel display
        self._draw_period_and_time(scoreboard, center_x, 10)
        
        # Away score below logo
        away_score_x = away_logo_x + 8  # Center score under 20px logo
        self.renderer.draw_text(away_score_x, 24, str(scoreboard.away_score), *scoreboard.away_color)
        
        # Home score below logo
        home_score_x = home_logo_x + 8  # Center score under 20px logo
        self.renderer.draw_text(home_score_x, 24, str(scoreboard.home_score), *scoreboard.home_color)
    
    def render_32x32(self, scoreboard: ScoreboardData, frame_count: int = 0):
        """Render scoreboard layout for 32x32 display (compact)."""
        self.renderer.clear()
        
        # Compact layout for smaller display:
        # Row 4:  Away vs Home
        # Row 12: Scores with separator
        # Row 20: Period/Time
        # Row 28: Leader indicator
        
        # Team matchup
        matchup = f"{scoreboard.away_team}@{scoreboard.home_team}"
        matchup_x = (self.cols - len(matchup) * 4) // 2
        self.renderer.draw_text(matchup_x, 4, matchup, *Color.WHITE)
        
        # Scores with separator
        score_text = f"{scoreboard.away_score}-{scoreboard.home_score}"
        score_x = (self.cols - len(score_text) * 4) // 2
        
        # Color the scores based on who's leading
        if scoreboard.away_score > scoreboard.home_score:
            away_color = Color.GREEN
            home_color = Color.WHITE
        elif scoreboard.home_score > scoreboard.away_score:
            away_color = Color.WHITE
            home_color = Color.GREEN
        else:
            away_color = home_color = Color.YELLOW
        
        # Draw away score
        self.renderer.draw_text(score_x, 12, str(scoreboard.away_score), *away_color)
        # Draw separator
        sep_x = score_x + len(str(scoreboard.away_score)) * 4
        self.renderer.draw_text(sep_x, 12, "-", *Color.WHITE)
        # Draw home score
        home_score_x = sep_x + 4
        self.renderer.draw_text(home_score_x, 12, str(scoreboard.home_score), *home_color)
        
        # Period and time
        period_text = f"Q{scoreboard.period}"
        if len(scoreboard.time_remaining) <= 4:
            period_time_text = f"{period_text} {scoreboard.time_remaining}"
        else:
            period_time_text = period_text  # Just period if time is too long
        
        pt_x = (self.cols - len(period_time_text) * 4) // 2
        self.renderer.draw_text(pt_x, 20, period_time_text, *Color.CYAN)
        
        # Leader indicators removed to save space for larger logos
    
    def render(self, scoreboard: ScoreboardData, frame_count: int = 0):
        """
        Render the live scoreboard display.
        
        Args:
            scoreboard: Scoreboard data to display
            frame_count: Current frame for animations
        """
        if scoreboard is None:
            logger.warning("No scoreboard data provided")
            return
        
        try:
            # Choose layout based on display dimensions
            if self.cols >= 64:
                self.render_64x32(scoreboard, frame_count)
            else:
                self.render_32x32(scoreboard, frame_count)
            
            # Refresh the display
            self.renderer.refresh()
            
        except Exception as e:
            logger.error(f"Error rendering scoreboard layout: {e}")
            # Draw error message
            self.renderer.clear()
            self.renderer.draw_text(2, 15, "ERROR", *Color.RED)
            self.renderer.refresh()


def create_test_scoreboard() -> ScoreboardData:
    """Create test scoreboard data for development."""
    return ScoreboardData(
        away_team="NY",
        away_score=78,
        home_team="SEA", 
        home_score=82,
        period=4,
        time_remaining="2:35",
        away_color=(134, 206, 188),  # NY Liberty teal
        home_color=(44, 82, 52),     # Seattle Storm green
        status_text="4th Quarter"
    )