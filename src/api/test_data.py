#!/usr/bin/env python3

import random
from datetime import datetime, timedelta, timezone
from typing import List

from .wnba_api import WNBAGame, GameTeam, GameStatus, GameClock


class TestDataGenerator:
    """Generate fake WNBA game data for testing and demonstration."""
    
    TEAM_NAMES = {
        'SEA': 'Seattle Storm',
        'MIN': 'Minnesota Lynx', 
        'NY': 'New York Liberty',
        'LAS': 'Las Vegas Aces',
        'ATL': 'Atlanta Dream',
        'CHI': 'Chicago Sky',
        'IND': 'Indiana Fever',
        'PHX': 'Phoenix Mercury',
        'WAS': 'Washington Mystics',
        'DAL': 'Dallas Wings',
        'CONN': 'Connecticut Sun'
    }
    
    @classmethod
    def create_live_game(cls, away_team: str = "SEA", home_team: str = "MIN") -> WNBAGame:
        """Create a fake live WNBA game."""
        # Generate realistic scores
        period = random.randint(1, 4)
        away_score = random.randint(45, 95)
        home_score = random.randint(45, 95)
        
        # Random game clock
        if period <= 4:
            minutes = random.randint(0, 10)
            seconds = random.randint(0, 59)
            clock = f"{minutes}:{seconds:02d}"
        else:
            clock = "5:00"  # Overtime
        
        # Create teams
        away = GameTeam(
            id=f"{away_team}_ID",
            name=cls.TEAM_NAMES.get(away_team, away_team),
            location=cls.TEAM_NAMES.get(away_team, away_team).split()[0],
            abbreviation=away_team,
            logo="",
            score=away_score
        )
        
        home = GameTeam(
            id=f"{home_team}_ID", 
            name=cls.TEAM_NAMES.get(home_team, home_team),
            location=cls.TEAM_NAMES.get(home_team, home_team).split()[0],
            abbreviation=home_team,
            logo="",
            score=home_score
        )
        
        # Create game status
        period_text = f"{period}Q" if period <= 4 else f"OT{period-4}"
        status = GameStatus(
            state="in",
            detail=f"{clock} - {period_text}",
            short_detail=f"{period_text}",
            completed=False
        )
        
        # Create clock
        game_clock = GameClock(
            display_clock=clock,
            period=period
        )
        
        return WNBAGame(
            id="test_live_game",
            date=datetime.now(timezone.utc),
            status=status,
            clock=game_clock,
            home_team=home,
            away_team=away,
            season="2025",
            week=15
        )
    
    @classmethod  
    def create_pregame(cls, away_team: str = "NY", home_team: str = "LAS", hours_until: float = 1.5) -> WNBAGame:
        """Create a fake pregame."""
        game_time = datetime.now(timezone.utc) + timedelta(hours=hours_until)
        
        away = GameTeam(
            id=f"{away_team}_ID",
            name=cls.TEAM_NAMES.get(away_team, away_team),
            location=cls.TEAM_NAMES.get(away_team, away_team).split()[0], 
            abbreviation=away_team,
            logo="",
            score=0
        )
        
        home = GameTeam(
            id=f"{home_team}_ID",
            name=cls.TEAM_NAMES.get(home_team, home_team), 
            location=cls.TEAM_NAMES.get(home_team, home_team).split()[0],
            abbreviation=home_team,
            logo="",
            score=0
        )
        
        time_str = game_time.strftime("%-I:%M %p ET")
        status = GameStatus(
            state="pre",
            detail=time_str,
            short_detail="Pregame",
            completed=False
        )
        
        clock = GameClock(
            display_clock="",
            period=0
        )
        
        return WNBAGame(
            id="test_pregame",
            date=game_time,
            status=status, 
            clock=clock,
            home_team=home,
            away_team=away,
            season="2025",
            week=15
        )