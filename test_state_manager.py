#!/usr/bin/env python3

import sys
import logging
sys.path.append('src')

from core.state_manager import WNBAStateManager
from api.data_models import DisplayState

logging.basicConfig(level=logging.INFO)

def test_state_manager():
    """Test the WNBA state manager."""
    print("Testing WNBA State Manager...")
    
    # Initialize state manager
    state_manager = WNBAStateManager()
    
    # Get current display context
    print("\n1. Getting current display context...")
    context = state_manager.get_current_display_context()
    
    print(f"Display State: {context.state.value}")
    print(f"Last Updated: {context.last_updated}")
    
    if context.state == DisplayState.LIVE:
        sb = context.scoreboard
        print(f"LIVE GAME: {sb.away_team} ({sb.away_score}) @ {sb.home_team} ({sb.home_score})")
        print(f"Period {sb.period}, Time: {sb.time_remaining}")
        print(f"Status: {sb.status_text}")
        if sb.leader:
            print(f"Leading: {sb.leader} by {sb.lead_amount}")
    
    elif context.state == DisplayState.PREGAME:
        cd = context.countdown
        print(f"UPCOMING: {cd.away_team} @ {cd.home_team}")
        print(f"Game time: {cd.game_time}")
        print(f"Time until: {cd.countdown_text}")
    
    elif context.state == DisplayState.IDLE:
        print(f"IDLE: {context.idle.message}")
        if context.idle.current_time:
            print(f"Current time: {context.idle.current_time}")
    
    elif context.state == DisplayState.ERROR:
        print(f"ERROR: {context.error.error_message}")
        print(f"Code: {context.error.error_code}")
        print(f"Retry in: {context.error.retry_in} seconds")
    
    # Test refresh scheduling
    print("\n2. Testing refresh scheduling...")
    state_manager.schedule_next_refresh(context)
    print(f"Should refresh: {state_manager.should_refresh()}")
    print(f"Next refresh: {state_manager.next_refresh}")
    
    # Get status summary
    print("\n3. State manager status:")
    status = state_manager.get_status_summary()
    for key, value in status.items():
        print(f"  {key}: {value}")
    
    print("\nState manager test completed!")
    return True

if __name__ == "__main__":
    success = test_state_manager()
    print(f"Test {'PASSED' if success else 'FAILED'}")