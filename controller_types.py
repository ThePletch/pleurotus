from typing import Literal, TypedDict


class MonodirectionalControllerConfig(TypedDict):
    """
    Value at which our controller should activate its control device to manage the greenhouse's conditions,
    e.g. turn on exhaust to reduce CO2 levels
    """
    threshold_value: float

    """
    Whether the controller is tasked with keeping the reading above or below the threshold value.
    """
    target_side_of_threshold: Literal['above', 'below']

    """
    How far past our threshold should the value get before activating its control device?
    Setting this to a nonzero value avoids the device rapidly cycling around its threshold value.
    """
    zero_energy_band: float
