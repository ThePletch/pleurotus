from dataclasses import dataclass, field

from controller_types import Controller


@dataclass
class FakeController(Controller):
    should_be_active_override: bool
    device_name: str = field(init=False, default="fake")

    def reader(self):
        return 0.0

    # no-op - state tracking happens automatically
    def toggle(self, state):
        pass

    def should_be_active(self, value):
        return self.should_be_active_override
