# turing-smart-screen-python - a Python system monitor and library for 3.5" USB-C displays like Turing Smart Screen or XuanFang
# https://github.com/mathoudebine/turing-smart-screen-python/

# Copyright (C) 2021-2023  Matthieu Houdebine (mathoudebine)
# Copyright (C) 2022-2023  Rollbacke
# Copyright (C) 2022-2023  Ebag333
# Copyright (C) 2022-2023  w1ld3r
# Copyright (C) 2022-2023  Charles Ferguson (gerph)
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

import datetime
import locale
import math
import os
import platform
import sys

import babel.dates
#from psutil._common import bytes2human

import library.config as config
from library.display import display
from library.log import logger

ETH_CARD = config.CONFIG_DATA["config"]["ETH"]
WLO_CARD = config.CONFIG_DATA["config"]["WLO"]
HW_SENSORS = config.CONFIG_DATA["config"]["HW_SENSORS"]

if HW_SENSORS == "PYTHON":
    import library.sensors.sensors_python as sensors
elif HW_SENSORS == "LHM":
    if platform.system() == 'Windows':
        import library.sensors.sensors_librehardwaremonitor as sensors
    else:
        logger.error("LibreHardwareMonitor integration is only available on Windows")
        try:
            sys.exit(0)
        except:
            os._exit(0)
elif HW_SENSORS == "STUB":
    logger.warning("Stub sensors, not real HW sensors")
    import library.sensors.sensors_stub_random as sensors
elif HW_SENSORS == "STATIC":
    logger.warning("Stub sensors, not real HW sensors")
    import library.sensors.sensors_stub_static as sensors
elif HW_SENSORS == "AUTO":
    if platform.system() == 'Windows':
        import library.sensors.sensors_librehardwaremonitor as sensors
    else:
        import library.sensors.sensors_python as sensors
else:
    logger.error("Unsupported SENSORS value in config.yaml")
    try:
        sys.exit(0)
    except:
        os._exit(0)


def get_full_path(path, name):
    if name:
        return path + name
    else:
        return None

def format_number(num, sectionConfig, unit, bytes = False) -> str:

    decimals      = sectionConfig.get("DECIMALS", 0)
    align         = sectionConfig.get("ALIGN", "LEFT")
    length        = sectionConfig.get("TEXT_LENGTH", 3)
    unit_space    = sectionConfig.get("UNIT_SPACE", True)
    show_unit     = sectionConfig.get("SHOW_UNIT", False)
    unit_override = sectionConfig.get("UNIT", False)
    symbol        = ""


    if bytes:
        symbols = ('B', 'K', 'M', 'G', 'T', 'P', 'E', 'Z', 'Y')
        prefix = {}
        for i, s in enumerate(symbols[1:]):
            prefix[s] = 1 << (i + 1) * 10
        if bytes and unit_override:
            num = num / prefix[unit_override]
            symbol = unit_override
        else:
            for symbol in reversed(symbols[1:]):
                if num >= prefix[symbol]:
                    num = num / prefix[symbol]
                    break
            
    if isinstance(decimals, str) and decimals.upper() == "AUTO":   # 0.12, 9.87, 12.3, 100
        if num == 0:
            string = "0"
        else:
            digits = len(str(int(num)))
            precision = length - 1 - digits
            if precision < 0:
                precision = 0
            string = f"{num:.{precision}f}"
    else:
        string = f"{num:.{decimals}f}"

    if show_unit:
        string += (" " if unit_space else "") + symbol + unit

    if show_unit and bytes:
        unit_len = len(str(symbol)) + len(str(unit))
    elif show_unit:
        unit_len = len(str(unit))
    else:
        unit_len = 0
    if show_unit and unit_space:
        unit_len += 1
        
    if align.upper() == "CENTER":
        string = string.center(length + unit_len)
    elif align.upper() == "LEFT":
        string = string.rjust(length + unit_len)
    else:
        string = string.rjust(length)
    
    return string
    
def text_factory(text, value, sectionConfig):
    
    tempConfig = sectionConfig.copy()
    
    if tempConfig.get("TRESHOLD", False):
        if value >= tempConfig['TRESHOLD'].get("VALUE", 0):
            for key in tempConfig['TRESHOLD']:
                if key == 'VALUE':
                    continue
                tempConfig[key] = tempConfig['TRESHOLD'][key]
    
    display.lcd.DisplayText(
        text=text,
        x=tempConfig.get("X", 0),
        y=tempConfig.get("Y", 0),
        font=tempConfig.get("FONT", config.THEME_DEFAULTS['FONT']),
        font_size=tempConfig.get("FONT_SIZE", config.THEME_DEFAULTS['FONT_SIZE']),
        font_color=tempConfig.get("FONT_COLOR", config.THEME_DEFAULTS['FONT_COLOR']),
        background_color=tempConfig.get("BACKGROUND_COLOR", config.THEME_DEFAULTS['TEXT_BACKGROUND_COLOR']),
        background_image=get_full_path(config.THEME_DATA['PATH'], tempConfig.get("BACKGROUND_IMAGE", config.THEME_DEFAULTS['TEXT_BACKGROUND_IMAGE']))
    )
    
    del tempConfig

def bar_factory(value, sectionConfig):
    
    tempConfig = sectionConfig.copy()
    
    if tempConfig.get("TRESHOLD", False):
        if value >= tempConfig['TRESHOLD'].get("VALUE", 0):
            for key in tempConfig['TRESHOLD']:
                if key == 'VALUE':
                    continue
                tempConfig[key] = tempConfig['TRESHOLD'][key]
    
    display.lcd.DisplayProgressBar(
        x=tempConfig.get("X", 0),
        y=tempConfig.get("Y", 0),
        width=tempConfig.get("WIDTH", 0),
        height=tempConfig.get("HEIGHT", 0),
        value=int(value),
        min_value=tempConfig.get("MIN_VALUE", 0),
        max_value=tempConfig.get("MAX_VALUE", 100),
        bar_color=tempConfig.get("BAR_COLOR", config.THEME_DEFAULTS['BAR_COLOR']),
        bar_outline=tempConfig.get("BAR_OUTLINE", config.THEME_DEFAULTS['BAR_OUTLINE']),
        background_color=tempConfig.get("BACKGROUND_COLOR", config.THEME_DEFAULTS['BAR_BACKGROUND_COLOR']),
        background_image=get_full_path(config.THEME_DATA['PATH'], tempConfig.get("BACKGROUND_IMAGE", config.THEME_DEFAULTS['BAR_BACKGROUND_IMAGE']))
    )
    
    del tempConfig


class CPU:
    @staticmethod
    def percentage():
        cpu_percentage = sensors.Cpu.percentage(
            interval=config.THEME_DATA['STATS']['CPU']['PERCENTAGE'].get("INTERVAL", None))
        # logger.debug(f"CPU Percentage: {cpu_percentage}")

        if config.THEME_DATA['STATS']['CPU']['PERCENTAGE']['TEXT'].get("SHOW", False):
            sectionConfig = config.THEME_DATA['STATS']['CPU']['PERCENTAGE']['TEXT'];
            cpu_percentage_text = format_number(cpu_percentage, sectionConfig, "%")
            text_factory(cpu_percentage_text, cpu_percentage, sectionConfig)

        if config.THEME_DATA['STATS']['CPU']['PERCENTAGE']['GRAPH'].get("SHOW", False):
            sectionConfig = config.THEME_DATA['STATS']['CPU']['PERCENTAGE']['GRAPH'];
            bar_factory(cpu_percentage, sectionConfig)

    @staticmethod
    def frequency():
        if config.THEME_DATA['STATS']['CPU']['FREQUENCY']['TEXT'].get("SHOW", False):
            sectionConfig = config.THEME_DATA['STATS']['CPU']['FREQUENCY']['TEXT'];
            cpu_freq = format_number(sensors.Cpu.frequency() / 1000, sectionConfig, "GHz")
            text_factory(cpu_freq, sensors.Cpu.frequency(), sectionConfig)

    @staticmethod
    def load():
        cpu_load = sensors.Cpu.load()
        # logger.debug(f"CPU Load: ({cpu_load[0]},{cpu_load[1]},{cpu_load[2]})")

        if config.THEME_DATA['STATS']['CPU']['LOAD']['ONE']['TEXT'].get("SHOW", False):
            sectionConfig = config.THEME_DATA['STATS']['CPU']['LOAD']['ONE']['TEXT'];
            cpu_load_one = format_number(cpu_load[0], sectionConfig, "%")
            text_factory(cpu_load_one, cpu_load[0], sectionConfig)

        if config.THEME_DATA['STATS']['CPU']['LOAD']['FIVE']['TEXT'].get("SHOW", False):
            sectionConfig = config.THEME_DATA['STATS']['CPU']['LOAD']['FIVE']['TEXT'];
            cpu_load_five = format_number(cpu_load[1], sectionConfig, "%")
            text_factory(cpu_load_five, cpu_load[1], sectionConfig)

        if config.THEME_DATA['STATS']['CPU']['LOAD']['FIFTEEN']['TEXT'].get("SHOW", False):
            sectionConfig = config.THEME_DATA['STATS']['CPU']['LOAD']['FIFTEEN']['TEXT']
            cpu_load_fifteen = format_number(cpu_load[2], sectionConfig, "%")
            text_factory(cpu_load_fifteen, cpu_load[2], sectionConfig)

    @staticmethod
    def is_temperature_available():
        return sensors.Cpu.is_temperature_available()

    @staticmethod
    def temperature():
        if config.THEME_DATA['STATS']['CPU']['TEMPERATURE']['TEXT'].get("SHOW", False):
            sectionConfig = config.THEME_DATA['STATS']['CPU']['TEMPERATURE']['TEXT'];
            cpu_temp = format_number(sensors.Cpu.temperature(), sectionConfig, "°C")
            text_factory(cpu_temp, sensors.Cpu.temperature(), sectionConfig)

        if config.THEME_DATA['STATS']['CPU']['TEMPERATURE']['GRAPH'].get("SHOW", False):
            sectionConfig = config.THEME_DATA['STATS']['CPU']['TEMPERATURE']['GRAPH']
            bar_factory(sensors.Cpu.temperature(), sectionConfig)

def display_gpu_stats(load, memory_percentage, memory_used_mb, temperature):
    if config.THEME_DATA['STATS']['GPU']['PERCENTAGE']['GRAPH'].get("SHOW", False):
        sectionConfig = config.THEME_DATA['STATS']['GPU']['PERCENTAGE']['GRAPH']
        if math.isnan(load):
            logger.warning("Your GPU load is not supported yet")
            config.THEME_DATA['STATS']['GPU']['PERCENTAGE']['GRAPH']['SHOW'] = False
            config.THEME_DATA['STATS']['GPU']['PERCENTAGE']['TEXT']['SHOW'] = False
        else:
            # logger.debug(f"GPU Load: {load}")
            bar_factory(int(load), sectionConfig)

    if config.THEME_DATA['STATS']['GPU']['PERCENTAGE']['TEXT'].get("SHOW", False):
        sectionConfig = config.THEME_DATA['STATS']['GPU']['PERCENTAGE']['TEXT']
        if math.isnan(load):
            logger.warning("Your GPU load is not supported yet")
            config.THEME_DATA['STATS']['GPU']['PERCENTAGE']['GRAPH']['SHOW'] = False
            config.THEME_DATA['STATS']['GPU']['PERCENTAGE']['TEXT']['SHOW'] = False
        else:
            load_text = format_number(load, sectionConfig, "%")
            text_factory(load_text, load, sectionConfig)

    if config.THEME_DATA['STATS']['GPU']['MEMORY']['GRAPH'].get("SHOW", False):
        sectionConfig = config.THEME_DATA['STATS']['GPU']['MEMORY']['GRAPH'];
        if math.isnan(memory_percentage):
            logger.warning("Your GPU memory relative usage (%) is not supported yet")
            config.THEME_DATA['STATS']['GPU']['MEMORY']['GRAPH']['SHOW'] = False
        else:
            bar_factory(memory_percentage, sectionConfig)

    if config.THEME_DATA['STATS']['GPU']['MEMORY']['TEXT'].get("SHOW", False):
        sectionConfig = config.THEME_DATA['STATS']['GPU']['MEMORY']['TEXT'];
        if math.isnan(memory_used_mb):
            logger.warning("Your GPU memory absolute usage (M) is not supported yet")
            config.THEME_DATA['STATS']['GPU']['MEMORY']['TEXT']['SHOW'] = False
        else:
            mem_used_text = format_number(memory_used_mb * 1000, sectionConfig, "", True)
            text_factory(mem_used_text, memory_used_mb, sectionConfig)

    if config.THEME_DATA['STATS']['GPU']['TEMPERATURE']['TEXT'].get("SHOW", False):
        sectionConfig = config.THEME_DATA['STATS']['GPU']['TEMPERATURE']['TEXT']
        if math.isnan(temperature):
            logger.warning("Your GPU temperature is not supported yet")
            config.THEME_DATA['STATS']['GPU']['TEMPERATURE']['TEXT']['SHOW'] = False
        else:
            temp_text = format_number(temperature, sectionConfig, "°C")
            text_factory(temp_text, temperature, sectionConfig)

            if config.THEME_DATA['STATS']['GPU']['TEMPERATURE'].get("GRAPH", False):
                if config.THEME_DATA['STATS']['GPU']['TEMPERATURE']['GRAPH'].get("SHOW", False):
                    sectionConfig = config.THEME_DATA['STATS']['GPU']['TEMPERATURE']['GRAPH']
                    bar_factory(temperature, sectionConfig)

class Gpu:
    @staticmethod
    def stats():
        load, memory_percentage, memory_used_mb, temperature = sensors.Gpu.stats()
        display_gpu_stats(load, memory_percentage, memory_used_mb, temperature)

    @staticmethod
    def is_available():
        return sensors.Gpu.is_available()


class Memory:
    @staticmethod
    def stats():
        swap_percent = sensors.Memory.swap_percent()

        if config.THEME_DATA['STATS']['MEMORY']['SWAP'].get('PERCENT_TEXT', False) and config.THEME_DATA['STATS']['MEMORY']['SWAP']['PERCENT_TEXT'].get("SHOW", False):
            sectionConfig = config.THEME_DATA['STATS']['MEMORY']['SWAP']['PERCENT_TEXT']
            swap_percent_text = format_number(swap_percent, sectionConfig, "%")
            text_factory(swap_percent_text, swap_percent, sectionConfig)

        if config.THEME_DATA['STATS']['MEMORY']['SWAP']['GRAPH'].get("SHOW", False):
            sectionConfig = config.THEME_DATA['STATS']['MEMORY']['SWAP']['GRAPH']
            bar_factory(swap_percent, sectionConfig)

        virtual_percent = sensors.Memory.virtual_percent()

        if config.THEME_DATA['STATS']['MEMORY']['VIRTUAL']['GRAPH'].get("SHOW", False):
            sectionConfig = config.THEME_DATA['STATS']['MEMORY']['VIRTUAL']['GRAPH']
            bar_factory(virtual_percent, sectionConfig)

        if config.THEME_DATA['STATS']['MEMORY']['VIRTUAL']['PERCENT_TEXT'].get("SHOW", False):
            sectionConfig = config.THEME_DATA['STATS']['MEMORY']['VIRTUAL']['PERCENT_TEXT']
            virtual_percent_text = format_number(virtual_percent, sectionConfig, "%")
            text_factory(virtual_percent_text, virtual_percent, sectionConfig)

        if config.THEME_DATA['STATS']['MEMORY']['VIRTUAL']['USED'].get("SHOW", False):
            virtual_used = sensors.Memory.virtual_used()
            sectionConfig = config.THEME_DATA['STATS']['MEMORY']['VIRTUAL']['USED']
            virtual_used_text = format_number(virtual_used, sectionConfig, "", True)
            text_factory(virtual_used_text, virtual_used, sectionConfig)

        if config.THEME_DATA['STATS']['MEMORY']['VIRTUAL']['FREE'].get("SHOW", False):
            virtual_free = sensors.Memory.virtual_free()
            sectionConfig = config.THEME_DATA['STATS']['MEMORY']['VIRTUAL']['FREE']
            virtual_free_text = format_number(virtual_free, sectionConfig, "", True)
            text_factory(virtual_free_text, virtual_free, sectionConfig)


class Disk:
    @staticmethod
    def stats():
        if config.THEME_DATA['STATS'].get('DISKS', False):
            for partition in config.THEME_DATA['STATS']['DISKS']:
                used = sensors.Disk.disk_used(config.THEME_DATA['STATS']['DISKS'][partition]['PARTITION'])
                free = sensors.Disk.disk_free(config.THEME_DATA['STATS']['DISKS'][partition]['PARTITION'])
                usage_percent = sensors.Disk.disk_usage_percent(config.THEME_DATA['STATS']['DISKS'][partition]['PARTITION'])

                if config.THEME_DATA['STATS']['DISKS'][partition]['USED'].get("GRAPH", False):
                    sectionConfig = config.THEME_DATA['STATS']['DISKS'][partition]['USED']['GRAPH']
                    if sectionConfig.get("SHOW", False):
                        bar_factory(usage_percent, sectionConfig)

                if config.THEME_DATA['STATS']['DISKS'][partition]['USED'].get("TEXT", False):
                    sectionConfig = config.THEME_DATA['STATS']['DISKS'][partition]['USED']['TEXT']
                    if sectionConfig.get("SHOW", False):
                        used_text = format_number(used, sectionConfig, "", True)
                        text_factory(used_text, used, sectionConfig)

                if config.THEME_DATA['STATS']['DISKS'][partition]['USED'].get("PERCENT_TEXT", False):
                    sectionConfig = config.THEME_DATA['STATS']['DISKS'][partition]['USED']['PERCENT_TEXT']
                    if sectionConfig.get("SHOW", False):
                        percent_text = format_number(usage_percent, sectionConfig, "%")
                        text_factory(percent_text, usage_percent, sectionConfig)

                if config.THEME_DATA['STATS']['DISKS'][partition].get("TOTAL", False):
                    sectionConfig = config.THEME_DATA['STATS']['DISKS'][partition]['TOTAL']['TEXT']
                    if sectionConfig.get("SHOW", False):
                        total_text = format_number((free + used), sectionConfig, "", True)
                        text_factory(total_text, (free + used), sectionConfig)

                if config.THEME_DATA['STATS']['DISKS'][partition]['FREE'].get("TEXT", False):
                    sectionConfig = config.THEME_DATA['STATS']['DISKS'][partition]['FREE']['TEXT']
                    if sectionConfig.get("SHOW", False):
                        free_text = format_number(free, sectionConfig, "", True)
                        text_factory(free_text, free, sectionConfig)

        # KEEPING DISK CONFIG FOR BACKWARDS COMPATIBILITY
        
        used = sensors.Disk.disk_used()
        free = sensors.Disk.disk_free()
        usage_percent = sensors.Disk.disk_usage_percent()
        
        if config.THEME_DATA['STATS']['DISK']['USED']['GRAPH'].get("SHOW", False):
            sectionConfig = config.THEME_DATA['STATS']['DISK']['USED']['GRAPH']
            bar_factory(usage_percent, sectionConfig)

        if config.THEME_DATA['STATS']['DISK']['USED']['TEXT'].get("SHOW", False):
            sectionConfig = config.THEME_DATA['STATS']['DISK']['USED']['TEXT']
            used_text = format_number(used, sectionConfig, "", True)
            text_factory(used_text, used, sectionConfig)

        if config.THEME_DATA['STATS']['DISK']['USED']['PERCENT_TEXT'].get("SHOW", False):
            sectionConfig = config.THEME_DATA['STATS']['DISK']['USED']['PERCENT_TEXT']
            percent_text = format_number(usage_percent, sectionConfig, "%")
            text_factory(percent_text, usage_percent, sectionConfig)

        if config.THEME_DATA['STATS']['DISK']['TOTAL']['TEXT'].get("SHOW", False):
            sectionConfig = config.THEME_DATA['STATS']['DISK']['TOTAL']['TEXT']
            total_text = format_number((free + used), sectionConfig, "", True)
            text_factory(total_text, (free + used), sectionConfig)

        if config.THEME_DATA['STATS']['DISK']['FREE']['TEXT'].get("SHOW", False):
            sectionConfig = config.THEME_DATA['STATS']['DISK']['FREE']['TEXT']
            free_text = format_number(free, sectionConfig, "", True)
            text_factory(free_text, free, sectionConfig)

class Net:
    @staticmethod
    def stats():
        interval = config.THEME_DATA['STATS']['CPU']['PERCENTAGE'].get("INTERVAL", None)
        upload_wlo, uploaded_wlo, download_wlo, downloaded_wlo = sensors.Net.stats(WLO_CARD, interval)

        if config.THEME_DATA['STATS']['NET']['WLO']['UPLOAD']['TEXT'].get("SHOW", False):
            sectionConfig = config.THEME_DATA['STATS']['NET']['WLO']['UPLOAD']['TEXT']
            upload_wlo_text = format_number(upload_wlo, sectionConfig, "/s", True)
            text_factory(upload_wlo_text, upload_wlo, sectionConfig)

        if config.THEME_DATA['STATS']['NET']['WLO']['UPLOADED']['TEXT'].get("SHOW", False):
            sectionConfig = config.THEME_DATA['STATS']['NET']['WLO']['UPLOADED']['TEXT']
            uploaded_wlo_text = format_number(uploaded_wlo, sectionConfig, "", True)
            text_factory(uploaded_wlo_text, uploaded_wlo, sectionConfig)

        if config.THEME_DATA['STATS']['NET']['WLO']['DOWNLOAD']['TEXT'].get("SHOW", False):
            sectionConfig = config.THEME_DATA['STATS']['NET']['WLO']['DOWNLOAD']['TEXT']
            download_wlo_text = format_number(download_wlo, sectionConfig, "/s", True)
            text_factory(download_wlo_text, download_wlo, sectionConfig)

        if config.THEME_DATA['STATS']['NET']['WLO']['DOWNLOADED']['TEXT'].get("SHOW", False):
            sectionConfig = config.THEME_DATA['STATS']['NET']['WLO']['DOWNLOADED']['TEXT']
            downloaded_wlo_text = format_number(downloaded_wlo, sectionConfig, "", True)
            text_factory(downloaded_wlo_text, downloaded_wlo, sectionConfig)

        upload_eth, uploaded_eth, download_eth, downloaded_eth = sensors.Net.stats(ETH_CARD, interval)

        if config.THEME_DATA['STATS']['NET']['ETH']['UPLOAD']['TEXT'].get("SHOW", False):
            sectionConfig = config.THEME_DATA['STATS']['NET']['ETH']['UPLOAD']['TEXT']
            upload_eth_text = format_number(upload_eth, sectionConfig, "/s", True)
            text_factory(upload_eth_text, upload_eth, sectionConfig)

        if config.THEME_DATA['STATS']['NET']['ETH']['UPLOADED']['TEXT'].get("SHOW", False):
            sectionConfig = config.THEME_DATA['STATS']['NET']['ETH']['UPLOADED']['TEXT']
            uploaded_eth_text = format_number(uploaded_eth, sectionConfig, "", True)
            text_factory(uploaded_eth_text, uploaded_eth, sectionConfig)

        if config.THEME_DATA['STATS']['NET']['ETH']['DOWNLOAD']['TEXT'].get("SHOW", False):
            sectionConfig = config.THEME_DATA['STATS']['NET']['ETH']['DOWNLOAD']['TEXT']
            download_eth_text = format_number(download_eth, sectionConfig, "/s", True)
            text_factory(download_eth_text, download_eth, sectionConfig)

        if config.THEME_DATA['STATS']['NET']['ETH']['DOWNLOADED']['TEXT'].get("SHOW", False):
            sectionConfig = config.THEME_DATA['STATS']['NET']['ETH']['DOWNLOADED']['TEXT']
            downloaded_eth_text = format_number(downloaded_eth, sectionConfig, "", True)
            text_factory(downloaded_eth_text, downloaded_eth, sectionConfig)


class Date:
    @staticmethod
    def stats():
        date_now = datetime.datetime.now()

        if platform.system() == "Windows":
            # Windows does not have LC_TIME environment variable, use deprecated getdefaultlocale() that returns language code following RFC 1766
            lc_time = locale.getdefaultlocale()[0]
        else:
            lc_time = babel.dates.LC_TIME

        if config.THEME_DATA['STATS']['DATE']['DAY']['TEXT'].get("SHOW", False):
            sectionConfig = config.THEME_DATA['STATS']['DATE']['DAY']['TEXT']
            date_format = sectionConfig.get("FORMAT", 'medium')
            display.lcd.DisplayText(
                text=f"{babel.dates.format_date(date_now, format=date_format, locale=lc_time)}",
                x=sectionConfig.get("X", 0),
                y=sectionConfig.get("Y", 0),
                font=sectionConfig.get("FONT", config.THEME_DEFAULTS['FONT']),
                font_size=sectionConfig.get("FONT_SIZE", config.THEME_DEFAULTS['FONT_SIZE']),
                font_color=sectionConfig.get("FONT_COLOR", config.THEME_DEFAULTS['FONT_COLOR']),
                background_color=sectionConfig.get("BACKGROUND_COLOR", config.THEME_DEFAULTS['TEXT_BACKGROUND_COLOR']),
                background_image=get_full_path(config.THEME_DATA['PATH'], sectionConfig.get("BACKGROUND_IMAGE", config.THEME_DEFAULTS['TEXT_BACKGROUND_IMAGE']))
            )

        if config.THEME_DATA['STATS']['DATE']['HOUR']['TEXT'].get("SHOW", False):
            sectionConfig = config.THEME_DATA['STATS']['DATE']['HOUR']['TEXT']
            time_format = sectionConfig.get("FORMAT", 'medium')
            display.lcd.DisplayText(
                text=f"{babel.dates.format_time(date_now, format=time_format, locale=lc_time)}",
                x=sectionConfig.get("X", 0),
                y=sectionConfig.get("Y", 0),
                font=sectionConfig.get("FONT", config.THEME_DEFAULTS['FONT']),
                font_size=sectionConfig.get("FONT_SIZE", config.THEME_DEFAULTS['FONT_SIZE']),
                font_color=sectionConfig.get("FONT_COLOR", config.THEME_DEFAULTS['FONT_COLOR']),
                background_color=sectionConfig.get("BACKGROUND_COLOR", config.THEME_DEFAULTS['TEXT_BACKGROUND_COLOR']),
                background_image=get_full_path(config.THEME_DATA['PATH'], sectionConfig.get("BACKGROUND_IMAGE", config.THEME_DEFAULTS['TEXT_BACKGROUND_IMAGE']))
            )
