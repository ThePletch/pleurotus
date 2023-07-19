from abc import ABC, abstractmethod
from typing import Protocol


class AddressableBWScreen(Protocol):
    width: int
    height: int

    """
    Turns the designated pixel on or off.

    Raises an IndexError if x or y is outside of the specified w/h
    """
    def set(self, x: int, y: int, on: bool) -> None: ...

    """
    Turns all pixels on the screen off.
    """
    def clear(self) -> None: ...


class Renderable(Protocol):
    def render(self, screen: AddressableBWScreen) -> None: ...


class Composition(Renderable, ABC):
    @abstractmethod
    def components(self) -> list[Renderable]:
        pass

    def render(self, screen):
        for component in self.components():
            component.render(screen)
