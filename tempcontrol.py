from typing import Any

import RPi.GPIO as GPIO
import logging
import time

from scd41 import SCD41
from controller import HumidityController, HumidityGatedCO2Controller

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
logging.basicConfig(level=logging.DEBUG)

class PinOutput:
    def __init__(self, pin: int):
        self._pin = pin
        GPIO.setup(self._pin, GPIO.OUT)

    def set(self, state: bool) -> None:
        GPIO.output(self._pin, state)


if __name__ == '__main__':
    sensor = SCD41()

    humidifier_pin = PinOutput(HUMIDIFIER_POWER_TOGGLE_PIN)
    exhaust_pin = PinOutput(EXHAUST_POWER_TOGGLE_PIN)

    humidity_control = HumidityController(
        config={
            'target_side_of_threshold': 'above',
            # pretty sure that RH is reported in 0-100 scale
            'threshold_value': 80.0,
            'zero_energy_band': 2.0,
        },
        # read from SCD-41 sensor
        reader=(lambda: sensor.get_current_reading('relative_humidity_100')),
        toggle=humidifier_pin.set
    )

    """
    typical indoor CO2 level is 400 ppm,
    mushrooms want between 700-1000ppm typically
    """
    co2_control = HumidityGatedCO2Controller(
        config={
            'target_side_of_threshold': 'below',
            'threshold_value': 800.0,
            'zero_energy_band': 100.0,
        },
        # read from SCD-41 sensor
        reader=(lambda: sensor.get_current_reading('co2_ppm')),
        toggle=exhaust_pin.set,
        humidity_controller=humidity_control,
    )

    while True:
        logging.debug("Getting new reading...")
        sensor.get_new_reading()
        logging.debug("Got a reading.")
        for controller in [humidity_control, co2_control]:
            logging.debug(f"Updating state for {controller.measure_name} controller...")
            controller.control_state()
            logging.debug("Done.")
        time.sleep(10)
