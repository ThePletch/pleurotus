from prometheus_client import Gauge

MEASURE_VALUE = Gauge(
    'measure_value',
    "Reported value for a measure",
    ['measure'],
)
DEVICE_ACTIVE = Gauge(
    'device_active',
    "Whether a device managing a measure is active",
    ['device', 'measure'],
)
DEVICE_THRESHOLD = Gauge(
    'device_threshold',
    "The measure threshold at which a device activates/deactivates",
    ['device', 'measure', 'target'],
)
DEVICE_ZERO_ENERGY_BAND = Gauge(
    'device_zero_energy_band',
    "The amount that a measure must exceed its threshold for a device to activate",
    ['device', 'measure', 'target'],
)
