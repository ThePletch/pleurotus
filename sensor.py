from abc import ABC, abstractmethod
import logging
import time
from typing import Generic, Literal, Protocol, TypedDict, TypeVar

import board
import busio
from adafruit_ahtx0 import AHTx0
from adafruit_scd4x import SCD4X

from config import SensorConfig

SensorReading = TypeVar('SensorReading', covariant=True)


class HardwareSensor(Protocol[SensorReading]):
    data_ready: bool

    def get_reading(self) -> SensorReading: ...


class Sensor(Generic[SensorReading], ABC):
    config: SensorConfig
    current_reading: SensorReading
    has_reading: bool

    @abstractmethod
    def _build_sensor(self) -> HardwareSensor[SensorReading]: ...

    @abstractmethod
    def reading_from_sensor(self) -> SensorReading: ...

    def __init__(self, config: SensorConfig):
        self.config = config
        self.has_reading = False
        self._sensor = self._build_sensor()

    def get_current_reading(self) -> SensorReading:
        if self.has_reading:
            return self.current_reading
        raise IOError("No reading available.")

    def get_new_reading(self) -> None:
        time_waited = 0.0
        while not self._sensor.data_ready:
            if time_waited > self.config.read_timeout:
                raise RuntimeError(f"Timed out waiting for AHT20 reading ({time_waited}s)")

            logging.debug("Waiting for AHT20 to have available reading...")
            time.sleep(self.config.poll_interval_seconds)
            time_waited += self.config.poll_interval_seconds

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
        return {
            'co2_ppm': self._sensor.CO2,
            'temp_c': self._sensor.temperature,
            'relative_humidity_100': self._sensor.relative_humidity,
        }
