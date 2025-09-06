#!/usr/bin/env python3

import sys
import time
import logging
sys.path.append('src')

from display.renderer import MatrixRenderer
from display.layouts.scoreboard import ScoreboardLayout, create_test_scoreboard

logging.basicConfig(level=logging.INFO)

def test_scoreboard_layout():
    """Test the live scoreboard layout."""
    print("Testing Scoreboard Layout...")
    
    # Initialize renderer
    renderer = MatrixRenderer(rows=32, cols=64, use_emulator=True)
    
    if not renderer.initialize():
        print("Failed to initialize renderer")
        return False
    
    print("Renderer initialized successfully!")
    
    # Create scoreboard layout
    layout = ScoreboardLayout(renderer)
    
    # Create test scoreboard data
    scoreboard = create_test_scoreboard()
    print(f"Test scoreboard: {scoreboard.away_team} ({scoreboard.away_score}) @ {scoreboard.home_team} ({scoreboard.home_score})")
    print(f"Period {scoreboard.period}, Time: {scoreboard.time_remaining}")
    print(f"Leading: {scoreboard.leader} by {scoreboard.lead_amount}")
    
    # Test rendering
    print("Rendering scoreboard layout...")
    
    try:
        # Render for 3 seconds
        for frame in range(90):  # 3 seconds at 30fps
            layout.render(scoreboard, frame)
            time.sleep(1/30)  # 30 FPS
        
        print("Scoreboard layout test completed! Check emulator window.")
        
    except KeyboardInterrupt:
        pass
    finally:
        renderer.shutdown()
    
    return True

if __name__ == "__main__":
    success = test_scoreboard_layout()
    print(f"Test {'PASSED' if success else 'FAILED'}")