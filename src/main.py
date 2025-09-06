#!/usr/bin/env python3

import sys
import time
import signal
import logging
from datetime import datetime
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from core.config import get_config
from core.state_manager import WNBAStateManager
from display.renderer import MatrixRenderer
from display.layouts.pregame import PregameLayout
from display.layouts.scoreboard import ScoreboardLayout
from display.layouts.idle import IdleLayout
from api.data_models import DisplayState

# Global flag for graceful shutdown
running = True

def signal_handler(signum, frame):
    """Handle shutdown signals gracefully."""
    global running
    print(f"\nReceived signal {signum}. Shutting down gracefully...")
    running = False

def setup_logging():
    """Configure logging based on config settings."""
    config = get_config()
    
    log_level = getattr(logging, config.logging.level.upper(), logging.INFO)
    log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    
    logging.basicConfig(
        level=log_level,
        format=log_format,
        handlers=[
            logging.FileHandler(config.logging.file),
            logging.StreamHandler(sys.stdout)
        ]
    )

def main():
    """Main application loop."""
    global running
    
    # Set up signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Setup logging
    setup_logging()
    logger = logging.getLogger(__name__)
    
    logger.info("Starting WNBA LED Scoreboard...")
    
    try:
        # Load configuration
        config = get_config()
        logger.info(f"Loaded config with {len(config.favorite_teams)} favorite teams: {config.favorite_teams}")
        
        # Initialize renderer
        renderer = MatrixRenderer(
            rows=config.display.led_rows,
            cols=config.display.led_cols,
            brightness=config.display.brightness,
            use_emulator=config.display.emulator
        )
        
        if not renderer.initialize():
            logger.error("Failed to initialize display renderer")
            return 1
        
        logger.info(f"Display initialized: {config.display.led_rows}x{config.display.led_cols}, emulator={config.display.emulator}")
        
        # Initialize layouts
        pregame_layout = PregameLayout(renderer)
        scoreboard_layout = ScoreboardLayout(renderer)
        idle_layout = IdleLayout(renderer)
        
        # Initialize state manager
        state_manager = WNBAStateManager()
        
        logger.info("All components initialized successfully")
        
        frame_count = 0
        last_status_log = datetime.now()
        
        # Main display loop
        while running:
            try:
                # Check if we need to refresh data
                if state_manager.should_refresh():
                    logger.debug("Refreshing game data...")
                    
                # Get current display context
                context = state_manager.get_current_display_context()
                
                # Schedule next refresh
                state_manager.schedule_next_refresh(context)
                
                # Render based on current state
                if context.state == DisplayState.LIVE:
                    scoreboard_layout.render(context.scoreboard, frame_count)
                    
                elif context.state == DisplayState.PREGAME:
                    pregame_layout.render(context.countdown, frame_count)
                    
                elif context.state == DisplayState.FINAL:
                    # Show final score (use scoreboard layout)
                    scoreboard_layout.render(context.scoreboard, frame_count)
                    
                elif context.state == DisplayState.IDLE:
                    idle_layout.render(context.idle, frame_count)
                    
                elif context.state == DisplayState.ERROR:
                    # Simple error display
                    renderer.clear()
                    renderer.draw_text(2, 10, "API ERROR", 255, 0, 0)
                    renderer.draw_text(2, 20, f"RETRY {context.error.retry_in}S", 255, 165, 0)
                    renderer.refresh()
                
                # Log status periodically
                now = datetime.now()
                if (now - last_status_log).total_seconds() > 300:  # Every 5 minutes
                    status = state_manager.get_status_summary()
                    logger.info(f"Status: {status}")
                    last_status_log = now
                
                frame_count += 1
                time.sleep(1/30)  # ~30 FPS
                
            except KeyboardInterrupt:
                break
            except Exception as e:
                logger.error(f"Error in main loop: {e}", exc_info=True)
                time.sleep(5)  # Wait before retrying
        
        logger.info("Shutting down WNBA LED Scoreboard...")
        
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        return 1
        
    finally:
        # Clean up resources
        if 'renderer' in locals():
            renderer.shutdown()
        logger.info("Shutdown complete")
    
    return 0

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)