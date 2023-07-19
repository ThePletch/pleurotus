import logging
import time
from typing import Literal, TypedDict
from typing_extensions import TypeGuard

import board
import busio
from adafruit_scd4x import SCD4X

from config import SCD41Config

SCD41Reading = TypedDict('SCD41Reading', {
    'co2_ppm': float,
    'relative_humidity_100': float,
    'temp_c': float,
})
ReadingKey = Literal['co2_ppm', 'relative_humidity_100', 'temp_c']


class SCD41:
    config: SCD41Config
    current_reading: SCD41Reading
    has_reading: bool

    def __init__(self, config: SCD41Config):
        self.config = config
        self.has_reading = False
        self._scd4x = SCD4X(busio.I2C(board.SCL, board.SDA))
        self._scd4x.start_periodic_measurement()

    def get_new_reading(self) -> None:
        time_waited = 0.0
        while not self._scd4x.data_ready:
            if time_waited > self.config.read_timeout:
                raise RuntimeError(f"Timed out waiting for SCD-41 reading ({time_waited}s)")

            logging.debug("Waiting for SCD-41 to have available reading...")
            time.sleep(self.config.poll_interval_seconds)
            time_waited += self.config.poll_interval_seconds

        self.current_reading = {
            'co2_ppm': self._scd4x.CO2,
            'temp_c': self._scd4x.temperature,
            'relative_humidity_100': self._scd4x.relative_humidity,
        }
        self.has_reading = True

    def get_current_reading(self, key: ReadingKey) -> float:
        if has_reading(self):
            return self.current_reading[key]
        raise IOError(f"No reading available for {key}")


class SCD41WithReading(SCD41):
    current_reading: SCD41Reading


def has_reading(sensor: SCD41) -> TypeGuard[SCD41WithReading]:
    return sensor.has_reading
