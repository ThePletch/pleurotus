from typing import Callable, Generic

from abc import ABC, abstractmethod
from dataclasses import dataclass
import logging

from types import MonodirectionalControllerConfig, UnitMeasure


@dataclass
class MonodirectionalController(ABC, Generic[UnitMeasure]):
    """
    Human-readable name of the measure this controller manages
    """
    @property
    @abstractmethod
    def measure_name(self) -> str: ...

    config: MonodirectionalControllerConfig[UnitMeasure]

    """
    Function that returns the current value of the target measurement.
    The function is expected to handle waiting for a value from the sensor. If no value is available,
    even after waiting, it should raise an `IOError`.
    """
    reader: Callable[[], UnitMeasure]

    """
    Function that sets the control device to an on/off state.
    As above, this function should raise an `IOError` if it is unable to change device state.
    """
    toggle: Callable[[bool], None]

    active: bool = False

    def should_be_active(self, value: UnitMeasure) -> bool:
        # if the controller is already active, it'll turn back off once we're past our threshold.
        if self.active:
            if self.config['target_side_of_threshold'] == 'below':
                return value > self.config['threshold_value']
            return value < self.config['threshold_value']

        # if the controller isn't active, it won't activate until we're past our threshold by at least the configured zero-energy band.
        if self.config['target_side_of_threshold'] == 'below':
            return value > self.config['threshold_value'] + self.config['zero_energy_band']

        return value < self.config['threshold_value'] - self.config['zero_energy_band']

    def control_state(self) -> None:
        try:
            current_value = self.reader()
        except IOError:
            logging.warning(f"Failed to read a new measure value for {self.measure_name}, remaining in current state")
        target_state = self.should_be_active(current_value)
        if self.active != target_state:
            logging.debug(f"Switching {self.measure_name} controller to {'active' if target_state else 'inactive'}")
            self.toggle(target_state)

# Concrete controller classes


class HumidityController(MonodirectionalController[float]):
    measure_name = "relative humidity"


class CO2Controller(MonodirectionalController[float]):
    measure_name = "CO2 PPM"
