#!/usr/bin/env python3

import sys
import time
import logging
sys.path.append('src')

from display.renderer import MatrixRenderer, Color
from core.config import get_config

logging.basicConfig(level=logging.INFO)

def test_basic_renderer():
    """Test basic matrix renderer functionality."""
    config = get_config()
    
    print("Testing Matrix Renderer...")
    renderer = MatrixRenderer(
        rows=config.display.led_rows,
        cols=config.display.led_cols,
        brightness=config.display.brightness,
        use_emulator=True
    )
    
    if not renderer.initialize():
        print("Failed to initialize renderer")
        return False
    
    print("Renderer initialized successfully!")
    
    # Test basic drawing
    renderer.clear()
    
    # Draw some text
    renderer.draw_text(2, 10, "WNBA", *Color.WHITE)
    renderer.draw_text(2, 20, "TEST", *Color.RED)
    
    # Draw some shapes
    renderer.fill_rectangle(50, 5, 10, 5, *Color.GREEN)
    renderer.set_pixel(55, 25, *Color.BLUE)
    
    # Update display
    renderer.refresh()
    
    print("Basic test display rendered. Check emulator window.")
    print("Press Ctrl+C to exit...")
    
    try:
        # Keep display active for a few seconds
        time.sleep(10)
    except KeyboardInterrupt:
        pass
    finally:
        renderer.shutdown()
    
    return True

if __name__ == "__main__":
    success = test_basic_renderer()
    print(f"Test {'PASSED' if success else 'FAILED'}")