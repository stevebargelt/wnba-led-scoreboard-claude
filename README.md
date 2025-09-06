# WNBA LED Scoreboard

A real-time WNBA scoreboard for Raspberry Pi LED matrices, displaying live game scores, countdown timers, and team information for your favorite WNBA teams.

## Features

- **Favorite Team Prioritization**: Configure your favorite teams in priority order
- **Real-time Updates**: Live scores and game status from ESPN API
- **Smart Display Logic**: Shows countdown timers for upcoming games, live scores during games
- **Multi-game Support**: Automatically prioritizes and switches between games
- **Team Graphics**: Team colors and logos on LED display
- **Emulator Support**: Test without hardware using RGBMatrixEmulator

## Hardware Requirements

- Raspberry Pi (3B+ or newer recommended)
- RGB LED Matrix (32x32, 64x32, or 64x64 pixels)
- Adafruit RGB Matrix HAT or Bonnet

## Installation

1. Clone this repository:
```bash
git clone https://github.com/yourusername/wnba-led-scoreboard.git
cd wnba-led-scoreboard
```

2. Create a virtual environment:
```bash
python3 -m venv venv
source venv/bin/activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

## Configuration

Edit `config/config.json` to set your favorite teams and display preferences:

```json
{
  "favorite_teams": [
    "LAS",  // Las Vegas Aces (highest priority)
    "SEA",  // Seattle Storm
    "NY"    // New York Liberty
  ],
  "display": {
    "brightness": 75,
    "led_rows": 32,
    "led_cols": 64
  }
}
```

## Usage

Run the scoreboard:
```bash
python src/main.py
```

For emulator mode (testing without hardware):
```bash
python src/main.py --emulator
```

## Team Abbreviations

- ATL - Atlanta Dream
- CHI - Chicago Sky  
- CONN - Connecticut Sun
- DAL - Dallas Wings
- IND - Indiana Fever
- LAS - Las Vegas Aces
- MIN - Minnesota Lynx
- NY - New York Liberty
- PHX - Phoenix Mercury
- SEA - Seattle Storm
- WAS - Washington Mystics

## Development

This project uses the RGBMatrixEmulator for cross-platform development. You can develop and test on any system before deploying to the Raspberry Pi.

## License

MIT License - see LICENSE file for details.

## Acknowledgments

Inspired by:
- [NHL LED Scoreboard](https://github.com/falkyre/nhl-led-scoreboard)
- [MLB LED Scoreboard](https://github.com/MLB-LED-Scoreboard/mlb-led-scoreboard)
- [Basketball Scoreboard](https://github.com/basketballrelativity/scoreboard)