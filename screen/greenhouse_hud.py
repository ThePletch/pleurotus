"""
Assumes a 128x64 screen

At the top, horizontally arranged numeric readouts

Below that, vertical bar readouts of current readings vs targets

3x5 font

3px bars

bar examples on 20px:

Humidity bar (min 40%, val 60%, target 80%)
...................*
**********.........*
**********.........*

Humidity bar (min 40%, target 60%, value 80%)
.........*..........
**********..........
********************

CO2 bar (max 1200, target 800, curr 1000)
*...................
*........***********
*........***********

CO2 bar (max 1200, curr 800, target 1000)
.........*..........
.........***********
********************


*.*.
***.
*.*.
*.*.

"""
from dataclasses import dataclass
from math import floor
from typing import Literal

from font import Text
from screen import AddressableTextScreen
from screen_types import Composition
from shapes import Rectangle


@dataclass
class Bar(Composition):
    """
    When target direction is 'up',
    the boundary must be lower than any potential reading.
    When target direction is 'down',
    the boundary must be higher than any potential reading.
    """
    target_direction: Literal['up', 'down']
    target: float
    reading: float
    boundary: float
    x: int
    y: int
    width: int

    @property
    def max_raw(self):
        if self.target_direction == 'down':
            return self.boundary

        return max(self.reading, self.target)

    @property
    def min_raw(self):
        if self.target_direction == 'up':
            return self.boundary

        return min(self.reading, self.target)

    @property
    def size_raw(self):
        return self.max_raw - self.min_raw

    @property
    def target_x(self):
        return self.x_pos(self.target)

    @property
    def reading_x(self):
        return self.x_pos(self.reading)

    @property
    def boundary_x(self):
        return self.x_pos(self.boundary)

    def x_pos(self, value):
        return floor(((value - self.min_raw) / self.size_raw) * self.width)

    def components(self):
        reading_rect_min = min(self.boundary_x, self.reading_x)
        reading_rect_max = max(self.boundary_x, self.reading_x)
        reading_rect_width = reading_rect_max - reading_rect_min

        # high goes from boundary to the closer of the reading and the target
        high_reading_rect_edge = min(self.reading_x, self.target_x) if self.target_direction == 'up' else max(self.reading_x, self.target_x)
        high_reading_rect_min = min(self.boundary_x, high_reading_rect_edge)
        high_reading_rect_max = max(self.boundary_x, high_reading_rect_edge)
        high_reading_rect_width = high_reading_rect_max - high_reading_rect_min

        return [
            # Reading rect (bottom portion)
            Rectangle(self.x + reading_rect_min, self.y + 3, reading_rect_width, 1, True),
            # Reading rect (middle portion)
            Rectangle(self.x + high_reading_rect_min, self.y + 2, high_reading_rect_width, 3, True),
            # Target marker
            Rectangle(self.x + self.target_x, self.y, 1, 5, True),
        ]


@dataclass
class Toggle(Composition):
    x: int
    y: int
    on: bool
    label_char: str

    def components(self):
        return [
            Rectangle(self.x, self.y, 7, 9, True),
            Rectangle(self.x + 1, self.y + 1, 5, 7, self.on),
            Text(self.label_char, self.x + 2, self.y + 2, not self.on),
        ]


@dataclass
class MetricState:
    current: float
    target: float
    controller_running: bool


@dataclass
class HudState:
    co2: MetricState
    humidity: MetricState
    temp: float


@dataclass
class Hud(Composition):
    state: HudState

    def components(self):
        return [
            Text(f"HUM    {self.state.humidity.current:.1f}% / {self.state.humidity.target:.1f}%", 0, 0, True),
            Text(f"CO2    {self.state.co2.current:.0f} PPM / {self.state.co2.target:.0f} PPM", 0, 6, True),
            Text(f"TEMP {self.state.temp:.1f}°F", 0, 12, True),
            Toggle(0, 18, self.state.co2.controller_running, "C"),
            Bar('down', self.state.co2.target, self.state.co2.current, 1200, 9, 20, 118),
            Toggle(0, 28, self.state.humidity.controller_running, "H"),
            Bar('up', self.state.humidity.target, self.state.humidity.current, 40.0, 9, 30, 118),
        ]


test = AddressableTextScreen(128, 64)
test.set(0, 63, True)
test.set(127, 0, True)
test.set(127, 63, True)
hud = Hud(HudState(
    co2=MetricState(
        current=600,
        target=800,
        controller_running=False,
    ),
    humidity=MetricState(
        current=84.65,
        target=95.00,
        controller_running=True,
    ),
    temp=71.2,
))
hud.render(test)
test.print()
