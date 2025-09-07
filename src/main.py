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
from display.graphics import get_logo_manager
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
        
        # Preload logos for favorite teams (20x20 for scoreboard)
        logo_manager = get_logo_manager()
        logger.info("Preloading 20x20 logos for favorite teams...")
        logo_manager.preload_favorite_logos(config.favorite_teams, width=20, height=20)
        
        logger.info("All components initialized successfully")
        
        frame_count = 0
        last_status_log = datetime.now()
        last_content_hash = None
        needs_redraw = True
        
        # Main display loop
        while running:
            try:
                # Only get new data when refresh is needed
                if state_manager.should_refresh():
                    logger.debug("Refreshing game data...")
                    context = state_manager.get_current_display_context()
                    state_manager.schedule_next_refresh(context)
                    needs_redraw = True
                else:
                    # Use cached context if no refresh needed
                    context = getattr(state_manager, '_last_context', None)
                    if context is None:
                        context = state_manager.get_current_display_context()
                        state_manager.schedule_next_refresh(context)
                        needs_redraw = True
                
                # Cache the context
                state_manager._last_context = context
                
                # Check if content has changed
                if context.state == DisplayState.IDLE:
                    # For idle state, only redraw if content actually changes
                    content_hash = hash((
                        context.state,
                        str(context.idle) if context.idle else ""
                    ))
                else:
                    # For other states, include animation frame for smooth updates
                    content_hash = hash((
                        context.state,
                        str(context.scoreboard) if context.scoreboard else "",
                        str(context.countdown) if context.countdown else "", 
                        frame_count // 30  # Animation updates every second
                    ))
                
                if content_hash != last_content_hash:
                    needs_redraw = True
                    last_content_hash = content_hash
                
                # Debug: Log state changes
                if not hasattr(state_manager, '_last_logged_state') or state_manager._last_logged_state != context.state:
                    if context.state == DisplayState.LIVE:
                        logger.info(f"Displaying LIVE: {context.scoreboard.away_team} vs {context.scoreboard.home_team}")
                    elif context.state == DisplayState.PREGAME:
                        logger.info(f"Displaying PREGAME: {context.countdown.away_team} @ {context.countdown.home_team} in {context.countdown.countdown_text}")
                    elif context.state == DisplayState.IDLE:
                        logger.info(f"Displaying IDLE: {context.idle.message}")
                    elif context.state == DisplayState.ERROR:
                        logger.info(f"Displaying ERROR: {context.error.error_message}")
                    state_manager._last_logged_state = context.state
                
                # Only render if something changed
                if needs_redraw:
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
                    
                    needs_redraw = False
                
                # Log status periodically
                now = datetime.now()
                if (now - last_status_log).total_seconds() > 300:  # Every 5 minutes
                    status = state_manager.get_status_summary()
                    logger.info(f"Status: {status}")
                    last_status_log = now
                
                frame_count += 1
                time.sleep(1/10)  # Reduced to 10 FPS to reduce load
                
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