"""Cheque life cycle rules. No Odoo imports, so they are unit-tested on their own."""
from datetime import date

STATES = ("in_hand", "deposited", "cleared", "bounced", "returned", "cancelled")

# A bounced cheque can be presented again (back to in_hand) or handed back.
TRANSITIONS = {
    "in_hand": {"deposited", "returned", "cancelled"},
    "deposited": {"cleared", "bounced"},
    "bounced": {"in_hand", "returned"},
    "cleared": set(),
    "returned": set(),
    "cancelled": set(),
}

OPEN_STATES = ("in_hand", "deposited")
DUE_SOON_DAYS = 7


def can_transition(current: str, target: str) -> bool:
    return target in TRANSITIONS.get(current, set())


def bucket(due: date, today: date, state: str, soon_days: int = DUE_SOON_DAYS) -> str:
    """Group a cheque for the portfolio view.

    closed: nothing left to do; overdue: past due and still open (or bounced);
    due_soon: due within ``soon_days`` days; upcoming: later than that.
    """
    if state in ("cleared", "returned", "cancelled"):
        return "closed"
    if state == "bounced":
        return "overdue"
    days = (due - today).days
    if days < 0:
        return "overdue"
    if days <= soon_days:
        return "due_soon"
    return "upcoming"
