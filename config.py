from dataclasses import dataclass
from dataclass_wizard import YAMLWizard


@dataclass
class HumidifierConfig:
    gpio_pin_id: int
    minimum_humidity_pct: float
    zero_energy_band: float


@dataclass
class ExhaustConfig:
    gpio_pin_id: int
    maximum_co2_ppm: int
    zero_energy_band: int


class GreenhouseConfig(YAMLWizard):
    humidifier: HumidifierConfig
    exhaust: ExhaustConfig
    update_interval_seconds: float
