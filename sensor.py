from abc import ABC, abstractmethod
from dataclasses import dataclass, field
import logging
import time
from typing import Generic, Literal, Protocol, TypedDict, TypeVar
try:
    import board
except NotImplementedError:
    import os
    if os.environ['HARDCODED_BOARD_PINS'] != 'true':
        logging.fatal(
            "Could not import dynamic pin settings. "
            "To use hardcoded settings, set HARDCODED_BOARD_PINS env to true"
        )
        raise

    logging.warning("Using hardcoded board pins.")
    import test.hardcoded_board as board

import busio
from adafruit_ahtx0 import AHTx0
from adafruit_scd4x import SCD4X

from config import SensorConfig

SensorReading = TypeVar('SensorReading', covariant=True)


class HardwareSensor(Protocol[SensorReading]):
    def get_reading(self) -> SensorReading: ...


@dataclass
class Sensor(Generic[SensorReading], ABC):
    config: SensorConfig = field(default_factory=SensorConfig)
    current_reading: SensorReading = field(init=False)
    has_reading: bool = field(init=False, default=False)

    @abstractmethod
    def _build_sensor(self) -> HardwareSensor[SensorReading]: ...

    @abstractmethod
    def reading_from_sensor(self) -> SensorReading: ...

    def __post_init__(self):
        self._sensor = self._build_sensor()

    def get_current_reading(self) -> SensorReading:
        if self.has_reading:
            return self.current_reading
        raise IOError("No reading available.")

    def get_new_reading(self) -> None:
        self.current_reading = self.reading_from_sensor()
        self.has_reading = True


AHT20Reading = TypedDict('AHT20Reading', {
    'relative_humidity_100': float,
    'temp_c': float,
})
AHT20ReadingKey = Literal['relative_humidity_100', 'temp_c']


class AHT20(Sensor[AHT20Reading]):
    def _build_sensor(self):
        return AHTx0(busio.I2C(board.SCL, board.SDA))

    def reading_from_sensor(self):
        return {
            'temp_c': self._sensor.temperature,
            'relative_humidity_100': self._sensor.relative_humidity,
        }


SCD41Reading = TypedDict('SCD41Reading', {
    'co2_ppm': float,
    'relative_humidity_100': float,
    'temp_c': float,
})
SCD41ReadingKey = Literal['co2_ppm', 'relative_humidity_100', 'temp_c']


class SCD41(Sensor[SCD41Reading]):
    def _build_sensor(self):
        sensor = SCD4X(busio.I2C(board.SCL, board.SDA))
        sensor.start_periodic_measurement()
        return sensor

    def reading_from_sensor(self):
        time_waited = 0.0
        while not self._sensor.data_ready:
            if time_waited > self.config.read_timeout:
                raise RuntimeError(f"Timed out waiting for SCD-41 reading ({time_waited}s)")

            logging.debug("Waiting for SCD-41 to have available reading...")
            time.sleep(self.config.poll_interval_seconds)
            time_waited += self.config.poll_interval_seconds

        return {
            'co2_ppm': self._sensor.CO2,
            'temp_c': self._sensor.temperature,
            'relative_humidity_100': self._sensor.relative_humidity,
        }
