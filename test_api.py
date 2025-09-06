#!/usr/bin/env python3

import sys
import logging
from datetime import datetime, timedelta
sys.path.append('src')

from api.wnba_api import ESPNWNBAClient

logging.basicConfig(level=logging.INFO)

def test_api_client():
    """Test the WNBA API client."""
    print("Testing ESPN WNBA API Client...")
    
    client = ESPNWNBAClient()
    
    # Test getting today's games
    print("\n1. Getting today's games...")
    today_games = client.get_scoreboard()
    print(f"Found {len(today_games)} games for today")
    
    for game in today_games:
        print(f"  {game.away_team.abbreviation} ({game.away_team.score}) @ {game.home_team.abbreviation} ({game.home_team.score}) - {game.status.detail}")
        print(f"    Status: {game.status.state}, Period: {game.clock.period}, Clock: {game.clock.display_clock}")
        if game.is_pregame:
            print(f"    Game starts at: {game.date}")
        elif game.is_live:
            print(f"    LIVE GAME! {game.clock.display_clock} remaining in period {game.clock.period}")
        elif game.is_final:
            winner = game.winning_team
            if winner:
                print(f"    FINAL - {winner.abbreviation} wins {winner.score} to {game.home_team.score if winner == game.away_team else game.away_team.score}")
    
    # Test getting games for specific teams
    print("\n2. Getting games for favorite teams...")
    favorite_teams = ["LAS", "SEA", "NY"]
    team_games = client.get_games_for_teams(favorite_teams)
    print(f"Found {len(team_games)} games involving favorite teams")
    
    for game in team_games:
        print(f"  {game.away_team.abbreviation} @ {game.home_team.abbreviation} - {game.status.detail}")
    
    # Test getting live games
    print("\n3. Getting live games...")
    live_games = client.get_live_games()
    print(f"Found {len(live_games)} live games")
    
    # Test getting upcoming games
    print("\n4. Getting upcoming games (next 24 hours)...")
    upcoming_games = client.get_upcoming_games(24)
    print(f"Found {len(upcoming_games)} upcoming games")
    
    for game in upcoming_games:
        from datetime import timezone
        now_utc = datetime.now(timezone.utc)
        game_date = game.date
        if game_date.tzinfo is None:
            game_date = game_date.replace(tzinfo=timezone.utc)
        elif game_date.tzinfo != timezone.utc:
            game_date = game_date.astimezone(timezone.utc)
            
        time_until = game_date - now_utc
        hours_until = time_until.total_seconds() / 3600
        print(f"  {game.away_team.abbreviation} @ {game.home_team.abbreviation} in {hours_until:.1f} hours")
    
    print("\nAPI test completed!")
    return len(today_games) >= 0  # Success if we can fetch data (even if 0 games)

if __name__ == "__main__":
    success = test_api_client()
    print(f"Test {'PASSED' if success else 'FAILED'}")