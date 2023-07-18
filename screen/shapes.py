from dataclasses import dataclass

from screen_types import Renderable


@dataclass
class Rectangle(Renderable):
    x: int
    y: int
    width: int
    height: int
    on: bool

    def render(self, screen):
        for x in range(self.x, self.x + self.width):
            for y in range(self.y, self.y + self.height):
                screen.set(x, y, self.on)
