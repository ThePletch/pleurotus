from abc import ABC, abstractmethod, abstractproperty
from dataclasses import dataclass, field, InitVar
from datetime import datetime
import importlib.util
try:
    # necessary to be able to do development on
    importlib.util.find_spec('RPi.GPIO')
    import RPi.GPIO as GPIO
except ImportError:
    import FakeRPi.GPIO as GPIO
import logging
from typing import Literal, Protocol

from prometheus_client import Gauge

from controller_types import MonodirectionalControllerConfig
from scd41 import ReadingKeys, SCD41

MEASURE_VALUE = Gauge(
    'measure_value',
    "Reported value for a measure",
    ['measure'],
)
DEVICE_ACTIVE = Gauge(
    'device_active',
    "Whether a device managing a measure is active",
    ['device', 'measure'],
)
DEVICE_THRESHOLD = Gauge(
    'device_threshold',
    "The measure threshold at which a device activates/deactivates",
    ['device', 'measure', 'target'],
)


class Settable(Protocol):
    def set(self, state: bool) -> None: ...


class PinOutput(Settable):
    def __init__(self, pin: int):
        self._pin = pin
        GPIO.setup(self._pin, GPIO.OUT)

    def set(self, state: bool) -> None:
        GPIO.output(self._pin, state)


class Controller(ABC):
    """
    Human-readable name of the measure this controller manages
    """
    measure_name: str

    """
    Human-readable name of the device that this class toggles.
    """
    device_name: str

    active: bool = False

    """
    Function that returns the current value of the target measurement.
    The function is expected to handle waiting for a value from the sensor. If no value is available,
    even after waiting, it should raise an `IOError`.
    """
    @abstractmethod
    def reader(self) -> float: ...

    """
    Function that sets the control device to an on/off state.
    As above, this function should raise an `IOError` if it is unable to change device state.
    """
    @abstractmethod
    def toggle(self, state: bool) -> None: ...

    """
    Returns whether the device should be active for a given measure value.
    """
    @abstractmethod
    def should_be_active(self, value: float) -> bool: ...

    """
    Loop that handles reading the measure value, toggling the device based on
    the result of should_be_active, and
    """
    def control_state(self) -> None:
        try:
            current_value = self.reader()
            MEASURE_VALUE.labels(measure=self.measure_name).set(current_value)
            logging.info(f"{self.measure_name}: {current_value}")
        except IOError:
            logging.warning(f"Failed to read a new measure value for {self.measure_name}, remaining in current state")
            return
        target_state = self.should_be_active(current_value)
        DEVICE_ACTIVE.labels(
            device=self.device_name,
            measure=self.measure_name,
        ).set(1 if target_state else 0)
        logging.debug(f"{self.device_name}: {target_state}")
        if self.active != target_state:
            logging.debug(f"Switching {self.measure_name} controller to {'active' if target_state else 'inactive'}")
            self.toggle(target_state)
            self.active = target_state


@dataclass
class MonodirectionalController(Controller):
    config: MonodirectionalControllerConfig
    active: bool = field(init=False, default=False)

    def __post_init__(self):
        DEVICE_THRESHOLD.labels(
            device=self.device_name,
            measure=self.measure_name,
            target=self.config['target_side_of_threshold'],
        ).set(self.config['threshold_value'])

    def should_be_active(self, value: float) -> bool:
        # if the controller is already active, it'll turn back off once we're past our threshold.
        if self.active:
            if self.config['target_side_of_threshold'] == 'below':
                return value > self.config['threshold_value']
            return value < self.config['threshold_value']

        # if the controller isn't active, it won't activate until we're past our threshold by at least the configured zero-energy band.
        if self.config['target_side_of_threshold'] == 'below':
            return value > self.config['threshold_value'] + self.config['zero_energy_band']

        return value < self.config['threshold_value'] - self.config['zero_energy_band']


@dataclass
class SCDController(Controller, ABC):
    sensor: SCD41

    @abstractproperty
    def target_reading(self) -> ReadingKeys: ...

    def reader(self):
        return self.sensor.get_current_reading(self.target_reading)


@dataclass
class DeviceController(Controller):
    device: Settable

    def toggle(self, state):
        self.device.set(state)


@dataclass
class HumidityController(MonodirectionalController, SCDController, DeviceController):
    target_reading: Literal['relative_humidity_100'] = 'relative_humidity_100'
    measure_name = "relative_humidity"
    device_name = "humidifier"


@dataclass
class CO2Controller(MonodirectionalController, SCDController, DeviceController):
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
class TemperatureController(MonodirectionalController, SCDController):
    target_reading: Literal['temp_c'] = 'temp_c'
    measure_name = "temp"
    device_name = "heater_nonexistent"

    # no device attached right now
    def toggle(self, state):
        pass


@dataclass
class LightsController(Controller):
    active_hour_ranges: list[tuple[int, int]]

    # obviously not a very useful metric to report to our aggregator,
    # but useful for debugging if it drifts
    measure_name: InitVar[str] = "hour_of_day"
    device_name: InitVar[str] = "lights_nonexistent"

    def reader(self):
        return datetime.now().hour

    def should_be_active(self, value):
        for hour_range in self.active_hour_ranges:
            if value in range(*hour_range):
                return True

        return False

    # no device attached right now
    def toggle(self, state):
        pass
