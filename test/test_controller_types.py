from dataclasses import dataclass
from unittest import TestCase

from test.testutils import FakeController

from controller_types import MinimumPercentageController


example_minimum_percentage_config = {
    'minimum_run_percentage': 0.5,
}


@dataclass
class FakeMinimumPercentageController(MinimumPercentageController, FakeController):
    pass


class TestMinimumPercentageController(TestCase):
    def test_active_when_parent_is(self):
        fake_always_active = FakeMinimumPercentageController(
            should_be_active_override=True,
            config=example_minimum_percentage_config,
        )

        self.assertTrue(fake_always_active.should_be_active(100.0))

        fake_always_active.time_running = 5.0
        fake_always_active.time_measured = 6.0
        self.assertTrue(fake_always_active.should_be_active(100.0))

    def test_inactive_when_parent_inactive_above_ratio(self):
        fake_always_active = FakeMinimumPercentageController(
            should_be_active_override=False,
            config=example_minimum_percentage_config,
        )

        fake_always_active.time_running = 5.0
        fake_always_active.time_measured = 6.0
        self.assertFalse(fake_always_active.should_be_active(100.0))

    def test_active_when_parent_inactive_below_ratio(self):
        fake_always_active = FakeMinimumPercentageController(
            should_be_active_override=False,
            config=example_minimum_percentage_config,
        )

        fake_always_active.time_running = 2.0
        fake_always_active.time_measured = 6.0
        self.assertTrue(fake_always_active.should_be_active(100.0))
