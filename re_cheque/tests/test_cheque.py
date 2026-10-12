from datetime import date

from psycopg2 import IntegrityError

from odoo.exceptions import UserError, ValidationError
from odoo.tests.common import TransactionCase
from odoo.tools import mute_logger


class TestReCheque(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        project = cls.env["re.project"].create({"name": "Cheque Project", "code": "CP"})
        unit = cls.env["re.unit"].create(
            {"name": "C-101", "project_id": project.id, "area": 100.0, "price": 1_000_000.0}
        )
        cls.buyer = cls.env["res.partner"].create({"name": "Cheque Buyer"})
        plan = cls.env["re.installment.plan"].create(
            {
                "unit_id": unit.id,
                "partner_id": cls.buyer.id,
                "total_price": 1_000_000.0,
                "down_payment_pct": 10.0,
                "installment_count": 4,
                "months_between": "3",
                "start_date": date(2026, 1, 1),
            }
        )
        plan.action_generate()
        cls.line = plan.line_ids.sorted("sequence")[1]  # first installment

    def _cheque(self, **overrides):
        vals = {
            "name": "000123",
            "bank": "Test Bank",
            "partner_id": self.buyer.id,
            "amount": 5000.0,
            "due_date": date(2026, 7, 1),
        }
        vals.update(overrides)
        return self.env["re.cheque"].create(vals)

    def test_defaults(self):
        cheque = self._cheque()
        self.assertEqual(cheque.state, "in_hand")
        self.assertTrue(cheque.received_date)

    def test_full_lifecycle_marks_installment_paid(self):
        cheque = self._cheque(amount=self.line.amount, line_id=self.line.id)
        cheque.action_deposit()
        self.assertEqual(cheque.state, "deposited")
        self.assertTrue(cheque.deposit_date)
        self.assertFalse(self.line.paid)
        cheque.action_clear()
        self.assertEqual(cheque.state, "cleared")
        self.assertTrue(cheque.clear_date)
        self.assertTrue(self.line.paid)
        self.assertEqual(self.line.paid_date, cheque.clear_date)

    def test_cannot_clear_before_deposit(self):
        cheque = self._cheque()
        with self.assertRaises(UserError):
            cheque.action_clear()

    def test_bounce_keeps_installment_unpaid_and_can_be_presented_again(self):
        cheque = self._cheque(amount=self.line.amount, line_id=self.line.id)
        cheque.action_deposit()
        cheque.action_bounce("Insufficient funds")
        self.assertEqual(cheque.state, "bounced")
        self.assertEqual(cheque.bounce_reason, "Insufficient funds")
        self.assertFalse(self.line.paid)
        cheque.action_represent()
        self.assertEqual(cheque.state, "in_hand")
        self.assertFalse(cheque.bounce_reason)

    def test_cleared_cheque_is_final(self):
        cheque = self._cheque()
        cheque.action_deposit()
        cheque.action_clear()
        for method in (cheque.action_cancel, cheque.action_return, cheque.action_deposit):
            with self.assertRaises(UserError):
                method()

    def test_amount_must_be_positive(self):
        with self.assertRaises(ValidationError):
            self._cheque(amount=0)

    def test_linked_amount_must_match_installment(self):
        with self.assertRaises(ValidationError):
            self._cheque(amount=self.line.amount + 1, line_id=self.line.id)

    def test_duplicate_number_same_bank_rejected(self):
        self._cheque()
        with mute_logger("odoo.sql_db"), self.assertRaises(IntegrityError):
            with self.cr.savepoint():
                self._cheque()

    def test_same_number_other_bank_allowed(self):
        self._cheque()
        self.assertTrue(self._cheque(bank="Other Bank"))

    def test_bucket_overdue_and_closed(self):
        overdue = self._cheque(name="old", due_date=date(2020, 1, 1))
        self.assertEqual(overdue.bucket, "overdue")
        overdue.action_cancel()
        self.assertEqual(overdue.bucket, "closed")

    def test_return_from_in_hand(self):
        cheque = self._cheque()
        cheque.action_return()
        self.assertEqual(cheque.state, "returned")
