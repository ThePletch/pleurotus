from typing import Literal, TypedDict
from typing_extensions import TypeGuard

import logging
import time

from board import I2C
from adafruit_scd4x import SCD4X

SCD41Reading = TypedDict('SCD41Reading', {
    'co2_ppm': float,
    'relative_humidity_100': float,
    'temp_f': float,
})
ReadingKeys = Literal['co2_ppm', 'relative_humidity_100', 'temp_f']

# How often to poll the SCD-41 for a fresh reading upon request.
POLL_INTERVAL_SECONDS = 5


class SCD41:
    current_reading: SCD41Reading
    has_reading: bool

    def __init__(self):
        self.has_reading = False
        self._scd4x = SCD4X(I2C())
        self._scd4x.start_periodic_measurement()

    def get_new_reading(self) -> None:
        while not self._scd4x.data_ready:
            logging.debug("Waiting for SCD-41 to have available reading...")
            time.sleep(POLL_INTERVAL_SECONDS)
            # TODO timeout

        self.current_reading = {
            'co2_ppm': self._scd4x.CO2,
            'temp_f': self._scd4x.temperature,
            'relative_humidity_100': self._scd4x.relative_humidity,
        }
        self.has_reading = True

    def get_current_reading(self, key: ReadingKeys) -> float:
        if has_reading(self):
            return self.current_reading[key]
        raise IOError(f"No reading available for {key}")


class SCD41WithReading(SCD41):
    current_reading: SCD41Reading


def has_reading(sensor: SCD41) -> TypeGuard[SCD41WithReading]:
    return sensor.has_reading
