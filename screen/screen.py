from dataclasses import dataclass, field
from screen_types import AddressableBWScreen, Renderable


class Screen(Renderable):
    elements: list[Renderable]

    def render(self, screen):
        screen.clear()

        for element in self.elements:
            element.render(screen)


ON = "■"
OFF = " "


@dataclass
class AddressableTextScreen(AddressableBWScreen):
    """
    Test screen that allows printing the screen's display to the console
    """
    width: int
    height: int
    pixels: list[list[int]] = field(init=False)

    def __post_init__(self):
        self.pixels = [
            [
                OFF
                for x in range(self.width)
            ]
            for y in range(self.height)
        ]

    def set(self, x, y, on):
        self.pixels[y][x] = ON if on else OFF

    def clear(self):
        for x in range(self.width):
            for y in range(self.height):
                self.pixels[y][x] = OFF

    def print(self):
        for row in self.pixels:
            print("".join(row))
