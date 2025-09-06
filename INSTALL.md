# Installation Guide - WNBA LED Scoreboard

This guide covers installation on both Raspberry Pi (for actual LED matrix) and development systems (with emulator).

## Raspberry Pi Installation

### Prerequisites

1. **Update your system:**
```bash
sudo apt update && sudo apt upgrade -y
```

2. **Install build dependencies:**
```bash
sudo apt install -y build-essential python3-dev python3-pip python3-venv git
```

3. **Install additional libraries for the LED matrix:**
```bash
sudo apt install -y libgraphicsmagick++-dev libwebp-dev
```

### Step 1: Clone the Repository

```bash
cd ~
git clone https://github.com/stevebargelt/wnba-led-scoreboard-claude.git
cd wnba-led-scoreboard-claude
```

### Step 2: Install rpi-rgb-led-matrix

The LED matrix library must be compiled from source:

```bash
# Clone and build the matrix library
cd ~
git clone https://github.com/hzeller/rpi-rgb-led-matrix.git
cd rpi-rgb-led-matrix

# Build the library
make build-python PYTHON=$(which python3)
sudo make install-python PYTHON=$(which python3)
```

### Step 3: Set up Python Environment

```bash
cd ~/wnba-led-scoreboard-claude

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install Python dependencies
pip install --upgrade pip
pip install -r requirements.txt
```

### Step 4: Configure the Scoreboard

1. **Edit your favorite teams:**
```bash
nano config/config.json
```

Update the `favorite_teams` array with your preferred teams:
```json
{
  "favorite_teams": [
    "SEA",  // Your top priority team
    "MIN",  // Second priority  
    "NY"    // Third priority
  ]
}
```

2. **Configure display settings:**
Update the display section for your LED matrix:
```json
{
  "display": {
    "brightness": 75,
    "led_rows": 32,      // Your matrix height
    "led_cols": 64,      // Your matrix width
    "emulator": false    // Set to false for real hardware
  }
}
```

### Step 5: Test the Installation

```bash
source venv/bin/activate
python src/main.py
```

### Step 6: Run as Service (Optional)

Create a systemd service to run the scoreboard automatically:

```bash
sudo nano /etc/systemd/system/wnba-scoreboard.service
```

Add this content (adjust paths as needed):
```ini
[Unit]
Description=WNBA LED Scoreboard
After=network.target

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/wnba-led-scoreboard-claude
ExecStart=/home/pi/wnba-led-scoreboard-claude/venv/bin/python /home/pi/wnba-led-scoreboard-claude/src/main.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start the service:
```bash
sudo systemctl enable wnba-scoreboard.service
sudo systemctl start wnba-scoreboard.service
sudo systemctl status wnba-scoreboard.service
```

## Development Installation (Non-Pi Systems)

For development and testing with the emulator:

### Prerequisites

- Python 3.11+
- Git

### Installation

```bash
# Clone the repository
git clone https://github.com/stevebargelt/wnba-led-scoreboard-claude.git
cd wnba-led-scoreboard-claude

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install development dependencies (includes emulator)
pip install --upgrade pip
pip install -r requirements-dev.txt
```

### Running with Emulator

```bash
source venv/bin/activate
python src/main.py
```

The emulator will open a browser window showing your LED matrix at `http://localhost:8888/`

## Troubleshooting

### Common Issues on Raspberry Pi

1. **Permission denied accessing GPIO:**
   - Run with sudo: `sudo python src/main.py`
   - Or add your user to gpio group: `sudo usermod -a -G gpio $USER`

2. **Matrix not displaying:**
   - Check hardware connections
   - Verify `emulator: false` in config.json
   - Try running with sudo

3. **Import errors:**
   - Ensure rpi-rgb-led-matrix was compiled and installed correctly
   - Check that you're using the virtual environment

### API Issues

1. **No games showing:**
   - Check internet connection
   - Verify ESPN API is accessible
   - Check logs for API errors

2. **Wrong teams showing:**
   - Update `favorite_teams` in config/config.json
   - Ensure team abbreviations are correct (see teams.json for valid codes)

## Hardware Setup

### Recommended Hardware
- Raspberry Pi 3B+ or newer
- 32x32 or 64x32 RGB LED Matrix
- Adafruit RGB Matrix HAT or Bonnet
- 5V power supply (4A+ recommended for larger matrices)

### Wiring
Follow the standard wiring for your Adafruit HAT/Bonnet. The software uses the `adafruit-hat` hardware mapping by default.

## Team Abbreviations

Valid WNBA team abbreviations for `favorite_teams`:
- `ATL` - Atlanta Dream
- `CHI` - Chicago Sky  
- `CONN` - Connecticut Sun
- `DAL` - Dallas Wings
- `IND` - Indiana Fever
- `LAS` - Las Vegas Aces
- `MIN` - Minnesota Lynx
- `NY` - New York Liberty
- `PHX` - Phoenix Mercury
- `SEA` - Seattle Storm
- `WAS` - Washington Mystics