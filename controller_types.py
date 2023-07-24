from abc import ABC, abstractmethod, abstractproperty
from dataclasses import dataclass, field
import logging
from typing import Literal, Protocol, TypedDict

from metrics import MEASURE_VALUE, DEVICE_ACTIVE, DEVICE_THRESHOLD
from sensor import SCD41, AHT20, SCD41ReadingKey, AHT20ReadingKey


class Settable(Protocol):
    def set(self, state: bool) -> None: ...


class Monitor(ABC):
    """
    Human-readable name of the measure this monitor reads
    """
    measure_name: str

    """
    Function that returns the current value of the target measurement.
    The function is expected to handle waiting for a value from the sensor.
    If no value is available, even after waiting, it should raise an `IOError`.
    """
    @abstractmethod
    def reader(self) -> float: ...

    def read_value(self) -> float:
        current_value = self.reader()
        MEASURE_VALUE.labels(measure=self.measure_name).set(current_value)
        logging.info(f"{self.measure_name}: {current_value}")

        return current_value


class Controller(Monitor, ABC):
    """
    Human-readable name of the device that this class toggles.
    """
    device_name: str

    active: bool = False

    """
    Function that sets the control device to an on/off state.
    As with `reader()`, this function should raise an `IOError` if it is unable to change device state.
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
            current_value = self.read_value()
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


class MonodirectionalControllerConfig(TypedDict):
    """
    Value at which our controller should activate its control device to manage the greenhouse's conditions,
    e.g. turn on exhaust to reduce CO2 levels
    """
    threshold_value: float

    """
    Whether the controller is tasked with keeping the reading above or below the threshold value.
    """
    target_side_of_threshold: Literal['above', 'below']

    """
    How far past our threshold should the value get before activating its control device?
    Setting this to a nonzero value avoids the device rapidly cycling around its threshold value.
    """
    zero_energy_band: float


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
class SCDMonitor(Monitor, ABC):
    sensor: SCD41

    @abstractproperty
    def target_reading(self) -> SCD41ReadingKey: ...

    def reader(self):
        return self.sensor.get_current_reading()[self.target_reading]


@dataclass
class AHTMonitor(Monitor, ABC):
    sensor: AHT20

    @abstractproperty
    def target_reading(self) -> AHT20ReadingKey: ...

    def reader(self):
        return self.sensor.get_current_reading()[self.target_reading]


@dataclass
class DeviceController(Controller):
    device: Settable

    def toggle(self, state):
        self.device.set(state)
