# cheque-tracker-odoo

[![CI](https://github.com/islamelsabahy/cheque-tracker-odoo/actions/workflows/ci.yml/badge.svg)](https://github.com/islamelsabahy/cheque-tracker-odoo/actions/workflows/ci.yml)

**EN** — An Odoo 17 add-on for the post-dated cheques that real estate buyers hand over against their installments. Register each cheque, link it to an installment line, and follow it: in hand → deposited → cleared (or bounced / returned). Clearing a linked cheque marks the installment as paid. Includes *overdue* and *due in 7 days* filters and a pivot of the portfolio by due month and status.

**AR** — موديول Odoo 17 لمتابعة الشيكات المؤجلة اللي العميل بيسلّمها مقابل الأقساط. سجّل كل شيك واربطه بالقسط وتابع حالته: في الخزنة ← مُودَع ← تم صرفه (أو مرتد / مُرجَع). لما الشيك المربوط يتصرف القسط بيتعلّم "مدفوع" تلقائي. فيه فلاتر "متأخر" و"يستحق خلال 7 أيام" وجدول pivot للمحفظة حسب شهر الاستحقاق والحالة.

## Life cycle / دورة حياة الشيك

| From | Allowed next |
|---|---|
| In hand | Deposited, Returned, Cancelled |
| Deposited | Cleared, Bounced |
| Bounced | In hand (present again), Returned |
| Cleared / Returned / Cancelled | final |

The rules live in `re_cheque/models/states.py` with no Odoo imports, so they are unit-tested without an Odoo install.

## Rules enforced / القواعد

- Amount must be positive.
- A cheque linked to an installment must equal that installment's amount (one cheque per installment).
- A cheque number is unique per bank and company.
- Only valid transitions are allowed (for example, no clearing before deposit).

## Install / التثبيت

Requires [`odoo-real-estate-addons`](https://github.com/islamelsabahy/odoo-real-estate-addons) (`re_unit` and `re_installment`).

1. Copy `re_unit`, `re_installment` and `re_cheque` into your Odoo addons path.
2. Restart Odoo, enable developer mode, Apps → Update Apps List.
3. Install **Real Estate Cheque Register**. The *Cheques* menu appears under *Real Estate*.

## Tests

| Layer | Runs | Covers |
|---|---|---|
| `tests/` | anywhere, no Odoo | transitions, due-soon / overdue buckets |
| `re_cheque/tests/` | Odoo 17 (CI uses the official image) | lifecycle, installment payment, constraints |

```bash
python -m unittest discover -s tests -v
```

## Status and limits / الحالة

- No accounting integration yet: clearing marks the installment paid but posts no journal entry.
- Access rights give all internal users read/write/create; tighten with groups before production.
- The "due in 7 days" window is fixed in the search view.

## Roadmap

- [ ] Journal entries on deposit / clearing
- [ ] Batch deposit slip (PDF) per bank
- [ ] Reminder activity N days before due date
- [ ] Arabic translation (`i18n/ar.po`)

## License

LGPL-3
