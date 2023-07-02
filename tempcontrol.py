import time

from scd41 import SCD41
from controller import CO2Controller, HumidityController

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

if __name__ == '__init__':
    sensor = SCD41()

    humidity_control = HumidityController(
        config={
            'target_side_of_threshold': 'above',
            # pretty sure that RH is reported in 0-100 scale
            'threshold_value': 90.0,
            'zero_energy_band': 2.0,
        },
        # read from SCD-41 sensor
        reader=(lambda: sensor.get_current_reading('relative_humidity_100')),
        # TODO turn on/off humidifier, i.e. toggle power control pin state
        toggle=(lambda state: None)
    )

    co2_control = CO2Controller(
        config={
            'target_side_of_threshold': 'below',
            'threshold_value': 800.0,
            'zero_energy_band': 100.0,
        },
        # read from SCD-41 sensor
        reader=(lambda: sensor.get_current_reading('co2_ppm')),
        # turn on/off exhaust fan, i.e. toggle power control pin state leading to voltage stepper, then to fan
        toggle=(lambda state: None)
    )

    while True:
        time.sleep(10)
        sensor.get_new_reading()
        for controller in [humidity_control, co2_control]:
            controller.control_state()
