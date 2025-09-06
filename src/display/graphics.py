#!/usr/bin/env python3

import os
import logging
import requests
from pathlib import Path
from typing import Optional, Dict, Tuple
from PIL import Image
import numpy as np

from .renderer import MatrixRenderer

logger = logging.getLogger(__name__)


class LogoManager:
    """Manages team logos for the LED matrix display."""
    
    def __init__(self, cache_dir: str = "assets/logos"):
        """
        Initialize logo manager.
        
        Args:
            cache_dir: Directory to cache downloaded logos
        """
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.logo_cache: Dict[str, np.ndarray] = {}
        
        # ESPN logo URL template 
        self.logo_url_template = "https://a.espncdn.com/i/teamlogos/wnba/500/{team_abbrev}.png"
        
        logger.info(f"Logo manager initialized with cache dir: {self.cache_dir}")
    
    def _download_logo(self, team_abbrev: str) -> bool:
        """Download a team logo from ESPN."""
        url = self.logo_url_template.format(team_abbrev=team_abbrev.upper())
        logo_file = self.cache_dir / f"{team_abbrev.lower()}.png"
        
        try:
            logger.info(f"Downloading logo for {team_abbrev} from {url}")
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            
            with open(logo_file, 'wb') as f:
                f.write(response.content)
            
            logger.info(f"Downloaded logo: {logo_file}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to download logo for {team_abbrev}: {e}")
            return False
    
    def _load_and_resize_logo(self, team_abbrev: str, width: int, height: int) -> Optional[np.ndarray]:
        """Load and resize a logo to fit the display."""
        logo_file = self.cache_dir / f"{team_abbrev.lower()}.png"
        
        # Download if not cached
        if not logo_file.exists():
            if not self._download_logo(team_abbrev):
                return None
        
        try:
            # Load and resize image
            with Image.open(logo_file) as img:
                # Convert to RGB if needed
                if img.mode != 'RGB':
                    img = img.convert('RGB')
                
                # Resize to fit the specified dimensions
                img = img.resize((width, height), Image.Resampling.LANCZOS)
                
                # Convert to numpy array
                logo_array = np.array(img)
                
                logger.debug(f"Loaded logo {team_abbrev}: {logo_array.shape}")
                return logo_array
                
        except Exception as e:
            logger.error(f"Error processing logo for {team_abbrev}: {e}")
            return None
    
    def get_logo(self, team_abbrev: str, width: int = 12, height: int = 12) -> Optional[np.ndarray]:
        """
        Get a team logo resized for the display.
        
        Args:
            team_abbrev: Team abbreviation (e.g., 'SEA', 'MIN')
            width: Desired width in pixels
            height: Desired height in pixels
            
        Returns:
            RGB array of logo pixels or None if unavailable
        """
        cache_key = f"{team_abbrev.lower()}_{width}x{height}"
        
        # Check cache first
        if cache_key in self.logo_cache:
            return self.logo_cache[cache_key]
        
        # Load and cache the logo
        logo = self._load_and_resize_logo(team_abbrev, width, height)
        if logo is not None:
            self.logo_cache[cache_key] = logo
            
        return logo
    
    def draw_logo(self, renderer: MatrixRenderer, team_abbrev: str, x: int, y: int, 
                  width: int = 12, height: int = 12):
        """
        Draw a team logo on the matrix display.
        
        Args:
            renderer: Matrix renderer instance
            team_abbrev: Team abbreviation
            x: X position to draw logo
            y: Y position to draw logo  
            width: Logo width in pixels
            height: Logo height in pixels
        """
        logo = self.get_logo(team_abbrev, width, height)
        
        if logo is None:
            # Fallback: draw colored rectangle with team initials
            self._draw_logo_fallback(renderer, team_abbrev, x, y, width, height)
            return
        
        try:
            # Draw each pixel of the logo
            for row in range(height):
                for col in range(width):
                    if y + row < renderer.rows and x + col < renderer.cols:
                        r, g, b = logo[row, col]
                        # Skip transparent/white pixels (logo background)
                        if not (r > 240 and g > 240 and b > 240):
                            renderer.set_pixel(x + col, y + row, int(r), int(g), int(b))
                            
        except Exception as e:
            logger.error(f"Error drawing logo for {team_abbrev}: {e}")
            self._draw_logo_fallback(renderer, team_abbrev, x, y, width, height)
    
    def _draw_logo_fallback(self, renderer: MatrixRenderer, team_abbrev: str, 
                           x: int, y: int, width: int, height: int):
        """Draw a simple fallback when logo is unavailable."""
        from core.config import get_config
        
        # Get team colors
        config = get_config()
        team = config.get_team(team_abbrev)
        
        if team:
            try:
                from .renderer import Color
                color = Color.from_hex(team.primary_color)
            except Exception:
                color = (255, 255, 255)  # White fallback
        else:
            color = (255, 255, 255)  # White fallback
        
        # Draw colored rectangle
        renderer.fill_rectangle(x, y, width, height, *color)
        
        # Draw team abbreviation if it fits
        if len(team_abbrev) <= 3 and width >= 12 and height >= 8:
            text_x = x + (width - len(team_abbrev) * 3) // 2
            text_y = y + (height - 5) // 2
            renderer.draw_text(text_x, text_y, team_abbrev, 0, 0, 0)  # Black text
    
    def preload_favorite_logos(self, team_abbreviations: list, width: int = 12, height: int = 12):
        """Preload logos for favorite teams."""
        logger.info(f"Preloading logos for teams: {team_abbreviations}")
        
        for team_abbrev in team_abbreviations:
            logo = self.get_logo(team_abbrev, width, height)
            if logo is not None:
                logger.info(f"Preloaded logo for {team_abbrev}")
            else:
                logger.warning(f"Could not preload logo for {team_abbrev}")


# Global logo manager instance
_logo_manager: Optional[LogoManager] = None


def get_logo_manager() -> LogoManager:
    """Get the global logo manager instance."""
    global _logo_manager
    if _logo_manager is None:
        _logo_manager = LogoManager()
    return _logo_manager