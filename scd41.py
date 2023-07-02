from typing import Literal, Optional, TypedDict, TypeGuard


SCD41Reading = TypedDict('SCD41Reading', {
    'co2_ppm': float,
    'relative_humidity_100': float,
    'temp_f': float,
})
ReadingKeys = Literal['co2_ppm', 'relative_humidity_100', 'temp_f']


class SCD41:
    current_reading: Optional[SCD41Reading]
    has_reading: bool

    def __init__(self):
        self.has_reading = False
        # TODO handle all the pin reads and initialization stuff

    # TODO
    def get_new_reading(self) -> None: ...

    def get_current_reading(self, key: ReadingKeys) -> float:
        if has_reading(self):
            return self.current_reading[key]
        raise IOError(f"No reading available for {key}")


class SCD41WithReading(SCD41):
    current_reading: SCD41Reading


def has_reading(sensor: SCD41) -> TypeGuard[SCD41WithReading]:
    return sensor.has_reading
