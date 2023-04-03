# turing-smart-screen-python - a Python system monitor and library for 3.5" USB-C displays like Turing Smart Screen or XuanFang
# https://github.com/mathoudebine/turing-smart-screen-python/

# Copyright (C) 2021-2023  Matthieu Houdebine (mathoudebine)
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

from library import config
from library.lcd.lcd_comm import Orientation
from library.lcd.lcd_comm_rev_a import LcdCommRevA
from library.lcd.lcd_comm_rev_b import LcdCommRevB
from library.lcd.lcd_simulated import LcdSimulated
from library.log import logger


def _get_full_path(path, name):
    if name:
        return path + name
    else:
        return None


def _get_theme_orientation() -> Orientation:
    if config.THEME_DATA["display"]["DISPLAY_ORIENTATION"] == 'portrait':
        if config.CONFIG_DATA["display"].get("DISPLAY_REVERSE", False):
            return Orientation.REVERSE_PORTRAIT
        else:
            return Orientation.PORTRAIT
    elif config.THEME_DATA["display"]["DISPLAY_ORIENTATION"] == 'landscape':
        if config.CONFIG_DATA["display"].get("DISPLAY_REVERSE", False):
            return Orientation.REVERSE_LANDSCAPE
        else:
            return Orientation.LANDSCAPE
    elif config.THEME_DATA["display"]["DISPLAY_ORIENTATION"] == 'reverse_portrait':
        logger.warn("'reverse_portrait' is deprecated as DISPLAY_ORIENTATION value in the theme."
                    "Use 'portrait' instead, and use DISPLAY_REVERSE in config.yaml to reverse orientation.")
        return Orientation.REVERSE_PORTRAIT
    elif config.THEME_DATA["display"]["DISPLAY_ORIENTATION"] == 'reverse_landscape':
        logger.warn("'reverse_landscape' is deprecated as DISPLAY_ORIENTATION value in the theme."
                    "Use 'landscape' instead, and use DISPLAY_REVERSE in config.yaml to reverse orientation.")
        return Orientation.REVERSE_LANDSCAPE
    else:
        logger.warning("Orientation '", config.THEME_DATA["display"]["DISPLAY_ORIENTATION"],
                       "' unknown, using portrait")
        return Orientation.PORTRAIT


class Display:
    def __init__(self):
        self.lcd = None
        if config.CONFIG_DATA["display"]["REVISION"] == "A":
            self.lcd = LcdCommRevA(com_port=config.CONFIG_DATA['config']['COM_PORT'],
                                   display_width=config.CONFIG_DATA["display"]["DISPLAY_WIDTH"],
                                   display_height=config.CONFIG_DATA["display"]["DISPLAY_HEIGHT"],
                                   update_queue=config.update_queue)
        elif config.CONFIG_DATA["display"]["REVISION"] == "B":
            self.lcd = LcdCommRevB(com_port=config.CONFIG_DATA['config']['COM_PORT'],
                                   display_width=config.CONFIG_DATA["display"]["DISPLAY_WIDTH"],
                                   display_height=config.CONFIG_DATA["display"]["DISPLAY_HEIGHT"],
                                   update_queue=config.update_queue)
        elif config.CONFIG_DATA["display"]["REVISION"] == "SIMU":
            self.lcd = LcdSimulated(display_width=config.CONFIG_DATA["display"]["DISPLAY_WIDTH"],
                                    display_height=config.CONFIG_DATA["display"]["DISPLAY_HEIGHT"])
        else:
            logger.error("Unknown display revision '", config.CONFIG_DATA["display"]["REVISION"], "'")

    def initialize_display(self):
        # Reset screen in case it was in an unstable state (screen is also cleared)
        self.lcd.Reset()

        # Send initialization commands
        self.lcd.InitializeComm()

        # Turn on display, set brightness and LEDs for supported HW
        self.turn_on()

        # Set orientation
        self.lcd.SetOrientation(_get_theme_orientation())

    def turn_on(self):
        # Turn screen on in case it was turned off previously
        self.lcd.ScreenOn()

        # Set brightness
        self.lcd.SetBrightness(config.CONFIG_DATA["display"]["BRIGHTNESS"])

        # Set backplate RGB LED color (for supported HW only)
        self.lcd.SetBackplateLedColor(config.THEME_DATA['display'].get("DISPLAY_RGB_LED", (255, 255, 255)))

    def turn_off(self):
        # Turn screen off
        self.lcd.ScreenOff()

        # Turn off backplate RGB LED
        self.lcd.SetBackplateLedColor(led_color=(0, 0, 0))

    def display_static_images(self):
        if config.THEME_DATA.get('static_images', False):
            for image in config.THEME_DATA['static_images']:
                logger.debug(f"Drawing Image: {image}")
                self.lcd.DisplayBitmap(
                    bitmap_path=config.THEME_DATA['PATH'] + config.THEME_DATA['static_images'][image].get("PATH"),
                    x=config.THEME_DATA['static_images'][image].get("X", 0),
                    y=config.THEME_DATA['static_images'][image].get("Y", 0),
                    width=config.THEME_DATA['static_images'][image].get("WIDTH", 0),
                    height=config.THEME_DATA['static_images'][image].get("HEIGHT", 0)
                )

    def display_static_text(self):
        if config.THEME_DATA.get('static_text', False):
            for text in config.THEME_DATA['static_text']:
                logger.debug(f"Drawing Text: {text}")
                self.lcd.DisplayText(
                    text=config.THEME_DATA['static_text'][text].get("TEXT"),
                    x=config.THEME_DATA['static_text'][text].get("X", 0),
                    y=config.THEME_DATA['static_text'][text].get("Y", 0),
                    font=config.THEME_DATA['static_text'][text].get("FONT", config.THEME_DEFAULTS['FONT']),
                    font_size=config.THEME_DATA['static_text'][text].get("FONT_SIZE", config.THEME_DEFAULTS['FONT_SIZE']),
                    font_color=config.THEME_DATA['static_text'][text].get("FONT_COLOR", config.THEME_DEFAULTS['FONT_COLOR']),
                    background_color=config.THEME_DATA['static_text'][text].get("BACKGROUND_COLOR", config.THEME_DEFAULTS['TEXT_BACKGROUND_COLOR']),
                    background_image=_get_full_path(config.THEME_DATA['PATH'], config.THEME_DATA['static_text'][text].get("BACKGROUND_IMAGE", config.THEME_DEFAULTS['TEXT_BACKGROUND_IMAGE']))
                )


display = Display()
