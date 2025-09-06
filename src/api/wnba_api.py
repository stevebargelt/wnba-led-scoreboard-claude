#!/usr/bin/env python3

import requests
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class GameTeam:
    """Team information for a game."""
    id: str
    name: str
    location: str
    abbreviation: str
    logo: str
    score: int = 0
    linescores: List[int] = None
    
    def __post_init__(self):
        if self.linescores is None:
            self.linescores = []


@dataclass
class GameStatus:
    """Game status information."""
    state: str  # pre, in, post
    detail: str
    short_detail: str
    completed: bool
    

@dataclass
class GameClock:
    """Game timing information."""
    display_clock: str
    period: int
    period_type: str = "regular"


@dataclass
class WNBAGame:
    """Complete WNBA game information."""
    id: str
    date: datetime
    status: GameStatus
    clock: GameClock
    home_team: GameTeam
    away_team: GameTeam
    season: str
    week: int
    broadcast: List[str] = None
    odds: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.broadcast is None:
            self.broadcast = []
        if self.odds is None:
            self.odds = {}
    
    @property
    def is_pregame(self) -> bool:
        """Check if game is in pregame state."""
        return self.status.state == "pre"
    
    @property
    def is_live(self) -> bool:
        """Check if game is currently live."""
        return self.status.state == "in"
    
    @property
    def is_final(self) -> bool:
        """Check if game is completed."""
        return self.status.completed or self.status.state == "post"
    
    @property
    def winning_team(self) -> Optional[GameTeam]:
        """Get the team that's currently winning or won."""
        if self.home_team.score > self.away_team.score:
            return self.home_team
        elif self.away_team.score > self.home_team.score:
            return self.away_team
        return None


class ESPNWNBAClient:
    """ESPN API client for WNBA data."""
    
    BASE_URL = "http://site.api.espn.com/apis/site/v2/sports/basketball/wnba"
    
    def __init__(self, timeout: int = 10):
        """
        Initialize the ESPN WNBA API client.
        
        Args:
            timeout: Request timeout in seconds
        """
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'WNBA-LED-Scoreboard/1.0'
        })
    
    def _make_request(self, endpoint: str, params: Dict[str, Any] = None) -> Optional[Dict[str, Any]]:
        """Make a request to the ESPN API."""
        url = f"{self.BASE_URL}/{endpoint}"
        
        try:
            logger.debug(f"Making request to: {url} with params: {params}")
            response = self.session.get(url, params=params, timeout=self.timeout)
            response.raise_for_status()
            
            data = response.json()
            logger.debug(f"Received response with {len(str(data))} characters")
            return data
            
        except requests.exceptions.RequestException as e:
            logger.error(f"API request failed: {e}")
            return None
        except ValueError as e:
            logger.error(f"Failed to parse JSON response: {e}")
            return None
    
    def _parse_team_data(self, team_data: Dict[str, Any]) -> GameTeam:
        """Parse team data from API response."""
        team = team_data.get('team', {})
        
        return GameTeam(
            id=str(team.get('id', '')),
            name=team.get('name', ''),
            location=team.get('location', ''),
            abbreviation=team.get('abbreviation', ''),
            logo=team.get('logo', ''),
            score=int(team_data.get('score', 0)),
            linescores=[int(score.get('value', 0)) for score in team_data.get('linescores', [])]
        )
    
    def _parse_game_data(self, game_data: Dict[str, Any]) -> WNBAGame:
        """Parse a single game from the API response."""
        game_id = game_data.get('id', '')
        
        # Parse date
        date_str = game_data.get('date', '')
        try:
            game_date = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
        except ValueError:
            logger.warning(f"Could not parse date: {date_str}")
            game_date = datetime.now()
        
        # Parse status
        status_data = game_data.get('status', {})
        status = GameStatus(
            state=status_data.get('type', {}).get('state', 'unknown'),
            detail=status_data.get('type', {}).get('detail', ''),
            short_detail=status_data.get('type', {}).get('shortDetail', ''),
            completed=status_data.get('type', {}).get('completed', False)
        )
        
        # Parse clock
        clock_data = game_data.get('status', {})
        clock = GameClock(
            display_clock=clock_data.get('displayClock', ''),
            period=int(clock_data.get('period', 1)),
            period_type=clock_data.get('type', {}).get('name', 'regular')
        )
        
        # Parse teams
        competitions = game_data.get('competitions', [])
        if competitions:
            competition = competitions[0]
            competitors = competition.get('competitors', [])
            
            home_team = None
            away_team = None
            
            for competitor in competitors:
                team = self._parse_team_data(competitor)
                if competitor.get('homeAway') == 'home':
                    home_team = team
                else:
                    away_team = team
        
        if not home_team or not away_team:
            logger.warning(f"Could not parse teams for game {game_id}")
            # Create dummy teams to prevent errors
            home_team = GameTeam('', 'Unknown', 'Unknown', 'UNK', '')
            away_team = GameTeam('', 'Unknown', 'Unknown', 'UNK', '')
        
        # Parse additional data
        season_data = game_data.get('season', {})
        season = str(season_data.get('year', ''))
        week = int(season_data.get('week', 0))
        
        # Parse broadcasts
        broadcasts = []
        if competitions and 'broadcasts' in competitions[0]:
            for broadcast in competitions[0]['broadcasts']:
                if 'names' in broadcast:
                    broadcasts.extend(broadcast['names'])
        
        return WNBAGame(
            id=game_id,
            date=game_date,
            status=status,
            clock=clock,
            home_team=home_team,
            away_team=away_team,
            season=season,
            week=week,
            broadcast=broadcasts
        )
    
    def get_scoreboard(self, date: Optional[datetime] = None) -> List[WNBAGame]:
        """
        Get WNBA games for a specific date.
        
        Args:
            date: Date to get games for. If None, uses today.
            
        Returns:
            List of WNBA games
        """
        if date is None:
            date = datetime.now()
        
        date_str = date.strftime('%Y%m%d')
        params = {'dates': date_str}
        
        data = self._make_request('scoreboard', params)
        if not data:
            return []
        
        games = []
        events = data.get('events', [])
        
        for event in events:
            try:
                game = self._parse_game_data(event)
                games.append(game)
                logger.debug(f"Parsed game: {game.away_team.abbreviation} @ {game.home_team.abbreviation}")
            except Exception as e:
                logger.error(f"Error parsing game data: {e}")
                continue
        
        logger.info(f"Retrieved {len(games)} games for {date_str}")
        return games
    
    def get_games_for_teams(self, team_abbreviations: List[str], date: Optional[datetime] = None) -> List[WNBAGame]:
        """
        Get games for specific teams.
        
        Args:
            team_abbreviations: List of team abbreviations to filter for
            date: Date to check. If None, uses today.
            
        Returns:
            List of games involving the specified teams
        """
        all_games = self.get_scoreboard(date)
        
        team_games = []
        for game in all_games:
            if (game.home_team.abbreviation in team_abbreviations or 
                game.away_team.abbreviation in team_abbreviations):
                team_games.append(game)
        
        return team_games
    
    def get_live_games(self) -> List[WNBAGame]:
        """Get all currently live WNBA games."""
        games = self.get_scoreboard()
        return [game for game in games if game.is_live]
    
    def get_upcoming_games(self, hours_ahead: int = 24) -> List[WNBAGame]:
        """
        Get upcoming WNBA games within a time window.
        
        Args:
            hours_ahead: How many hours ahead to look for games
            
        Returns:
            List of upcoming games
        """
        from datetime import timezone
        
        now = datetime.now(timezone.utc)
        end_time = now + timedelta(hours=hours_ahead)
        
        upcoming_games = []
        current_date = now.date()
        end_date = end_time.date()
        
        # Check each day in the range
        check_date = current_date
        while check_date <= end_date:
            games = self.get_scoreboard(datetime.combine(check_date, datetime.min.time()))
            
            for game in games:
                # Convert game.date to UTC if it has timezone info
                game_date = game.date
                if game_date.tzinfo is None:
                    game_date = game_date.replace(tzinfo=timezone.utc)
                elif game_date.tzinfo != timezone.utc:
                    game_date = game_date.astimezone(timezone.utc)
                
                if game.is_pregame and now <= game_date <= end_time:
                    upcoming_games.append(game)
            
            check_date += timedelta(days=1)
        
        return upcoming_games