#!/usr/bin/env python3

import logging
from datetime import datetime
from typing import Optional

from display.renderer import MatrixRenderer, Color
from api.data_models import IdleData

logger = logging.getLogger(__name__)


class IdleLayout:
    """Layout manager for idle state display."""
    
    def __init__(self, renderer: MatrixRenderer):
        """
        Initialize idle layout.
        
        Args:
            renderer: Matrix renderer instance
        """
        self.renderer = renderer
        self.rows = renderer.rows
        self.cols = renderer.cols
        
    def _draw_centered_text(self, text: str, y: int, color: tuple = None):
        """Draw text centered horizontally."""
        if color is None:
            color = Color.WHITE
        
        text_width = len(text) * 4  # Rough estimate
        x_start = max(0, (self.cols - text_width) // 2)
        
        self.renderer.draw_text(x_start, y, text, *color)
    
    def _draw_clock(self, current_time: datetime, y: int):
        """Draw current time."""
        if current_time is None:
            current_time = datetime.now()
        
        # Format time (12-hour with AM/PM)
        time_str = current_time.strftime("%I:%M %p")
        self._draw_centered_text(time_str, y, Color.CYAN)
        
        # Draw date below time
        date_str = current_time.strftime("%m/%d")
        self._draw_centered_text(date_str, y + 8, Color.WHITE)
    
    def _draw_wnba_logo_text(self, y: int):
        """Draw simple WNBA text logo."""
        self._draw_centered_text("WNBA", y, Color.ORANGE)
    
    def _draw_animated_border(self, frame_count: int):
        """Draw an animated border effect."""
        # Simple animated border using corner pixels
        animation_speed = 60  # Change every 2 seconds at 30fps
        phase = (frame_count // animation_speed) % 4
        
        border_color = Color.GREEN
        
        # Corner positions
        corners = [
            (0, 0), (self.cols-1, 0),  # Top corners
            (0, self.rows-1), (self.cols-1, self.rows-1)  # Bottom corners
        ]
        
        # Light up corners in sequence
        for i, (x, y) in enumerate(corners):
            if i == phase:
                self.renderer.set_pixel(x, y, *border_color)
    
    def render(self, idle_data: Optional[IdleData], frame_count: int = 0):
        """
        Render the idle display.
        
        Args:
            idle_data: Idle state data
            frame_count: Current frame for animations
        """
        self.renderer.clear()
        
        if idle_data is None:
            idle_data = IdleData()
        
        try:
            if self.cols >= 64:
                # Layout for 64x32 or larger (adjusted for 5-pixel tall characters)
                self._draw_wnba_logo_text(5)  # WNBA at top (rows 5-9)
                
                # Split long messages even for 64-wide displays
                message = idle_data.message
                if len(message) * 4 > self.cols - 8:  # Too long for one line
                    words = message.split()
                    if len(words) >= 3:  # Split into two lines
                        # Try to split roughly in half
                        mid = len(words) // 2
                        line1 = " ".join(words[:mid])
                        line2 = " ".join(words[mid:])
                        
                        self._draw_centered_text(line1, 12, Color.YELLOW)  # rows 12-16
                        self._draw_centered_text(line2, 19, Color.YELLOW)  # rows 19-23
                    else:
                        # Just draw what fits
                        max_chars = (self.cols - 8) // 4
                        short_message = message[:max_chars] if len(message) > max_chars else message
                        self._draw_centered_text(short_message, 15, Color.YELLOW)  # rows 15-19
                else:
                    self._draw_centered_text(message, 15, Color.YELLOW)  # rows 15-19
                
                if idle_data.show_clock:
                    self._draw_clock(idle_data.current_time, 26)  # rows 26-30 (clock is 2 lines)
                    
            else:
                # Compact layout for 32x32
                self._draw_wnba_logo_text(4)
                
                # Split long messages
                message = idle_data.message
                if len(message) > 8:  # Split if too long
                    words = message.split()
                    if len(words) >= 2:
                        line1 = words[0]
                        line2 = " ".join(words[1:])
                        self._draw_centered_text(line1, 14, Color.YELLOW)
                        if len(line2) * 4 <= self.cols:
                            self._draw_centered_text(line2, 22, Color.YELLOW)
                    else:
                        self._draw_centered_text(message[:8], 18, Color.YELLOW)
                else:
                    self._draw_centered_text(message, 18, Color.YELLOW)
            
            # Add subtle animation
            self._draw_animated_border(frame_count)
            
            # Refresh the display
            self.renderer.refresh()
            
        except Exception as e:
            logger.error(f"Error rendering idle layout: {e}")
            # Draw simple error state
            self.renderer.clear()
            self._draw_centered_text("IDLE", 15, Color.WHITE)
            self.renderer.refresh()