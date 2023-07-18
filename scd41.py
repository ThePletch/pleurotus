from typing import Literal, TypedDict
from typing_extensions import TypeGuard

import logging
import time

import board
import busio
from adafruit_scd4x import SCD4X

SCD41Reading = TypedDict('SCD41Reading', {
    'co2_ppm': float,
    'relative_humidity_100': float,
    'temp_c': float,
})
ReadingKeys = Literal['co2_ppm', 'relative_humidity_100', 'temp_c']

# How often to poll the SCD-41 for a fresh reading upon request.
POLL_INTERVAL_SECONDS = 5
READING_TIMEOUT = 120


class SCD41:
    current_reading: SCD41Reading
    has_reading: bool

    def __init__(self):
        self.has_reading = False
        self._scd4x = SCD4X(busio.I2C(board.SCL, board.SDA))
        self._scd4x.start_periodic_measurement()

    def get_new_reading(self) -> None:
        time_waited = 0
        while not self._scd4x.data_ready:
            if time_waited > READING_TIMEOUT:
                raise RuntimeError("Timed out waiting for SCD-41 reading ({time_waited}s)")

            logging.debug("Waiting for SCD-41 to have available reading...")
            time.sleep(POLL_INTERVAL_SECONDS)
            time_waited += POLL_INTERVAL_SECONDS

        self.current_reading = {
            'co2_ppm': self._scd4x.CO2,
            'temp_c': self._scd4x.temperature,
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
