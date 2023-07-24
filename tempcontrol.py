import logging
import time

from prometheus_client import start_http_server

from config import GreenhouseConfig
from controller import (
    CO2Controller,
    HumidityController,
    PinOutput,
    TemperatureMonitor,
)
from controller_types import Controller, Monitor
from sensor import AHT20, SCD41

"""
Control code for managing switching of humidity and CO2 controls.
Assumes the following:
* Humidity and CO2 are measured via an SCD-41 sensor connected via the I2C protocol

* Humidity is managed with a humidification device controlled by a single power toggle
    * In our case, an aquarium fogger in a chamber circulated by a waterproof 12V fan
* Dehumidification will not be necessary

* CO2 levels are reduced by a simple exhaust fan that vents air out of the chamber, with intake coming through a passive filtered port on the sheeting
* CO2 will not need to be increased.

Future features:
* LED panel controls for displaying current levels/stats
* Control of target environment levels via knobs/dials (potentiometers are hard)
"""
logging.basicConfig(level=logging.INFO)
config = GreenhouseConfig.from_yaml_file('config.yaml')


def controllers(aht20: AHT20, scd41: SCD41) -> list[Controller]:
    return [
        HumidityController(
            config={
                'target_side_of_threshold': 'above',
                'threshold_value': config.humidifier.minimum_humidity_pct,
                'zero_energy_band': config.humidifier.zero_energy_band,
            },
            sensor=aht20,
            device=PinOutput(config.humidifier.gpio_pin_id),
        ),
        CO2Controller(
            config={
                'target_side_of_threshold': 'below',
                'threshold_value': config.exhaust.maximum_co2_ppm,
                'zero_energy_band': config.exhaust.zero_energy_band,
            },
            sensor=scd41,
            device=PinOutput(config.exhaust.gpio_pin_id),
        ),
    ]


def monitors(sensor: AHT20) -> list[Monitor]:
    return [
        TemperatureMonitor(
            sensor=sensor,
        ),
    ]


if __name__ == '__main__':
    start_http_server(config.metrics_server_port)
    scd41 = SCD41(config.scd41)
    aht20 = AHT20(config.aht20)
    device_controllers = controllers(aht20, scd41)
    measure_monitors = monitors(aht20)

    while True:
        logging.debug("Getting new readings...")
        aht20.get_new_reading()
        scd41.get_new_reading()
        logging.debug("Got readings.")

        for monitor in measure_monitors:
            logging.debug(f"Fetching value from {monitor.measure_name} monitor...")
            monitor.read_value()
            logging.debug("Done.")

        for controller in device_controllers:
            logging.debug(f"Updating state for {controller.device_name} controller...")
            controller.control_state()
            logging.debug("Done.")

        time.sleep(config.update_interval_seconds)
