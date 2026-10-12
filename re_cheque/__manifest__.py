{
    "name": "Real Estate Cheque Register",
    "summary": "Post-dated cheques per installment: portfolio, deposit, clearing and bounces",
    "description": """
Real Estate Cheque Register
===========================
Register the post-dated cheques a buyer hands over, optionally link each one to
an installment line, and follow it through in hand, deposited, cleared or
bounced. Clearing a linked cheque marks the installment as paid. Includes
due-soon and overdue filters and a pivot by due month.
""",
    "version": "17.0.1.0.0",
    "category": "Real Estate",
    "author": "Islam El-Sherbiny",
    "license": "LGPL-3",
    "depends": ["re_installment", "mail"],
    "data": [
        "security/ir.model.access.csv",
        "views/cheque_views.xml",
    ],
    "installable": True,
}
