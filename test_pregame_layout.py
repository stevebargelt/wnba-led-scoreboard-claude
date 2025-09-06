#!/usr/bin/env python3

import sys
import time
import logging
sys.path.append('src')

from display.renderer import MatrixRenderer
from display.layouts.pregame import PregameLayout, create_test_countdown

logging.basicConfig(level=logging.INFO)

def test_pregame_layout():
    """Test the pregame countdown layout."""
    print("Testing Pregame Layout...")
    
    # Initialize renderer
    renderer = MatrixRenderer(rows=32, cols=64, use_emulator=True)
    
    if not renderer.initialize():
        print("Failed to initialize renderer")
        return False
    
    print("Renderer initialized successfully!")
    
    # Create pregame layout
    layout = PregameLayout(renderer)
    
    # Create test countdown data
    countdown = create_test_countdown()
    print(f"Test countdown: {countdown.away_team} @ {countdown.home_team}")
    print(f"Time until game: {countdown.countdown_text}")
    
    # Test rendering with animation frames
    print("Rendering pregame layout with animation...")
    
    try:
        for frame in range(120):  # 4 seconds of animation at 30fps
            layout.render(countdown, frame)
            time.sleep(1/30)  # 30 FPS
        
        print("Pregame layout test completed! Check emulator window.")
        
    except KeyboardInterrupt:
        pass
    finally:
        renderer.shutdown()
    
    return True

if __name__ == "__main__":
    success = test_pregame_layout()
    print(f"Test {'PASSED' if success else 'FAILED'}")