import logging
import time

from prometheus_client import start_http_server

from scd41 import SCD41
from controller import (
    Controller,
    HumidityController,
    CO2Controller,
    LightsController,
    PinOutput,
    TemperatureController,
)

"""
Control code for managing switching of humidity and CO2 controls.
Assumes the following:
* Humidity and CO2 are measured via an SCD-41 sensor connected via the STEMMA QT protocol

* Humidity is managed with a humidification device controlled by a single power toggle
    * In our case, an aquarium fogger in a chamber circulated by a waterproof 12V fan
* Dehumidification will not be necessary

* CO2 levels are reduced by a simple exhaust fan that vents air out of the chamber, with intake coming through a passive filtered port on the sheeting
* CO2 will not need to be increased.

Future features:
* Alarm controls for when levels remain out of bounds for longer than a configured duration, configurable alert destinations
* LED panel controls for displaying current levels/stats
"""
HUMIDIFIER_POWER_TOGGLE_PIN = 4
EXHAUST_POWER_TOGGLE_PIN = 5
logging.basicConfig(level=logging.INFO)


def controllers(sensor: SCD41) -> list[Controller]:
    humidifier_pin = PinOutput(HUMIDIFIER_POWER_TOGGLE_PIN)
    exhaust_pin = PinOutput(EXHAUST_POWER_TOGGLE_PIN)

    humidity_control = HumidityController(
        config={
            'target_side_of_threshold': 'above',
            # pretty sure that RH is reported in 0-100 scale
            'threshold_value': 80.0,
            'zero_energy_band': 2.0,
        },
        sensor=sensor,
        device=humidifier_pin,
    )

    """
    typical indoor CO2 level is 400 ppm,
    mushrooms want between 700-1000ppm typically
    """
    co2_control = CO2Controller(
        config={
            'target_side_of_threshold': 'below',
            'threshold_value': 800.0,
            'zero_energy_band': 100.0,
        },
        sensor=sensor,
        device=exhaust_pin,
        humidity_controller=humidity_control,
    )

    """
    config is accurate to what we want, but there's not currently
    a heater in the system since it's summertime.
    this exists primarily to export temperature readings to the associated
    metrics service.
    """
    temp_control = TemperatureController(
        config={
            'target_side_of_threshold': 'above',
            'threshold_value': 70.0,
            'zero_energy_band': 2.0,
        },
        sensor=sensor,
    )

    lights_control = LightsController(
        active_hour_ranges=[
            # 8am to 8pm (hour is zero indexed)
            (7, 19),
        ]
    )

    return [
        humidity_control,
        co2_control,
        lights_control,
        temp_control,
    ]


if __name__ == '__main__':
    start_http_server(9100)
    sensor = SCD41()
    measure_controllers = controllers(sensor)

    while True:
        logging.debug("Getting new reading...")
        sensor.get_new_reading()
        logging.debug("Got a reading.")
        for controller in measure_controllers:
            logging.debug(f"Updating state for {controller.measure_name} controller...")
            controller.control_state()
            logging.debug("Done.")
        time.sleep(10)
