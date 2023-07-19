"""
3x5 font encoded from:
https://www.fontspace.com/teeny-tiny-pixls-font-f30095
Credit to Chequered Ink
"""
from dataclasses import dataclass, field
from screen_types import Composition, Renderable

TEXT_MAPPING = {
    "1": "110010010010111",
    "2": "111001111100111",
    "3": "111001111001111",
    "4": "101101111001001",
    "5": "111100111001111",
    "6": "111100111101111",
    "7": "111101001001001",
    "8": "111101111101111",
    "9": "111101111001001",
    "0": "111101101101111",
    "A": "111101111101101",
    "B": "111101110101111",
    "C": "111100100100111",
    "D": "110101101101110",
    "E": "111100111100111",
    "F": "111100111100100",
    "G": "111100101101111",
    "H": "101101111101101",
    "I": "111010010010111",
    "J": "001001001101111",
    "K": "101101110101101",
    "L": "100100100100111",
    "M": "101111101101101",
    "N": "111101101101101",
    "O": "111101101101111",
    "P": "111101111100100",
    "Q": "111101101110001",
    "R": "111101110101101",
    "S": "111100111001111",
    "T": "111010010010010",
    "U": "101101101101111",
    "V": "101101101101010",
    "W": "101101101111101",
    "X": "101101010101101",
    "Y": "101101111010010",
    "Z": "111001010101111",
    "%": "101001010100101",
    "°": "010101010000000",
    ".": "000000000000010",
    " ": "000000000000000",
    "|": "010010010010010",
    "/": "001001010100100",
}


@dataclass
class Character(Renderable):
    char: str
    x: int
    y: int
    on: bool

    def render(self, screen):
        text = TEXT_MAPPING[self.char]
        for yi, y in enumerate(range(self.y, self.y + 5)):
            for xi, x in enumerate(range(self.x, self.x + 3)):
                index = yi * 3 + xi
                screen.set(x, y, text[index] == ("1" if self.on else "0"))


@dataclass
class Text(Composition):
    text: str
    x: int
    y: int
    characters: list[Character] = field(init=False)
    on: bool

    def __post_init__(self):
        self.characters = [
            Character(char, self.x + i * 4, self.y, self.on)
            for i, char
            in enumerate(self.text)
        ]

    def components(self):
        return self.characters
