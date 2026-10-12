"""Standalone tests for the cheque life cycle (no Odoo needed)."""
import importlib.util
import unittest
from datetime import date
from pathlib import Path

_path = Path(__file__).resolve().parents[1] / "re_cheque" / "models" / "states.py"
_spec = importlib.util.spec_from_file_location("states", _path)
states = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(states)

TODAY = date(2026, 6, 10)


class TransitionTests(unittest.TestCase):
    def test_happy_path(self):
        self.assertTrue(states.can_transition("in_hand", "deposited"))
        self.assertTrue(states.can_transition("deposited", "cleared"))

    def test_cannot_clear_without_deposit(self):
        self.assertFalse(states.can_transition("in_hand", "cleared"))

    def test_bounced_can_be_presented_again_or_returned(self):
        self.assertTrue(states.can_transition("bounced", "in_hand"))
        self.assertTrue(states.can_transition("bounced", "returned"))
        self.assertFalse(states.can_transition("bounced", "cleared"))

    def test_final_states_are_final(self):
        for final in ("cleared", "returned", "cancelled"):
            for target in states.STATES:
                self.assertFalse(states.can_transition(final, target), (final, target))

    def test_every_state_is_defined(self):
        self.assertEqual(set(states.TRANSITIONS), set(states.STATES))
        for targets in states.TRANSITIONS.values():
            self.assertLessEqual(targets, set(states.STATES))

    def test_unknown_state(self):
        self.assertFalse(states.can_transition("nope", "cleared"))


class BucketTests(unittest.TestCase):
    def b(self, due, state="in_hand"):
        return states.bucket(due, TODAY, state)

    def test_overdue(self):
        self.assertEqual(self.b(date(2026, 6, 9)), "overdue")

    def test_due_today_is_due_soon(self):
        self.assertEqual(self.b(TODAY), "due_soon")

    def test_seven_days_is_due_soon_eight_is_upcoming(self):
        self.assertEqual(self.b(date(2026, 6, 17)), "due_soon")
        self.assertEqual(self.b(date(2026, 6, 18)), "upcoming")

    def test_bounced_is_always_overdue(self):
        self.assertEqual(self.b(date(2027, 1, 1), "bounced"), "overdue")

    def test_closed_states(self):
        for st in ("cleared", "returned", "cancelled"):
            self.assertEqual(self.b(date(2020, 1, 1), st), "closed")

    def test_deposited_past_due_is_overdue(self):
        self.assertEqual(self.b(date(2026, 6, 1), "deposited"), "overdue")


if __name__ == "__main__":
    unittest.main()
