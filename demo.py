#!/usr/bin/env python3

import sys
import shutil
from pathlib import Path

def show_usage():
    """Show usage instructions."""
    print("WNBA Scoreboard Demo Mode")
    print("Usage:")
    print("  python demo.py live     - Show simulated live game")
    print("  python demo.py pregame  - Show simulated pregame countdown") 
    print("  python demo.py normal   - Return to normal mode (real data)")
    print("  python demo.py status   - Show current mode")

def main():
    if len(sys.argv) != 2:
        show_usage()
        sys.exit(1)
    
    mode = sys.argv[1].lower()
    config_dir = Path("config")
    main_config = config_dir / "config.json"
    
    if mode == "live":
        # Copy test-live config
        test_config = config_dir / "test-live.json"
        if test_config.exists():
            shutil.copy(test_config, main_config)
            print("✅ Enabled LIVE GAME demo mode")
            print("Run: sudo /path/to/venv/bin/python src/main.py")
            print("You should see: SEA vs MIN with live scores!")
        else:
            print("❌ test-live.json not found")
    
    elif mode == "pregame":
        # Copy test-pregame config  
        test_config = config_dir / "test-pregame.json"
        if test_config.exists():
            shutil.copy(test_config, main_config)
            print("✅ Enabled PREGAME COUNTDOWN demo mode")
            print("Run: sudo /path/to/venv/bin/python src/main.py")
            print("You should see: NY @ LAS countdown timer!")
        else:
            print("❌ test-pregame.json not found")
    
    elif mode == "normal":
        # Disable test mode
        import json
        if main_config.exists():
            with open(main_config, 'r') as f:
                config = json.load(f)
            
            config['test_mode'] = {
                "enabled": False,
                "simulate_live_game": False, 
                "simulate_pregame": False
            }
            
            with open(main_config, 'w') as f:
                json.dump(config, f, indent=2)
            
            print("✅ Returned to NORMAL mode (real WNBA data)")
            print("Run: sudo /path/to/venv/bin/python src/main.py")
        else:
            print("❌ config.json not found")
    
    elif mode == "status":
        # Show current mode
        import json
        if main_config.exists():
            with open(main_config, 'r') as f:
                config = json.load(f)
            
            test_mode = config.get('test_mode', {})
            if test_mode.get('enabled', False):
                if test_mode.get('simulate_live_game', False):
                    print("📺 Current mode: LIVE GAME DEMO")
                elif test_mode.get('simulate_pregame', False):
                    print("⏰ Current mode: PREGAME COUNTDOWN DEMO")
                else:
                    print("🧪 Current mode: TEST (no simulation)")
            else:
                print("🏀 Current mode: NORMAL (real WNBA data)")
        else:
            print("❌ config.json not found")
    
    else:
        show_usage()
        sys.exit(1)

if __name__ == "__main__":
    main()