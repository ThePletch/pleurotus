from dataclasses import dataclass
import importlib.util
try:
    # necessary to be able to do development on
    importlib.util.find_spec('RPi.GPIO')
    import RPi.GPIO as GPIO
except ImportError:
    import FakeRPi.GPIO as GPIO
from typing import Literal

from controller_types import (
    DeviceController,
    MonodirectionalController,
    AHTMonitor,
    SCDMonitor,
    Settable,
)


class PinOutput(Settable):
    def __init__(self, pin: int):
        self._pin = pin
        GPIO.setup(self._pin, GPIO.OUT)

    def set(self, state: bool) -> None:
        GPIO.output(self._pin, state)


@dataclass
class HumidityController(MonodirectionalController, DeviceController, SCDMonitor):
    target_reading: Literal['relative_humidity_100'] = 'relative_humidity_100'
    measure_name = "relative_humidity"
    device_name = "humidifier"


@dataclass
class CO2Controller(MonodirectionalController, DeviceController, SCDMonitor):
    target_reading: Literal['co2_ppm'] = 'co2_ppm'
    measure_name = "co2"
    device_name = "exhaust_fan"


@dataclass
class TemperatureMonitor(AHTMonitor):
    target_reading: Literal['temp_c'] = 'temp_c'
    measure_name = "temp"
