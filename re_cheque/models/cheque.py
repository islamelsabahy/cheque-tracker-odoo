from odoo import api, fields, models
from odoo.exceptions import UserError, ValidationError

from .states import bucket as bucket_for
from .states import can_transition


class ReCheque(models.Model):
    _name = "re.cheque"
    _description = "Cheque"
    _inherit = ["mail.thread"]
    _order = "due_date, id"

    name = fields.Char("Cheque number", required=True, tracking=True)
    bank = fields.Char(required=True)
    partner_id = fields.Many2one("res.partner", "Drawer", required=True, tracking=True)
    company_id = fields.Many2one("res.company", default=lambda self: self.env.company, required=True)
    currency_id = fields.Many2one("res.currency", default=lambda self: self.env.company.currency_id, required=True)
    amount = fields.Monetary(required=True, tracking=True)
    received_date = fields.Date(default=fields.Date.context_today)
    due_date = fields.Date(required=True, tracking=True)
    line_id = fields.Many2one(
        "re.installment.line", "Installment", domain=[("paid", "=", False)], ondelete="set null"
    )
    state = fields.Selection(
        [
            ("in_hand", "In hand"),
            ("deposited", "Deposited"),
            ("cleared", "Cleared"),
            ("bounced", "Bounced"),
            ("returned", "Returned"),
            ("cancelled", "Cancelled"),
        ],
        default="in_hand",
        required=True,
        tracking=True,
    )
    deposit_date = fields.Date()
    clear_date = fields.Date()
    bounce_reason = fields.Char()
    bucket = fields.Selection(
        [("overdue", "Overdue"), ("due_soon", "Due soon"), ("upcoming", "Upcoming"), ("closed", "Closed")],
        compute="_compute_bucket",
    )

    _sql_constraints = [
        ("bank_number_uniq", "unique(bank, name, company_id)", "This cheque number is already registered for that bank."),
    ]

    @api.depends("due_date", "state")
    def _compute_bucket(self):
        today = fields.Date.context_today(self)
        for rec in self:
            rec.bucket = bucket_for(rec.due_date, today, rec.state) if rec.due_date else "upcoming"

    @api.constrains("amount")
    def _check_amount(self):
        for rec in self:
            if rec.amount <= 0:
                raise ValidationError("The cheque amount must be positive.")

    @api.constrains("line_id", "amount")
    def _check_line_amount(self):
        for rec in self:
            if rec.line_id and abs(rec.line_id.amount - rec.amount) > 0.005:
                raise ValidationError(
                    "The cheque amount must equal the installment amount "
                    f"({rec.line_id.amount:,.2f}). Register one cheque per installment."
                )

    def _move(self, target, **extra):
        for rec in self:
            if not can_transition(rec.state, target):
                raise UserError(f"A {rec.state.replace('_', ' ')} cheque cannot become {target.replace('_', ' ')}.")
        self.write(dict(extra, state=target))

    def action_deposit(self):
        self._move("deposited", deposit_date=fields.Date.context_today(self))

    def action_clear(self):
        today = fields.Date.context_today(self)
        self._move("cleared", clear_date=today)
        for rec in self.filtered("line_id"):
            rec.line_id.write({"paid": True, "paid_date": today})

    def action_bounce(self, reason=None):
        self._move("bounced", bounce_reason=reason or False)

    def action_represent(self):
        self._move("in_hand", deposit_date=False, bounce_reason=False)

    def action_return(self):
        self._move("returned")

    def action_cancel(self):
        self._move("cancelled")
