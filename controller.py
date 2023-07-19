from dataclasses import dataclass
import importlib.util
try:
    # necessary to be able to do development on
    importlib.util.find_spec('RPi.GPIO')
    import RPi.GPIO as GPIO
except ImportError:
    import FakeRPi.GPIO as GPIO
import logging
from typing import Literal

from controller_types import (
    DeviceController,
    MonodirectionalController,
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
    """
    The CO2 controller only turns on the exhaust when the humidifier is off.

    This avoids fog being exhausted from the chamber before it's able to evaporate into the air and increase humidity levels.
    """
    humidity_controller: HumidityController
    target_reading: Literal['co2_ppm'] = 'co2_ppm'
    measure_name = "co2"
    device_name = "exhaust_fan"

    def should_be_active(self, value: float) -> bool:
        base_active_state = super().should_be_active(value)
        if not self.humidity_controller.should_be_active(self.humidity_controller.reader()):
            return base_active_state
        elif base_active_state:
            logging.debug("Exhaust is waiting to activate due to high CO2 levels, but is disabled while the humidifier runs.")
        return False


@dataclass
class TemperatureMonitor(SCDMonitor):
    target_reading: Literal['temp_c'] = 'temp_c'
    measure_name = "temp"
