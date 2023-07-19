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


@dataclass
class SCD41Config:
    """
    How often to poll the SCD-41 for a fresh reading upon request.
    """
    poll_interval_seconds: float = 5.0
    read_timeout: float = 120.0


@dataclass
class GreenhouseConfig(YAMLWizard):
    humidifier: HumidifierConfig
    exhaust: ExhaustConfig
    scd41: SCD41Config
    update_interval_seconds: float = 10.0
    metrics_server_port: int = 9100
