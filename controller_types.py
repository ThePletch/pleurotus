from typing import Generic, Literal, Protocol, runtime_checkable, TypedDict, TypeVar

from abc import abstractmethod


@runtime_checkable
class Mathable(Protocol):
    """
    Protocol describing operations expected from something usable as a unit measure,
    i.e. "can be compared with other values" and "can be used to do basic arithmetic"
    """

    @abstractmethod
    def __lt__(self: 'UnitMeasure', other: 'UnitMeasure') -> bool: ...

    @abstractmethod
    def __gt__(self: 'UnitMeasure', other: 'UnitMeasure') -> bool: ...

    @abstractmethod
    def __add__(self: 'UnitMeasure', other: 'UnitMeasure') -> 'UnitMeasure': ...

    @abstractmethod
    def __sub__(self: 'UnitMeasure', other: 'UnitMeasure') -> 'UnitMeasure': ...


UnitMeasure = TypeVar('UnitMeasure', bound=Mathable)


class MonodirectionalControllerConfig(TypedDict, Generic[UnitMeasure]):
    """
    Value at which our controller should activate its control device to manage the greenhouse's conditions,
    e.g. turn on exhaust to reduce CO2 levels
    """
    threshold_value: UnitMeasure

    """
    Whether the controller is tasked with keeping the reading above or below the threshold value.
    """
    target_side_of_threshold: Literal['above', 'below']

    """
    How far past our threshold should the value get before activating its control device?
    Setting this to a nonzero value avoids the device rapidly cycling around its threshold value.
    """
    zero_energy_band: UnitMeasure
