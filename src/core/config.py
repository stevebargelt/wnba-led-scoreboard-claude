#!/usr/bin/env python3

import json
import logging
import os
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class DisplayConfig:
    """Display configuration settings."""
    brightness: int = 75
    refresh_rate: int = 30
    led_rows: int = 32
    led_cols: int = 64
    emulator: bool = True


@dataclass
class ApiConfig:
    """API configuration settings."""
    update_interval: int = 15
    pregame_hours: int = 2
    timeout: int = 10


@dataclass 
class LoggingConfig:
    """Logging configuration settings."""
    level: str = "INFO"
    file: str = "wnba_scoreboard.log"


@dataclass
class Team:
    """Team information."""
    name: str
    abbreviation: str
    primary_color: str
    secondary_color: str


class Config:
    """Main configuration class for WNBA LED Scoreboard."""
    
    def __init__(self, config_dir: Optional[str] = None):
        """
        Initialize configuration.
        
        Args:
            config_dir: Path to configuration directory. If None, uses default location.
        """
        self.config_dir = Path(config_dir) if config_dir else self._get_default_config_dir()
        self.config_file = self.config_dir / "config.json"
        self.teams_file = self.config_dir / "teams.json"
        
        # Configuration sections
        self.display = DisplayConfig()
        self.api = ApiConfig()
        self.logging = LoggingConfig()
        self.favorite_teams: List[str] = []
        self.teams: Dict[str, Team] = {}
        
        # Load configuration
        self.load()
    
    def _get_default_config_dir(self) -> Path:
        """Get the default configuration directory."""
        # First check if we're in the project root
        current_dir = Path.cwd()
        config_dir = current_dir / "config"
        if config_dir.exists():
            return config_dir
            
        # If running from src/, go up one level
        parent_config = current_dir.parent / "config"
        if parent_config.exists():
            return parent_config
            
        # If all else fails, use current directory
        return current_dir
    
    def load(self):
        """Load configuration from files."""
        try:
            self._load_main_config()
            self._load_teams_config()
            logger.info("Configuration loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load configuration: {e}")
            raise
    
    def _load_main_config(self):
        """Load main configuration from config.json."""
        if not self.config_file.exists():
            logger.warning(f"Config file not found: {self.config_file}")
            return
            
        try:
            with open(self.config_file, 'r') as f:
                config_data = json.load(f)
            
            # Load favorite teams
            self.favorite_teams = config_data.get('favorite_teams', [])
            
            # Load display config
            if 'display' in config_data:
                display_data = config_data['display']
                self.display = DisplayConfig(
                    brightness=display_data.get('brightness', 75),
                    refresh_rate=display_data.get('refresh_rate', 30),
                    led_rows=display_data.get('led_rows', 32),
                    led_cols=display_data.get('led_cols', 64),
                    emulator=display_data.get('emulator', True)
                )
            
            # Load API config
            if 'api' in config_data:
                api_data = config_data['api']
                self.api = ApiConfig(
                    update_interval=api_data.get('update_interval', 15),
                    pregame_hours=api_data.get('pregame_hours', 2),
                    timeout=api_data.get('timeout', 10)
                )
            
            # Load logging config
            if 'logging' in config_data:
                logging_data = config_data['logging']
                self.logging = LoggingConfig(
                    level=logging_data.get('level', 'INFO'),
                    file=logging_data.get('file', 'wnba_scoreboard.log')
                )
                
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in config file: {e}")
            raise
        except Exception as e:
            logger.error(f"Error reading config file: {e}")
            raise
    
    def _load_teams_config(self):
        """Load teams configuration from teams.json."""
        if not self.teams_file.exists():
            logger.warning(f"Teams file not found: {self.teams_file}")
            return
            
        try:
            with open(self.teams_file, 'r') as f:
                teams_data = json.load(f)
            
            if 'teams' in teams_data:
                for abbrev, team_data in teams_data['teams'].items():
                    self.teams[abbrev] = Team(
                        name=team_data.get('name', ''),
                        abbreviation=team_data.get('abbreviation', abbrev),
                        primary_color=team_data.get('primary_color', '#FFFFFF'),
                        secondary_color=team_data.get('secondary_color', '#000000')
                    )
                    
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in teams file: {e}")
            raise
        except Exception as e:
            logger.error(f"Error reading teams file: {e}")
            raise
    
    def get_team(self, abbreviation: str) -> Optional[Team]:
        """Get team information by abbreviation."""
        return self.teams.get(abbreviation)
    
    def get_favorite_teams(self) -> List[Team]:
        """Get list of favorite teams in priority order."""
        teams = []
        for abbrev in self.favorite_teams:
            team = self.get_team(abbrev)
            if team:
                teams.append(team)
        return teams
    
    def is_favorite_team(self, abbreviation: str) -> bool:
        """Check if a team is in the favorites list."""
        return abbreviation in self.favorite_teams
    
    def get_favorite_team_priority(self, abbreviation: str) -> int:
        """Get the priority of a favorite team (lower number = higher priority)."""
        try:
            return self.favorite_teams.index(abbreviation)
        except ValueError:
            return 999  # Not a favorite team
    
    def save(self):
        """Save current configuration to files."""
        try:
            # Create config directory if it doesn't exist
            self.config_dir.mkdir(parents=True, exist_ok=True)
            
            # Save main config
            config_data = {
                'favorite_teams': self.favorite_teams,
                'display': {
                    'brightness': self.display.brightness,
                    'refresh_rate': self.display.refresh_rate,
                    'led_rows': self.display.led_rows,
                    'led_cols': self.display.led_cols,
                    'emulator': self.display.emulator
                },
                'api': {
                    'update_interval': self.api.update_interval,
                    'pregame_hours': self.api.pregame_hours,
                    'timeout': self.api.timeout
                },
                'logging': {
                    'level': self.logging.level,
                    'file': self.logging.file
                }
            }
            
            with open(self.config_file, 'w') as f:
                json.dump(config_data, f, indent=2)
            
            logger.info(f"Configuration saved to {self.config_file}")
            
        except Exception as e:
            logger.error(f"Failed to save configuration: {e}")
            raise


# Global configuration instance
_config: Optional[Config] = None


def get_config(config_dir: Optional[str] = None) -> Config:
    """Get the global configuration instance."""
    global _config
    if _config is None:
        _config = Config(config_dir)
    return _config


def reload_config(config_dir: Optional[str] = None):
    """Reload configuration from files."""
    global _config
    _config = Config(config_dir)