#!/usr/bin/env python3

import sys
import logging
from typing import Optional, Tuple

try:
    from rgbmatrix import RGBMatrix, RGBMatrixOptions, graphics
    HARDWARE_AVAILABLE = True
except ImportError:
    try:
        from RGBMatrixEmulator import RGBMatrix, RGBMatrixOptions, graphics
        HARDWARE_AVAILABLE = False
    except ImportError:
        raise ImportError("Neither rgbmatrix nor RGBMatrixEmulator is available")

logger = logging.getLogger(__name__)


class MatrixRenderer:
    """Hardware abstraction layer for RGB LED Matrix display."""
    
    def __init__(self, rows: int = 32, cols: int = 64, brightness: int = 75, use_emulator: bool = False):
        """
        Initialize the matrix renderer.
        
        Args:
            rows: Number of LED matrix rows
            cols: Number of LED matrix columns  
            brightness: Display brightness (0-100)
            use_emulator: Force use of emulator even if hardware available
        """
        self.rows = rows
        self.cols = cols
        self.brightness = brightness
        self.use_emulator = use_emulator or not HARDWARE_AVAILABLE
        
        self.matrix: Optional[RGBMatrix] = None
        self.canvas = None
        self.font = None
        
        logger.info(f"Initializing MatrixRenderer: {rows}x{cols}, brightness={brightness}, emulator={self.use_emulator}")
        
    def initialize(self) -> bool:
        """Initialize the matrix display."""
        try:
            options = RGBMatrixOptions()
            options.rows = self.rows
            options.cols = self.cols
            options.brightness = self.brightness
            
            if not self.use_emulator and HARDWARE_AVAILABLE:
                options.hardware_mapping = 'adafruit-hat'
                options.gpio_slowdown = 4
                options.disable_hardware_pulsing = True
            
            self.matrix = RGBMatrix(options=options)
            self.canvas = self.matrix.CreateFrameCanvas()
            
            # Load default font with fallbacks - Pi specific paths first
            self.font = graphics.Font()
            font_paths = [
                "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",        # Pi common
                "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",   # Pi bold
                "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf", # Pi alternative
                "/usr/share/fonts/TTF/DejaVuSans.ttf",                    # Some Pi installs
                "/System/Library/Fonts/Arial.ttf",                       # macOS
                "/Windows/Fonts/arial.ttf",                              # Windows
            ]
            
            font_loaded = False
            for font_path in font_paths:
                try:
                    self.font.LoadFont(font_path)
                    font_loaded = True
                    logger.info(f"Loaded font: {font_path}")
                    break
                except Exception as e:
                    logger.debug(f"Could not load font {font_path}: {e}")
            
            if not font_loaded:
                logger.warning("No font could be loaded - using pixel fallback font")
                self.font = None  # Will trigger fallback pixel font
            
            logger.info("Matrix initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize matrix: {e}")
            return False
    
    def clear(self):
        """Clear the display."""
        if self.canvas:
            self.canvas.Clear()
    
    def set_pixel(self, x: int, y: int, red: int, green: int, blue: int):
        """Set a single pixel color."""
        if self.canvas:
            self.canvas.SetPixel(x, y, red, green, blue)
    
    def draw_text(self, x: int, y: int, text: str, red: int = 255, green: int = 255, blue: int = 255):
        """Draw text on the display."""
        if self.canvas:
            # Debug: log the actual color values being used
            logger.debug(f"Rendering '{text}' at ({x},{y}) with RGB({red},{green},{blue})")
            
            color = graphics.Color(red, green, blue)
            try:
                if self.font and hasattr(self.font, 'default_character'):
                    graphics.DrawText(self.canvas, self.font, x, y, color, text)
                else:
                    # If no font loaded or font is incomplete, draw simple pixel text as fallback
                    logger.debug(f"Using pixel fallback for '{text}'")
                    self._draw_simple_text(x, y, text, red, green, blue)
            except (AttributeError, Exception) as e:
                logger.debug(f"Font rendering failed, using fallback: {e}")
                self._draw_simple_text(x, y, text, red, green, blue)
    
    def draw_line(self, x1: int, y1: int, x2: int, y2: int, red: int, green: int, blue: int):
        """Draw a line on the display."""
        if self.canvas:
            color = graphics.Color(red, green, blue)
            graphics.DrawLine(self.canvas, x1, y1, x2, y2, color)
    
    def draw_circle(self, x: int, y: int, radius: int, red: int, green: int, blue: int, fill: bool = False):
        """Draw a circle on the display."""
        if self.canvas:
            color = graphics.Color(red, green, blue)
            if fill:
                graphics.DrawCircle(self.canvas, x, y, radius, color)
            else:
                # For outline, we'd need to implement manually or use a different method
                graphics.DrawCircle(self.canvas, x, y, radius, color)
    
    def fill_rectangle(self, x: int, y: int, width: int, height: int, red: int, green: int, blue: int):
        """Fill a rectangle with color."""
        if self.canvas:
            for i in range(width):
                for j in range(height):
                    if x + i < self.cols and y + j < self.rows:
                        self.canvas.SetPixel(x + i, y + j, red, green, blue)
    
    def get_text_dimensions(self, text: str) -> Tuple[int, int]:
        """Get the width and height of text when rendered."""
        if self.font:
            # This is an approximation - actual implementation may vary
            return len(text) * 6, 11  # Rough estimate for default font
        return 0, 0
    
    def refresh(self):
        """Update the display with current canvas content."""
        if self.matrix and self.canvas:
            self.canvas = self.matrix.SwapOnVSync(self.canvas)
    
    def _draw_simple_text(self, x: int, y: int, text: str, red: int, green: int, blue: int):
        """Draw simple pixel text as fallback when no font is available."""
        # Comprehensive 3x5 pixel font
        char_patterns = {
            'W': [[1,0,0,0,1], [1,0,0,0,1], [1,0,1,0,1], [1,0,1,0,1], [0,1,0,1,0]],
            'N': [[1,0,0,1], [1,0,0,1], [1,1,0,1], [1,0,1,1], [1,0,0,1]],
            'B': [[1,1,1], [1,0,1], [1,1,1], [1,0,1], [1,1,1]],
            'A': [[0,1,1,0], [1,0,0,1], [1,1,1,1], [1,0,0,1], [1,0,0,1]],
            'T': [[1,1,1,1,1], [0,0,1,0,0], [0,0,1,0,0], [0,0,1,0,0], [0,0,1,0,0]],
            'E': [[1,1,1,1], [1,0,0,0], [1,1,1,0], [1,0,0,0], [1,1,1,1]],
            'S': [[0,1,1,1], [1,0,0,0], [0,1,1,0], [0,0,0,1], [1,1,1,0]],
            'L': [[1,0,0], [1,0,0], [1,0,0], [1,0,0], [1,1,1]],
            'M': [[1,0,0,0,1], [1,1,0,1,1], [1,0,1,0,1], [1,0,0,0,1], [1,0,0,0,1]],
            'I': [[1,1,1], [0,1,0], [0,1,0], [0,1,0], [1,1,1]],
            'Y': [[1,0,0,1], [1,0,0,1], [0,1,1,0], [0,1,0,0], [0,1,0,0]],
            'H': [[1,0,1], [1,0,1], [1,1,1], [1,0,1], [1,0,1]],
            'G': [[0,1,1,1], [1,0,0,0], [1,0,1,1], [1,0,0,1], [0,1,1,1]],
            'O': [[0,1,1,0], [1,0,0,1], [1,0,0,1], [1,0,0,1], [0,1,1,0]],
            'D': [[1,1,1,0], [1,0,0,1], [1,0,0,1], [1,0,0,1], [1,1,1,0]],
            'F': [[1,1,1,1], [1,0,0,0], [1,1,1,0], [1,0,0,0], [1,0,0,0]],
            'R': [[1,1,1,0], [1,0,0,1], [1,1,1,0], [1,0,1,0], [1,0,0,1]],
            'C': [[0,1,1,1], [1,0,0,0], [1,0,0,0], [1,0,0,0], [0,1,1,1]],
            'P': [[1,1,1,0], [1,0,0,1], [1,1,1,0], [1,0,0,0], [1,0,0,0]],
            'V': [[1,0,0,0,1], [1,0,0,0,1], [1,0,0,0,1], [0,1,0,1,0], [0,0,1,0,0]],
            'X': [[1,0,0,1], [1,0,0,1], [0,1,1,0], [1,0,0,1], [1,0,0,1]],
            'Q': [[0,1,1,0], [1,0,0,1], [1,0,0,1], [1,0,1,1], [0,1,1,1]],
            ' ': [[0,0,0], [0,0,0], [0,0,0], [0,0,0], [0,0,0]],
            '0': [[1,1,1], [1,0,1], [1,0,1], [1,0,1], [1,1,1]],
            '1': [[0,1,0], [1,1,0], [0,1,0], [0,1,0], [1,1,1]],
            '2': [[1,1,1], [0,0,1], [1,1,1], [1,0,0], [1,1,1]],
            '3': [[1,1,1], [0,0,1], [1,1,1], [0,0,1], [1,1,1]],
            '4': [[1,0,1], [1,0,1], [1,1,1], [0,0,1], [0,0,1]],
            '5': [[1,1,1], [1,0,0], [1,1,1], [0,0,1], [1,1,1]],
            '6': [[1,1,1], [1,0,0], [1,1,1], [1,0,1], [1,1,1]],
            '7': [[1,1,1], [0,0,1], [0,0,1], [0,0,1], [0,0,1]],
            '8': [[1,1,1], [1,0,1], [1,1,1], [1,0,1], [1,1,1]],
            '9': [[1,1,1], [1,0,1], [1,1,1], [0,0,1], [1,1,1]],
            ':': [[0], [1], [0], [1], [0]],
            '-': [[0,0,0], [0,0,0], [1,1,1], [0,0,0], [0,0,0]],
            '@': [[0,1,1,0], [1,0,1,1], [1,1,1,1], [1,0,0,0], [0,1,1,1]],
            '!': [[1], [1], [1], [0], [1]],
            '?': [[1,1,1], [0,0,1], [0,1,1], [0,0,0], [0,1,0]]
        }
        
        current_x = x
        for char in text.upper():
            if char in char_patterns:
                pattern = char_patterns[char]
                for row_idx, row in enumerate(pattern):
                    for col_idx, pixel in enumerate(row):
                        if pixel and current_x + col_idx < self.cols and y + row_idx < self.rows:
                            self.canvas.SetPixel(current_x + col_idx, y + row_idx, red, green, blue)
                current_x += len(pattern[0]) + 1  # character width + spacing
            else:
                current_x += 4  # space for unknown characters

    def shutdown(self):
        """Clean up resources."""
        if self.matrix:
            self.matrix.Clear()
            logger.info("Matrix display shutdown")


class Color:
    """Predefined colors for convenience."""
    RED = (255, 0, 0)
    GREEN = (0, 255, 0)
    BLUE = (0, 0, 255)
    WHITE = (255, 255, 255)
    BLACK = (0, 0, 0)
    YELLOW = (255, 255, 0)
    CYAN = (0, 255, 255)
    MAGENTA = (255, 0, 255)
    ORANGE = (255, 165, 0)
    
    @staticmethod
    def from_hex(hex_color: str) -> Tuple[int, int, int]:
        """Convert hex color string to RGB tuple."""
        hex_color = hex_color.lstrip('#')
        return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))